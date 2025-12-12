"""Commonly reused helper functions for simplifying GUI building"""
from tkinter import ttk
from typing import Any
from os import path
from utils import file_info

def separator(parent: Any, r: int, span: int) -> int:
    """Pre and Post increments the row, creates a separator, returns row"""
    r += 1
    ttk.Separator(parent, orient='horizontal').grid(
        sticky="we", row=r, column=0, columnspan=span, pady=10)
    r += 1
    return r

def generate_file_names(files: tuple, post_pend: str) -> tuple:
    """Generate the file paths for output and showing"""
    output_files: list = []
    show_files: list = []
    for filename in files:
        head, tail = path.split(filename)
        name, _ext = path.splitext(tail)

        output_filename = path.join(head, name + post_pend)
        show_temp_file = path.join(file_info["temp_folder_path"], name + post_pend)

        output_files.append(output_filename)
        show_files.append(show_temp_file)
    return output_files, show_files

def set_title_icon(parent: Any, title: str):
    """Set the window title and icon"""
    parent.title(title)
    parent.iconbitmap(r'C:\Dev\Plotter-Post-Processing\images\LewistonFace.ico')
