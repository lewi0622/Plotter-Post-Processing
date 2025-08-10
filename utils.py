import os, glob, sys, shutil, stat
from lxml import etree as ET
import webbrowser
import re
import random
import math
import threading
import subprocess
from tkinter.filedialog import askopenfilenames

initial_dir = os.path.expandvars(r"C:\Users\$USERNAME\Downloads")
temp_folder_path = ""

file_info = {
    "files": (),
    "color_dicts": (),
    "interleaved?": (),
    "combined_color_dicts": {},
    "size_info": ()
}


def get_all_size_info():
    size_info = []
    for file in file_info["files"]:
        size_info.append(get_svg_width_height(file))
    file_info["size_info"] = tuple(size_info)


def get_all_color_dicts():
    color_dicts = []
    interleaved_files = []
    combined_color_dict = {}
    for file in file_info["files"]:
        color_dict, interleaved = build_color_dict(file)    
        color_dicts.append(color_dict)
        interleaved_files.append(interleaved)
        combined_color_dict = combined_color_dict | color_dict
    file_info["color_dicts"] = tuple(color_dicts)
    file_info["combined_color_dicts"] = combined_color_dict
    file_info["interleaved?"] = interleaved_files


def open_url_in_browser(url):
   """Opens the given url in a new browser tab"""
   webbrowser.open_new_tab(url)


def get_svg_width_height(path):
    """get svg width and height in inches"""
    root = None
    for event, elem in ET.iterparse(path, events=('start', 'end')):
        if event == "start":
            try: 
                elem.attrib["width"]
                root = elem
            except KeyError:
                pass
        if root != None:
            break

    try:
        svg_width = root.attrib["width"] #size in pixels, css units are 96 px = 1 inch 
        svg_height = root.attrib["height"] 
    except KeyError:
        try:
            viewbox = root.attrib["viewBox"].split()
            svg_width = viewbox[2]
            svg_height = viewbox[3]
        except KeyError:
            print("No width, height, or viewBox info found")
            return 0,0

    if "in" in svg_width:
        svg_width_inches = float(svg_width.replace("in", ""))
    elif "px" in svg_width:
        svg_width_inches = float(svg_width.replace("px", ""))/96 
    elif "cm" in svg_width:
        svg_width_inches = float(svg_width.replace("cm", ""))/2.54
    else:
        svg_width_inches = float(svg_width)/96 

    if "in" in svg_height:
        svg_height_inches = float(svg_height.replace("in", ""))
    elif "px" in svg_height:
        svg_height_inches = float(svg_height.replace("px", ""))/96 
    elif "cm" in svg_height:
        svg_height_inches = float(svg_height.replace("cm", ""))/2.54
    else:   
        svg_height_inches = float(svg_height)/96

    svg_width_inches = round(svg_width_inches * 1000)/1000
    svg_height_inches = round(svg_height_inches * 1000)/1000

    return svg_width_inches, svg_height_inches


def select_files(files=(), dialog_title="SELECT DESIGN FILE(s)"):
    if len(files) == 0:
        recieved_files = get_files(dialog_title) #prompt user to select files
        if len(recieved_files) > 0:
            input_files = recieved_files
    else:
        input_files = files
    print("Currently Loaded Files: ", input_files)
    file_info["files"] = input_files
    get_all_color_dicts()
    get_all_size_info()
    return input_files


def get_files(title=""):
    global temp_folder_path
    # initial_dir = os.path.expandvars(R"C:\Users\$USERNAME\Downloads\demo")
    list_of_files = glob.glob(initial_dir + r"\*.svg")
    latest_file = max(list_of_files, key=os.path.getctime)

    recieved_files = askopenfilenames(title=title, initialdir=initial_dir, filetypes=(("SVG files","*.svg*"),("all files","*.*")), initialfile=latest_file)
    if recieved_files == "":
        return ()
    else:
        temp_folder_path = os.path.join(os.path.dirname(recieved_files[0]), r"ppp_temp")
        return recieved_files


def get_hex_value(rgb):
    """rgb must be in the form of a tuple of integers, returns a hex string"""
    hex_value = '#%02x%02x%02x' % rgb
    return hex_value


def build_color_dict(input_file):
    color_dict = {}
    current_color = ""
    color_change_count = 0
    #if the file is properly formatted, this will find the colors
    for _, elem in ET.iterparse(input_file, events=('end',)):
        hex_string = None
        if elem.tag.endswith("text"):
            continue
        elif "stroke" in elem.attrib:
            hex_string = parse_stroke_color(elem.attrib["stroke"])
        elif elem.tag.endswith("g"): #handling color transformations within g tags a la DrawingBotV3 style outputs
            if "style" in elem.attrib:
                stroke_string = re.search(r"(stroke:.*?;)", elem.attrib["style"])
                if stroke_string != None:
                    hex_string = parse_stroke_color(stroke_string.group())
        elif "fill" in elem.attrib: # if there is a fill with no stroke, vpype will assign it a stroke color
            hex_string = parse_stroke_color(elem.attrib["fill"])
        
        if hex_string != None:
            color_dict[hex_string] = 0
            if hex_string != current_color:
                color_change_count += 1
        elem.clear()
    #otherwise we look in all the rest
    if color_dict == {}:
        with open(input_file, 'r') as file:
            content = file.read()
            strokes = re.findall(r'(?:stroke=")(.*?)(?:")', content)
            for stroke in strokes:
                hex_string = parse_stroke_color(stroke)
                if hex_string != None:
                    color_dict[hex_string] = 0
    interleaved = color_change_count > len(color_dict)
    return (color_dict, interleaved)


def parse_stroke_color(s):
    # converts a string of a color representation into a hex stringg
    c = None
    #check for rgb and convert to hex
    if "rgb" in s:
        rgb = re.findall(r'(?:rgb\()(.*?)(?:\))', s)[0].split(",")
        c = get_hex_value((int(rgb[0]), int(rgb[1]), int(rgb[2])))
    elif "#" in s:
        c = s
    elif "black" in s:
        c = "#000000"
    elif "none" in s:
        pass
    else:
        print("Can't parse: ", s)

    return c


def max_colors_per_file():
    """Finds the max of distinct colors in any given file"""
    max_num_color = 0
    for color_dict in file_info["color_dicts"]:
        if len(color_dict) > max_num_color:
            max_num_color = len(color_dict)
    return max_num_color


def generate_random_color():
    #generate first color
    rgb = (
    math.floor(random.random()*256), 
    math.floor(random.random()*256), 
    math.floor(random.random()*256)
    )
    rgb_hex = get_hex_value(rgb)

    # keep generating colors if matching
    while(rgb_hex in file_info["combined_color_dicts"]):
        rgb = (
            math.floor(random.random()*256), 
            math.floor(random.random()*256), 
            math.floor(random.random()*256)
        )
        rgb_hex = get_hex_value(rgb)

    file_info["combined_color_dicts"][rgb_hex] = 0

    return rgb_hex


def get_directory_name(file_name):
    if sys.argv[0] == "file_name":
        return os.getcwd()
    else:
        return os.path.dirname(sys.argv[0])
    

def delete_temp_file(filename):
    try:
        os.remove(filename)
    except FileNotFoundError:
        return


def rename_replace(old_filename, new_filename):
    try:
        os.rename(old_filename, new_filename)
    except FileExistsError:
        os.remove(new_filename)
        os.rename(old_filename, new_filename)

def check_make_temp_folder():
    if not os.path.isdir(temp_folder_path):
        print("Making temp folder")
        os.mkdir(temp_folder_path)

def check_delete_temp_folder():
    if os.path.isdir(temp_folder_path):
        # set permissions to write
        os.chmod(temp_folder_path, stat.S_IWUSR)        # #https://stackoverflow.com/questions/2656322/shutil-rmtree-fails-on-windows-with-access-is-denied
        shutil.rmtree(temp_folder_path)

def on_closing(win):
    check_delete_temp_folder()
    win.quit()      

def find_closest_dimensions(width, height):
    if(width > height):
        width, height = height, width

    dimensinons = {
        "Letter":[8.5, 11],
        "A4":[8.3, 11.7], 
        "11x17 in":[11, 17], 
        "A3": [11.7, 16.5], 
        "17x23 in": [17, 23], 
        "A2": [16.5, 23.4]
        }
    id = 0
    closest_w = 8.5
    for index, size in enumerate(dimensinons):
        w = dimensinons[size][0]

        if abs(width - closest_w) > abs(width - w):
            closest_w = w
            id = index

    return id

def run_subprocess(command):
    subprocess.run(command, capture_output=True, shell=True)

def thread_vpypelines(commands, app):
    """Set up multithreading for each file in the batch"""
    print(
        "", 
        "Running " + app + f" on {len(commands)} file(s). First pipeline:", 
        commands[0], 
        sep="\n"
    )
    threads = []
    for command in commands:
        thread = threading.Thread(target=run_subprocess, args=(command,))
        thread.start()
        threads.append(thread)
    for thread in threads:
        thread.join()