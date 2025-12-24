"""Commonly reused helper functions for simplifying GUI building"""
from tkinter import ttk, Canvas
from typing import Any
from os import path
from utils import file_info

def separator(parent: Any, r: int, span: int) -> int:
    """Pre and Post increments the row, creates a separator, returns row"""
    r += 1
    ttk.Separator(parent, orient='horizontal').grid(
        sticky="ew", row=r, column=0, columnspan=span, pady=10)
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
    parent.attributes('-topmost', True) # make window topmost window https://stackoverflow.com/questions/8691655/how-to-put-a-tkinter-window-on-top-of-the-others
    parent.update()

def on_focus_in(entry, placeholder): 
    """Will delete placeholder text in an entry when user interacts with it"""
    if entry.get() == placeholder:
        entry.delete(0, 'end')

def on_focus_out(entry, placeholder):
    """Will replace a blank entry with placeholder text when a user stops interacting with it"""
    if entry.get() == "":
        entry.insert(0, placeholder)

def create_scrollbar(root: Any):
    """Creates and returns a scrollframe that all other widgets should attach themselves to"""
    # Configure root grid
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)

    # Container frame
    container = ttk.Frame(root)
    container.grid(row=0, column=0, sticky="nsew")

    container.grid_rowconfigure(0, weight=1)
    container.grid_columnconfigure(0, weight=1)

    # Canvas
    canvas = Canvas(container)
    canvas.grid(row=0, column=0, sticky="nsew")

    # Scrollbar
    scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
    scrollbar.grid(row=0, column=1, sticky="ns")

    canvas.configure(yscrollcommand=scrollbar.set)

    # Scrollable frame
    scrollable_frame = ttk.Frame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

    def _on_mousewheel(event):
        if event.delta:  # Windows / macOS
            canvas.yview_scroll(-1 * int(event.delta / 120), "units")
        else:  # Linux
            if event.num == 4:
                canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                canvas.yview_scroll(1, "units")

    canvas.bind_all("<MouseWheel>", _on_mousewheel)      # Windows / macOS
    canvas.bind_all("<Button-4>", _on_mousewheel)        # Linux scroll up
    canvas.bind_all("<Button-5>", _on_mousewheel)        # Linux scroll down

    return scrollable_frame