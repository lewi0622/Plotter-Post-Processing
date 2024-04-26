import os, glob, sys
import xml.etree.ElementTree as ET
import webbrowser
import re
import random
import math
from tkinter.filedialog import askopenfilenames

def open_url_in_browser(url):
   """Opens the given url in a new browser tab"""
   webbrowser.open_new_tab(url)


def get_svg_width_height(path):
    """get svg width and height in inches"""
    tree = ET.parse(path)
    root = tree.getroot()
    svg_width = root.attrib["width"] #size in pixels, css units are 96 px = 1 inch 
    svg_height = root.attrib["height"] 

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


def get_files():
    initial_dir = os.path.expandvars(R"C:\Users\$USERNAME\Downloads")
    list_of_files = glob.glob(initial_dir + r"\*.svg")
    latest_file = max(list_of_files, key=os.path.getctime)

    recieved_files = askopenfilenames(initialdir=initial_dir, filetypes=(("SVG files","*.svg*"),("all files","*.*")), initialfile=latest_file)
    if recieved_files == "":
        return ()
    else:
        return recieved_files

def get_hex_value(rgb):
    """rgb must be in the form of a tubple of integers"""
    hex_value = '#%02x%02x%02x' % rgb
    return hex_value


def build_color_dict(input_file):
    color_dict = {}
    #if the file is properly formatted, this will find the colors
    tree = ET.parse(input_file)
    root = tree.getroot()
    for child in root:
        if "stroke" in child.attrib:
            color_dict[child.attrib["stroke"]] = 0
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
                elif "none" in stroke:
                    pass
                else:
                    print("Can't parse: ", stroke)
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


def generate_random_color(input_file):
    color_dict = build_color_dict(input_file)
    rgb_hex = "#000000"
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