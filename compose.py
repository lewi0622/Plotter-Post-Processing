import subprocess
import os
from typing import Any
from tkinter import ttk, END, CENTER, Tk, IntVar
from utils import rename_replace, on_closing, check_make_temp_folder, file_info, select_files
from utils import open_url_in_browser, generate_random_color, max_colors_per_file
import settings
from gui_helpers import separator

return_val: tuple
current_row: int
window: Any

def main(input_files=()):
    """"Run Compose utility"""
    def run_vpypeline():
        global return_val

        if last_shown_command == build_vpypeline(True):
            rename_replace(show_temp_file, output_file_list[0])
            print("Same command as shown file, not re-running Vpype pipeline")
        else:
            command = build_vpypeline(False)
            print("Running: \n", command)
            subprocess.run(command, capture_output=True, shell=True, check=False)

        return_val = output_file_list
        print("Closing Compose")
        on_closing(window)

    def show_vpypeline():
        """Runs given commands on first file, but only shows the output."""
        global last_shown_command
        check_make_temp_folder()
        last_shown_command = build_vpypeline(True)
        print("Showing: \n", last_shown_command)
        subprocess.run(last_shown_command, check=False)

    def build_vpypeline(show):
        global show_temp_file
        global output_filename
        global output_file_list

        # build output files list
        input_file_list = list(input_files)
        output_file_list = []

        filename = input_file_list[0]
        head, tail = os.path.split(filename)
        name, _ext = os.path.splitext(tail)
        show_temp_file = os.path.join(file_info["temp_folder_path"], name + "_C.svg")
        output_filename = head + "/" + name + "_C.svg"
        output_file_list.append(output_filename)

        # determine if grid is necessary
        cols = grid_col_entry.get()
        rows = grid_row_entry.get()
        width = grid_col_width_entry.get()
        height = grid_row_height_entry.get()

        cols = int(cols)
        rows = int(rows)
        col_size = float(width)
        row_size = float(height)

        slots = cols * rows
        grid = slots > 1

        # sort list in reverse, but load new files in lower number layers
        sorted_info_list = sorted(
            compose_info_list, key=lambda d: d['order'].get(), reverse=not grid)

        args = r"vpype "

        if grid:
            args += f' eval "files_in={input_file_list}" '
            args += r' eval "%grid_layer_count=1%" '
            args += f" grid -o {col_size}in {row_size}in {cols} {rows} "
            args += r' read -a stroke --no-crop %files_in[_i%%len(files_in)]% '
            args += r' forlayer '
            # moves each layer onto it's own unique layer so there's no merging
            args += r' lmove %_lid% %grid_layer_count% '
            # inc the global layer counter
            args += r' eval "%grid_layer_count=grid_layer_count+1%" end end '

        else:  # Load files on top of one another
            for index, info in enumerate(sorted_info_list):
                if index > 0:
                    incoming_layer_number = 1
                    if info["attribute"].get():
                        file_info_index = file_info["files"].index(
                            info["file"])
                        incoming_layer_number = len(
                            file_info["color_dicts"][file_info_index])
                    # shift layers up the number of incoming layers
                    args += f' forlayer lmove "%_lid%" "%_lid+{incoming_layer_number}%" end '
                if info["attribute"].get():
                    args += f' read -a stroke --no-crop "{info["file"]}" '
                else:
                    # args += r' forlayer eval "%last_layer=_lid%" end '
                    args += f' read --no-crop --layer 1 "{info["file"]}" '
                    if info["overwrite_color"].get():
                        args += f' color -l 1 {info["color_info"].get()}'

        # layout as letter centers graphics within given page size
        if layout.get():
            args += r" layout "
            if layout_landscape.get():
                args += r" -l "
            args += f" {layout_width_entry.get()}x{layout_height_entry.get()}in "

        if show:
            args += f' write "{show_temp_file}" '
            if condense.get(): # reread rewrite file
                args += f' ldelete all read -a stroke --no-crop "{show_temp_file}" write "{show_temp_file}" '
            args += ' show '
        else:
            args += f' write "{output_filename}" '
            if condense.get(): # reread rewrite file
                args += f' ldelete all read -a stroke --no-crop "{output_filename}" write "{output_filename}" '

        return args

    def layout_selection_changed(event):
        """Event from changing the layout dropdown box, sets the width and height accordingly"""
        selection = layout_combobox.get()
        layout_width_entry.delete(0, END)
        layout_height_entry.delete(0, END)
        if selection == "Letter":
            layout_width_entry.insert(0, "8.5")
            layout_height_entry.insert(0, "11")
            layout.set(1)
        elif selection == "A4":
            layout_width_entry.insert(0, "8.3")
            layout_height_entry.insert(0, "11.7")
        elif selection == "A3":
            layout_width_entry.insert(0, "11.7")
            layout_height_entry.insert(0, "16.5")
        elif selection == "A2":
            layout_width_entry.insert(0, "16.5")
            layout_height_entry.insert(0, "23.4")
            layout.set(0)

    global return_val, last_shown_command, compose_color_list, compose_info_list
    return_val = ()
    last_shown_command = ""

    svg_width_inches = file_info["size_info"][0][0]  # first file first item
    svg_height_inches = file_info["size_info"][0][1]  # first file second item

    compose_color_list = []
    # generate color list for each potential -k
    for file in input_files:
        compose_color_list.append(generate_random_color())

    max_col = 4

    # tk widgets and window
    current_row = 0  # helper row var, inc-ed every time used;

    global window
    window = Tk()

    ttk.Label(window, text="Compose").grid(
        pady=(10, 0), row=current_row, column=0, columnspan=max_col)
    current_row += 1

    ttk.Label(window, justify=CENTER, text=f"{len(input_files)} Design file(s) selected,\nDesign file Width(in): {svg_width_inches}, Height(in): {svg_height_inches}").grid(
        row=current_row, column=0, columnspan=max_col)
    current_row += 1

    ttk.Label(window, justify=CENTER, text="If Grid Cols and Rows equal 1,\ndesigns are simply loaded on top of one another").grid(
        row=current_row, column=0, columnspan=max_col)
    
    current_row = separator(window, current_row, max_col)

    # grid options
    grid_label = ttk.Label(window, justify=CENTER, text="Merge Multiple SVGs into Grid",
                           foreground=settings.THEME_SETTINGS["link_color"], cursor="hand2")
    grid_label.bind("<Button-1>", lambda e: open_url_in_browser(
        "https://vpype.readthedocs.io/en/latest/cookbook.html#faq-merge-to-grid"))
    grid_label.grid(row=current_row, column=0, columnspan=max_col)
    current_row += 1

    ttk.Label(window, justify=CENTER, text="Grid Col Width(in):").grid(
        row=current_row, column=0)
    grid_col_width_entry = ttk.Entry(window, width=7)
    grid_col_width_entry.grid(sticky="w", row=current_row, column=1)

    ttk.Label(window, justify=CENTER, text="Grid Row Height(in):").grid(
        row=current_row, column=2)
    grid_row_height_entry = ttk.Entry(window, width=7)
    grid_row_height_entry.grid(sticky="w", row=current_row, column=3)
    current_row += 1

    ttk.Label(window, justify=CENTER, text="Grid Columns:").grid(
        row=current_row, column=0)
    grid_col_entry = ttk.Entry(window, width=7)
    grid_col_entry.grid(sticky="w", row=current_row, column=1)

    ttk.Label(window, justify=CENTER, text="Grid Rows:").grid(
        row=current_row, column=2)
    grid_row_entry = ttk.Entry(window, width=7)
    grid_row_entry.grid(sticky="w", row=current_row, column=3)

    # insert after creation of the size entries so
    grid_col_width_entry.insert(0, f"{svg_width_inches}")
    grid_row_height_entry.insert(0, f"{svg_height_inches}")
    grid_col_entry.insert(0, "1")
    grid_row_entry.insert(0, "1")

    current_row = separator(window, current_row, max_col)

    compose_info_list = []

    for index, file in enumerate(input_files):
        compose_info = {"file": file}

        name = os.path.basename(os.path.normpath(file))
        ttk.Label(window, text=f"File: {name}").grid(
            row=current_row, column=0, columnspan=2)

        ttk.Label(window, text=f"Order: ").grid(row=current_row, column=2)
        compose_order = ttk.Combobox(
            window,
            width=4,
            state="readonly",
            values=[*range(len(input_files))]
        )
        compose_order.current(index)
        compose_order.grid(sticky="w", row=current_row, column=3)
        compose_info["order"] = compose_order
        current_row += 1

        ttk.Label(window, text=f"Colors in file: {len(file_info['color_dicts'][index])}").grid(
            row=current_row, column=0)

        attribute = IntVar(window, value=0)
        if max_colors_per_file() == 1:
            attribute = IntVar(window, value=1)
        compose_info["attribute"] = attribute
        ttk.Radiobutton(window, text="single layer", variable=attribute, value=0).grid(
            row=current_row, column=1)
        ttk.Radiobutton(window, text="stroke layer(s)", variable=attribute, value=1).grid(
            row=current_row, column=2)
        current_row += 1

        overwrite_color = IntVar(window, value=0)
        compose_info["overwrite_color"] = overwrite_color
        ttk.Checkbutton(window, text="If single layer, overwrite color?", variable=overwrite_color).grid(
            sticky="e", row=current_row, column=0, columnspan=2)
        compose_color_entry = ttk.Entry(window, width=7)
        compose_info["color_info"] = compose_color_entry
        compose_color_entry.insert(0, f"{compose_color_list[index]}")
        compose_color_entry.grid(sticky="w", row=current_row, column=2)

        current_row = separator(window, current_row, max_col)

        compose_info_list.append(compose_info)

    condense  = IntVar(window, value=1)
    ttk.Checkbutton(window, text="Condense same color layers into single layer", variable=condense).grid(
        sticky="w", row=current_row, column=0)
    
    current_row += 1

    layout_label = ttk.Label(window, justify=CENTER, text="Layout centers scaled\ndesign in page size)",
                             foreground=settings.THEME_SETTINGS["link_color"], cursor="hand2")
    layout_label.bind("<Button-1>", lambda e: open_url_in_browser(
        "https://vpype.readthedocs.io/en/latest/reference.html#layout"))
    layout_label.grid(row=current_row, column=0)
    layout = IntVar(window, value=1)
    ttk.Checkbutton(window, text="Layout?", variable=layout).grid(
        sticky="w", row=current_row, column=1)

    ttk.Label(window, justify=CENTER, text="Page Layout Width(in):").grid(
        row=current_row, column=2)
    layout_width_entry = ttk.Entry(window, width=7)
    layout_width_entry.insert(0, f"8.5")
    layout_width_entry.grid(sticky="w", row=current_row, column=3)
    current_row += 1

    ttk.Label(window, justify=CENTER, text="Page Size").grid(
        row=current_row, column=0)
    layout_combobox = ttk.Combobox(
        window,
        width=7,
        state="readonly",
        values=["Letter", "A4", "A3", "A2"]
    )
    layout_combobox.current(0)
    layout_combobox.grid(sticky="w", row=current_row, column=1)
    layout_combobox.bind("<<ComboboxSelected>>", layout_selection_changed)

    ttk.Label(window, justify=CENTER, text="Page Layout Height(in):").grid(
        row=current_row, column=2)
    layout_height_entry = ttk.Entry(window, width=7)
    layout_height_entry.insert(0, f"11")
    layout_height_entry.grid(sticky="w", row=current_row, column=3)
    current_row += 1

    layout_landscape_label = ttk.Label(
        window, justify=CENTER, text="By default, the larger layout size is the height,\nLandscape flips the orientation")
    layout_landscape_label.grid(row=current_row, column=0, columnspan=2)
    layout_landscape = IntVar(window, value=1)
    ttk.Checkbutton(window, text="Landscape", variable=layout_landscape).grid(
        sticky="w", row=current_row, column=2)

    current_row = separator(window, current_row, max_col)

    ttk.Button(window, text="Show Output", command=show_vpypeline).grid(
        pady=(0, 10), row=current_row, column=0)

    ttk.Button(window, text="Confirm", command=run_vpypeline).grid(
        pady=(0, 10), row=current_row, column=1)

    window.protocol("WM_DELETE_WINDOW", lambda arg=window: on_closing(arg))

    settings.set_theme(window)
    window.mainloop()

    return tuple(return_val)


if __name__ == "__main__":
    settings.init()
    selected_files = select_files()
    if len(selected_files) == 0:
        print("No Design Files Selected")
    else:
        main(input_files=selected_files)
