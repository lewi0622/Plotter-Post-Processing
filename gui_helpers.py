"""Commonly reused helper functions for simplifying GUI building"""

from os import path
from posixpath import join
from tkinter import CENTER, Canvas, ttk
from typing import Any

from settings import THEME_SETTINGS
from utils import file_info, open_url_in_browser


def separator(parent: Any, r: int, span: int) -> int:
    """Pre and Post increments the row, creates a separator, returns row"""
    r += 1
    ttk.Separator(parent, orient="horizontal").grid(
        sticky="ew", row=r, column=0, columnspan=span, pady=10
    )
    r += 1
    return r


def generate_file_names(files: tuple, post_pend: str) -> tuple:
    """Generate the file paths for output and showing"""
    output_files: list = []
    show_files: list = []
    for filename in files:
        head, tail = path.split(filename)
        name, _ext = path.splitext(tail)

        output_filename = join(head, name + post_pend)
        show_temp_file = join(file_info["temp_folder_path"], name + post_pend)

        output_files.append(output_filename)
        show_files.append(show_temp_file)
    return output_files, show_files


def make_topmost_temp(window: Any):
    """Unminimizes, pops the given window to the top of all others, and makes it the focused window"""
    if window.state() == "iconic":
        window.wm_state("normal")  # un-minimize if it is minimized

    window.attributes(
        "-topmost", True
    )  # make window topmost window https://stackoverflow.com/questions/8691655/how-to-put-a-tkinter-window-on-top-of-the-others
    window.update()
    window.attributes(
        "-topmost", False
    )  # stop making topmost window (but it's still on top)
    window.update()
    window.focus_force()  # bring focus to the window


def set_title_icon(parent: Any, title: str):
    """Set the window title and icon"""
    parent.title(title)
    icon_path = join(path.dirname(__file__), "images/LewistonFace.ico")
    try:
        parent.iconbitmap(icon_path)
    except:
        pass
    make_topmost_temp(parent)


def on_focus_in(entry: Any, placeholder: str):
    """Will delete placeholder text in an entry when user interacts with it"""
    if entry.get() == placeholder:
        entry.delete(0, "end")


def on_focus_out(entry: Any, placeholder: str):
    """Will replace a blank entry with placeholder text when a user stops interacting with it"""
    if entry.get() == "":
        entry.insert(0, placeholder)


def create_scrollbar(root: Any, row=0, span=1):
    """Creates and returns a scrollframe that all other widgets should attach themselves to"""
    # Configure root grid
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)

    # Container frame
    container = ttk.Frame(root)
    container.grid(row=row, column=0, columnspan=span, sticky="nsew")

    container.grid_rowconfigure(0, weight=1)
    container.grid_columnconfigure(0, weight=1)

    canvas = Canvas(container)
    canvas.grid(row=row, column=0, sticky="nsew")

    # Scrollbar
    scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
    scrollbar.grid(row=row, column=1, sticky="ns")

    canvas.configure(yscrollcommand=scrollbar.set)

    # Scrollable frame
    scrollable_frame = ttk.Frame(canvas)

    scrollable_frame.bind(
        "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
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

    scrollable_frame.bind_all("<MouseWheel>", _on_mousewheel)  # Windows / macOS
    scrollable_frame.bind_all("<Button-4>", _on_mousewheel)  # Linux scroll up
    scrollable_frame.bind_all("<Button-5>", _on_mousewheel)  # Linux scroll down

    return scrollable_frame


def disable_combobox_scroll(root: Any):
    """Changes the Combobox class for the window to not allow scrolling to change its' value"""

    def _empty(_event):
        return "break"  # stops the event from going further

    root.bind_class("TCombobox", "<MouseWheel>", _empty)  # Windows / macOS
    root.bind_class("TCombobox", "<Button-4>", _empty)  # Linux scroll up
    root.bind_class("TCombobox", "<Button-5>", _empty)  # Linux scroll down


def create_toast(
    root: Any,
    duration_milliseconds: int,
    message: str,
):
    """Generates a toast message that destroys itself after duration"""
    toast = ttk.Button(root, text=message)
    toast.place(relx=0.5, rely=1, anchor="s")
    root.after(duration_milliseconds, toast.destroy)


def create_url_label(parent, text: str, url: str) -> ttk.Label:
    """Creates a styled label with URL binding on click"""
    label = ttk.Label(
        parent,
        text=text,
        justify=CENTER,
        foreground=THEME_SETTINGS["link_color"],
        cursor="hand2",
    )
    label.bind("<Button-1>", lambda e: open_url_in_browser(url))
    return label
