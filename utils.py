import os, glob, sys, shutil
import xml.etree.ElementTree as ET
import webbrowser
import re
import random
import math
from tkinter.filedialog import askopenfilenames
import time

initial_dir = os.path.expandvars(r"C:\Users\$USERNAME\Downloads")
temp_folder_path = ""

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
        svg_width_inches = svg_width.replace("in", "")
    elif "px" in svg_width:
        svg_width_inches = float(svg_width.replace("px", ""))/96 
    elif "cm" in svg_width:
        svg_width_inches = float(svg_width.replace("cm", ""))/2.54
    else:
        svg_width_inches = float(svg_width)/96 

    if "in" in svg_height:
        svg_height_inches = svg_height.replace("in", "")
    elif "px" in svg_height:
        svg_height_inches = float(svg_height.replace("px", ""))/96 
    elif "cm" in svg_height:
        svg_height_inches = float(svg_height.replace("cm", ""))/2.54
    else:   
        svg_height_inches = float(svg_height)/96

    svg_width_inches = round(svg_width_inches * 1000)/1000
    svg_height_inches = round(svg_height_inches * 1000)/1000

    return svg_width_inches, svg_height_inches


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
    """rgb must be in the form of a tuple of integers"""
    hex_value = '#%02x%02x%02x' % rgb
    return hex_value


def build_color_dict(input_file):
    color_dict = {}
    #if the file is properly formatted, this will find the colors
    tree = ET.parse(input_file)
    root = tree.getroot()
    for child in root:
        if child.tag.endswith("text"):
            continue
        if "stroke" in child.attrib:
            color_dict[child.attrib["stroke"]] = 0
        elif "fill" in child.attrib: # if there is a fill with no stroke, vpype will assign it a stroke color
            color_dict[child.attrib["fill"]] = 0
    #otherwise we look in all the test
    if color_dict == {}:
        with open(input_file, 'r') as file:
            content = file.read()
            strokes = re.findall(r'(?:stroke=")(.*?)(?:")', content)
            for stroke in strokes:
                #check for rgb and convert to hex
                if "rgb" in stroke:
                    rgb = re.findall(r'(?:rgb\()(.*?)(?:\))', stroke)[0].split(",")
                    hex_value = get_hex_value((int(rgb[0]), int(rgb[1]), int(rgb[2])))
                elif "#" in stroke:
                    hex_value = stroke
                elif "black" in stroke:
                    hex_value = "#000000"
                elif "none" in stroke:
                    continue
                else:
                    print("Can't parse: ", stroke)
                    continue
                color_dict[hex_value] = 0
    return color_dict


def max_colors_per_file(input_files):
    """Finds the max of distinct colors in any given file"""
    max_num_color = 0
    for input_file in input_files:
        color_dict = build_color_dict(input_file)
        if len(color_dict) > max_num_color:
            max_num_color = len(color_dict)
    return max_num_color


def generate_random_color(input_file, do_not_use=[]):
    color_dict = build_color_dict(input_file)
    for color in do_not_use:
        color_dict[str(color)] = 0

    #generate first color
    rgb = (
    math.floor(random.random()*256), 
    math.floor(random.random()*256), 
    math.floor(random.random()*256)
    )
    rgb_hex = get_hex_value(rgb)

    # keep generating colors if matching
    while(rgb_hex in color_dict):
        rgb = (
            math.floor(random.random()*256), 
            math.floor(random.random()*256), 
            math.floor(random.random()*256)
        )
        rgb_hex = get_hex_value(rgb)

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
