"""Utils provides helpful functions for any Plotter Post Processing apps as well as the main 
function. Any common functions that multiple apps share should be placed here"""
import glob
import math
import os
import random
import re
import shutil
import stat
import subprocess
import sys
import threading
import webbrowser
from tkinter.filedialog import askopenfilenames

from lxml import etree

initial_dir = os.path.expandvars(r"C:\Users\$USERNAME\Downloads")

file_info = {
    "files": (),
    "color_dicts": (),
    "interleaved?": (),
    "combined_color_dicts": {},
    "size_info": (),
    "shown_files": [],
    "temp_folder_path": ""
}


def get_all_size_info():
    """Builds sizing info for each svg file"""
    size_info = []
    for file in file_info["files"]:
        size_info.append(get_svg_width_height(file))
    file_info["size_info"] = tuple(size_info)


def get_all_color_dicts():
    """Builds color info for each svg file"""
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
    for event, elem in etree.iterparse(path, events=('start', 'end')):
        if event == "start":
            if "width" in elem.attrib:
                root = elem
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
    """Calls get_files and file diagnositcs returns a list of files"""
    if len(files) == 0:
        files = get_files(dialog_title) #prompt user to select files
    print("Currently Loaded Files: ", files)
    file_info["temp_folder_path"] = os.path.join(
        os.path.dirname(files[0]),
        r"ppp_temp"
    )
    file_info["files"] = files
    file_info["shown_files"] = [None]*len(files)
    get_all_color_dicts()
    get_all_size_info()
    return files


def get_files(title=""):
    """Opens dialog box to select files and returns a tuple of the selected files"""
    list_of_files = glob.glob(initial_dir + r"\*.svg")
    latest_file = max(list_of_files, key=os.path.getctime)

    recieved_files = askopenfilenames(
        title=title,
        initialdir=initial_dir,
        filetypes=(("SVG files","*.svg*"),("all files","*.*")),
        initialfile=latest_file
        )
    # if nothing selected, askopenfilenames returns a blank string
    if recieved_files == "":
        return ()
    else:
        return recieved_files


def get_hex_value(rgb):
    """rgb must be in the form of a tuple of integers, returns a hex string"""
    hex_value = f'#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}'
    return hex_value


def build_color_dict(input_file):
    """Gets all colors within a file and returns them in a dict"""
    color_dict = {}
    current_color = ""
    color_change_count = 0
    #if the file is properly formatted, this will find the colors
    for _, elem in etree.iterparse(input_file, events=('end',)):
        hex_string = None
        if elem.tag.endswith("text"):
            continue
        elif "stroke" in elem.attrib:
            hex_string = parse_stroke_color(elem.attrib["stroke"])
        #handling color transformations within g tags a la DrawingBotV3 style outputs
        elif elem.tag.endswith("g"):
            if "style" in elem.attrib:
                stroke_string = re.search(r"(stroke:.*?;)", elem.attrib["style"])
                if stroke_string is not None:
                    hex_string = parse_stroke_color(stroke_string.group())
        # if there is a fill with no stroke, vpype will assign it a stroke color
        elif "fill" in elem.attrib:
            hex_string = parse_stroke_color(elem.attrib["fill"])

        if hex_string is not None:
            color_dict[hex_string] = 0
            if hex_string != current_color:
                color_change_count += 1
        elem.clear()
    #otherwise we look in all the rest
    if not color_dict:
        with open(input_file, 'r', encoding="utf-8") as file:
            content = file.read()
            strokes = re.findall(r'(?:stroke=")(.*?)(?:")', content)
            for stroke in strokes:
                hex_string = parse_stroke_color(stroke)
                if hex_string is not None:
                    color_dict[hex_string] = 0
    interleaved = color_change_count > len(color_dict)
    return (color_dict, interleaved)


def parse_stroke_color(s):
    """converts a string of a color representation into a hex string"""
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
    """Generates a unique random color, adds it to color dict"""
    #generate first color
    rgb = (
    math.floor(random.random()*256),
    math.floor(random.random()*256),
    math.floor(random.random()*256)
    )
    rgb_hex = get_hex_value(rgb)

    # keep generating colors if matching
    while rgb_hex in file_info["combined_color_dicts"]:
        rgb = (
            math.floor(random.random()*256),
            math.floor(random.random()*256),
            math.floor(random.random()*256)
        )
        rgb_hex = get_hex_value(rgb)

    file_info["combined_color_dicts"][rgb_hex] = 0

    return rgb_hex


def get_directory_name(file_name):
    """Gets the current directory based on file name or the cwd"""
    if sys.argv[0] == file_name:
        return os.getcwd()
    else:
        return os.path.dirname(sys.argv[0])


def delete_temp_file(filename):
    """Attempt to delete a given file"""
    try:
        os.remove(filename)
    except FileNotFoundError:
        return


def rename_replace(old_filename, new_filename):
    """Move a given file, overwrite if necessary"""
    try:
        os.rename(old_filename, new_filename)
    except FileExistsError:
        os.remove(new_filename)
        os.rename(old_filename, new_filename)
    print("Same command as shown file, not re-running Vpype pipeline")
    print(f"Moving {old_filename} to {new_filename}")

def check_make_temp_folder():
    """Creates the temp folder"""
    if not os.path.isdir(file_info["temp_folder_path"]):
        print(f"Making temp folder at {file_info["temp_folder_path"]}")
        os.mkdir(file_info["temp_folder_path"])

def check_delete_temp_folder():
    """Deletes the temp folder"""
    if os.path.isdir(file_info["temp_folder_path"]):
        # set permissions to write
        os.chmod(file_info["temp_folder_path"], stat.S_IWUSR)
        shutil.rmtree(file_info["temp_folder_path"])

def on_closing(win):
    """Cleanup for all Tk Inter windows"""
    check_delete_temp_folder()
    win.quit()

def find_closest_dimensions(width, height):
    """Finds the closest standard paper dimensions for a given WxH"""
    if width > height:
        width, height = height, width

    dimensinons = {
        "Letter":[8.5, 11],
        "A4":[8.3, 11.7], 
        "11x17 in":[11, 17], 
        "A3": [11.7, 16.5], 
        "17x23 in": [17, 23], 
        "A2": [16.5, 23.4]
        }
    closest_id = 0
    closest_w = 8.5
    for index, size in enumerate(dimensinons):
        w = dimensinons[size][0]

        if abs(width - closest_w) > abs(width - w):
            closest_w = w
            closest_id = index

    return closest_id

def run_subprocess(command):
    """Execute the command in a subprocess"""
    subprocess.run(command, capture_output=True, shell=True, check=False)

def thread_vpypelines(commands, show_commands, app, show_info):
    """Set up multithreading for each file in the batch"""
    if len(show_info) > 0:
        commands = [show_commands[show_info["index"]]]
    print(
        "", 
        "Running " + app + f" on {len(commands)} file(s). First pipeline:", 
        commands[0],
        sep="\n"
    )
    threads = []
    for index, command in enumerate(commands):
        moving_file = False
        current_shown_file = file_info["shown_files"][index]
        if current_shown_file is not None:
            if current_shown_file["command"] == show_commands[index]:
                moving_file = True

        if moving_file:
            thread = threading.Thread(
                target=rename_replace,
                args=(
                    current_shown_file["show_path"],
                    current_shown_file["output_path"])
                )
        else:
            thread = threading.Thread(target=run_subprocess, args=(command,))
        thread.start()
        threads.append(thread)
    for thread in threads:
        thread.join()

    #write shown info so that we can avoid needing to re-run any given pipeline
    if len(show_info) > 0:
        file_info["shown_files"][show_info["index"]] = {
            "command": show_commands[show_info["index"]],
            "show_path": show_info["show_path"],
            "output_path": show_info["output_path"]
        }
