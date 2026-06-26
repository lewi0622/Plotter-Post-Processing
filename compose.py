import os
import subprocess
from math import ceil
from posixpath import join
from tkinter import CENTER, IntVar, Tk, ttk
from typing import Any

from gui_helpers import (
    create_page_layout_combobox,
    create_scrollbar,
    create_url_label,
    disable_combobox_scroll,
    make_topmost_temp,
    separator,
    set_title_icon,
)
from links import PPP_URLS, VPYPE_URLS
from settings import COMPOSE_DEFAULTS, init, set_theme
from utils import (
    check_make_temp_folder,
    file_info,
    generate_random_color,
    on_closing,
    rename_replace,
    select_files,
)

return_val: tuple
current_row: int
window: Any


def main(input_files=()):
    """ "Run Compose utility"""

    def run_vpypeline():
        global return_val

        if spare_files.get() == COMPOSE_DEFAULTS[
            "ignore_files"
        ] and last_shown_command == build_vpypeline(True):
            rename_replace(show_temp_file, output_file_list[0])
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
        make_topmost_temp(window)

    def build_vpypeline(show):
        global show_temp_file
        global output_filename
        global output_file_list

        try:
            cols = int(grid_col_entry.get())
            rows = int(grid_row_entry.get())
            col_size = float(grid_col_width_entry.get())
            row_size = float(grid_row_height_entry.get())
        except ValueError:
            print("Invalid grid size or number of rows/columns")
            return ""

        # create list of translation equivalents instead of using the grid block operator
        translation_list = []
        for i in range(cols):
            for j in range(rows):
                translation_dict = {"x": i * col_size, "y": j * row_size}
                translation_list.append(translation_dict)

        translation_list = list(reversed(translation_list))

        slots = cols * rows
        grid = slots > 1

        sorted_info_list = sorted(
            compose_info_list,
            key=lambda entry: entry["order"].get(),
            reverse=True,
        )

        number_of_output_files = 1
        if spare_files.get() == COMPOSE_DEFAULTS["new_file"] and not show:
            number_of_output_files = ceil(len(sorted_info_list) / slots)

        output_file_list = []
        built_info_collection = []

        for output_index in range(number_of_output_files):
            section = []
            start = output_index * slots
            end = start + slots

            for input_index in range(start, end):
                if input_index >= len(sorted_info_list):
                    if empty_tiles.get() == COMPOSE_DEFAULTS["repeat_deisgns"]:
                        section.append(
                            sorted_info_list[input_index % len(sorted_info_list)]
                        )
                    else:
                        break
                else:
                    section.append(sorted_info_list[input_index])

            if not section:
                continue

            built_info_collection.append(section)

            source_file = section[0]["file"]
            source_name = os.path.splitext(os.path.basename(source_file))[0]
            show_temp_file = join(file_info["temp_folder_path"], source_name + "_C.svg")
            output_filename = join(os.path.dirname(source_file), source_name + "_C.svg")
            output_file_list.append(output_filename)

        args = "vpype "

        for output_index, built_info_list in enumerate(built_info_collection):
            for index, info in enumerate(built_info_list):
                incoming_layer_number = 1
                if info["attribute"].get():
                    file_info_index = file_info["files"].index(info["file"])
                    incoming_layer_number = len(
                        file_info["color_dicts"][file_info_index]
                    )

                if index > 0:
                    # shift layers up the number of incoming layers
                    args += f' forlayer lmove "%_lid%" "%_lid+{incoming_layer_number}%" end '

                # read new layers in
                if info["attribute"].get():
                    args += f' read -a stroke --no-crop "{info["file"]}" '
                else:
                    args += f' read --no-crop --layer 1 "{info["file"]}" '
                    if info["overwrite_color"].get():
                        args += f" color -l 1 {info['color_info'].get()}"

                if grid:
                    layer_list = ",".join(
                        str(i) for i in range(1, incoming_layer_number + 1)
                    )
                    translation = translation_list[index]
                    args += f" translate -l {layer_list} {translation['x']}in {translation['y']}in "

            if layout.get():
                args += " layout "
                if layout_landscape.get():
                    args += " -l "
                args += f" {layout_width_entry.get()}x{layout_height_entry.get()}in "

            target_file = show_temp_file if show else output_file_list[output_index]
            args += f' write "{target_file}" '

            if condense.get():
                args += f' ldelete all read -a stroke --no-crop "{target_file}" write "{target_file}" '

            if show:
                args += " show "
            elif output_index + 1 < len(built_info_collection):
                args += " ldelete all "

        return args

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
    disable_combobox_scroll(window)

    set_title_icon(window, "Compose")

    ttk.Label(window, text="Compose").grid(
        pady=(10, 0), row=current_row, column=0, columnspan=max_col
    )
    current_row += 1

    create_url_label(
        window,
        "For help, visit the Plotter Post Processing Compose Tutorial",
        PPP_URLS["compose"],
    ).grid(row=current_row, column=0, columnspan=max_col)

    current_row += 1

    ttk.Label(
        window,
        justify=CENTER,
        text=f"{len(input_files)} Design file(s) selected,\nDesign file Width(in): {svg_width_inches}, Height(in): {svg_height_inches}",
    ).grid(row=current_row, column=0, columnspan=max_col)
    current_row += 1

    ttk.Label(
        window,
        justify=CENTER,
        text="If Grid Cols and Rows equal 1,\ndesigns are simply loaded on top of one another",
    ).grid(row=current_row, column=0, columnspan=max_col)

    current_row = separator(window, current_row, max_col)

    # grid options
    ttk.Label(window, justify=CENTER, text="Merge Multiple SVGs into Grid").grid(
        row=current_row, column=0, columnspan=max_col
    )
    current_row += 1

    ttk.Label(window, justify=CENTER, text="Grid Col Width(in):").grid(
        row=current_row, column=0
    )
    grid_col_width_entry = ttk.Entry(window, width=7)
    grid_col_width_entry.grid(sticky="w", row=current_row, column=1)

    ttk.Label(window, justify=CENTER, text="Grid Row Height(in):").grid(
        row=current_row, column=2
    )
    grid_row_height_entry = ttk.Entry(window, width=7)
    grid_row_height_entry.grid(sticky="w", row=current_row, column=3)
    current_row += 1

    ttk.Label(window, justify=CENTER, text="Grid Columns:").grid(
        row=current_row, column=0
    )
    grid_col_entry = ttk.Entry(window, width=7)
    grid_col_entry.grid(sticky="w", row=current_row, column=1)

    ttk.Label(window, justify=CENTER, text="Grid Rows:").grid(row=current_row, column=2)
    grid_row_entry = ttk.Entry(window, width=7)
    grid_row_entry.grid(sticky="w", row=current_row, column=3)

    # insert after creation of the size entries so
    grid_col_width_entry.insert(0, f"{svg_width_inches}")
    grid_row_height_entry.insert(0, f"{svg_height_inches}")
    grid_col_entry.insert(0, COMPOSE_DEFAULTS["column_number"])
    grid_row_entry.insert(0, COMPOSE_DEFAULTS["row_number"])

    current_row += 1

    # empty tiles
    ttk.Label(window, justify=CENTER, text="Extra Grid Tiles:").grid(
        row=current_row, column=0, columnspan=2, sticky="e"
    )

    empty_tiles = IntVar(window, value=COMPOSE_DEFAULTS["empty_tiles"])
    ttk.Radiobutton(
        window,
        text="Leave Empty",
        variable=empty_tiles,
        value=COMPOSE_DEFAULTS["leave_empty"],
    ).grid(row=current_row, column=2, sticky="w")
    ttk.Radiobutton(
        window,
        text="Repeat Designs",
        variable=empty_tiles,
        value=COMPOSE_DEFAULTS["repeat_deisgns"],
    ).grid(row=current_row, column=3, sticky="w")

    current_row += 1

    # Spare files
    ttk.Label(window, justify=CENTER, text="Spare Design Files:").grid(
        row=current_row, column=0, columnspan=2, sticky="e"
    )
    spare_files = IntVar(window, value=COMPOSE_DEFAULTS["spare_files"])
    ttk.Radiobutton(
        window,
        text="New File(s)",
        variable=spare_files,
        value=COMPOSE_DEFAULTS["new_file"],
    ).grid(row=current_row, column=2, sticky="w")
    ttk.Radiobutton(
        window,
        text="Ignore Files",
        variable=spare_files,
        value=COMPOSE_DEFAULTS["ignore_files"],
    ).grid(row=current_row, column=3, sticky="w")

    current_row = separator(window, current_row, max_col)

    compose_info_list = []

    frame = window
    if len(input_files) > 2:
        frame = create_scrollbar(window, current_row, max_col)

    for index, file in enumerate(input_files):
        if index != 0:
            current_row = separator(frame, current_row, max_col)

        compose_info = {"file": file}

        name = os.path.basename(os.path.normpath(file))
        ttk.Label(frame, text=f"File: {name}").grid(
            row=current_row, column=0, columnspan=2
        )

        ttk.Label(frame, text="Order: ").grid(row=current_row, column=2)
        compose_order = ttk.Combobox(
            frame, width=4, state="readonly", values=[*range(len(input_files))]
        )
        compose_order.current(index)
        compose_order.grid(sticky="w", row=current_row, column=3)
        compose_info["order"] = compose_order
        current_row += 1

        color_count = len(file_info["color_dicts"][index])
        ttk.Label(frame, text=f"Colors in file: {color_count}").grid(
            row=current_row, column=0
        )

        attribute = IntVar(frame, value=COMPOSE_DEFAULTS["single_layer"])
        if color_count > 1:
            attribute.set(COMPOSE_DEFAULTS["stroke_layers"])
        compose_info["attribute"] = attribute
        ttk.Radiobutton(
            frame,
            text="single layer",
            variable=attribute,
            value=COMPOSE_DEFAULTS["single_layer"],
        ).grid(row=current_row, column=1)
        ttk.Radiobutton(
            frame,
            text="stroke layer(s)",
            variable=attribute,
            value=COMPOSE_DEFAULTS["stroke_layers"],
        ).grid(row=current_row, column=2)
        current_row += 1

        overwrite_color = IntVar(frame, value=COMPOSE_DEFAULTS["overwrite_color"])
        compose_info["overwrite_color"] = overwrite_color
        ttk.Checkbutton(
            frame, text="If single layer, overwrite color?", variable=overwrite_color
        ).grid(sticky="e", row=current_row, column=0, columnspan=2)
        compose_color_entry = ttk.Entry(frame, width=7)
        compose_info["color_info"] = compose_color_entry
        compose_color_entry.insert(0, f"{compose_color_list[index]}")
        compose_color_entry.grid(sticky="w", row=current_row, column=2)

        compose_info_list.append(compose_info)

    current_row = separator(window, current_row, max_col)

    condense = IntVar(window, value=COMPOSE_DEFAULTS["condense_color_layers"])
    ttk.Checkbutton(
        window, text="Condense same color layers into single layer", variable=condense
    ).grid(sticky="w", row=current_row, column=0)

    current_row += 1

    create_url_label(
        window, "Layout centers scaled\ndesign in page size)", VPYPE_URLS["layout"]
    ).grid(row=current_row, column=0)

    layout = IntVar(window, value=COMPOSE_DEFAULTS["layout"])
    ttk.Checkbutton(window, text="Layout?", variable=layout).grid(
        sticky="w", row=current_row, column=1
    )

    ttk.Label(window, justify=CENTER, text="Page Layout Width(in):").grid(
        row=current_row, column=2
    )
    layout_width_entry = ttk.Entry(window, width=7)
    layout_width_entry.grid(sticky="w", row=current_row, column=3)
    current_row += 1

    ttk.Label(window, justify=CENTER, text="Page Size").grid(row=current_row, column=0)

    ttk.Label(window, justify=CENTER, text="Page Layout Height(in):").grid(
        row=current_row, column=2
    )
    layout_height_entry = ttk.Entry(window, width=7)
    layout_height_entry.grid(sticky="w", row=current_row, column=3)

    create_page_layout_combobox(
        window,
        svg_width_inches,
        svg_height_inches,
        layout_width_entry,
        layout_height_entry,
    ).grid(sticky="w", row=current_row, column=1)
    current_row += 1

    ttk.Label(
        window,
        justify=CENTER,
        text="By default, the larger layout size is the height,\nLandscape flips the orientation",
    ).grid(row=current_row, column=0, columnspan=2)

    layout_landscape = IntVar(window, value=COMPOSE_DEFAULTS["layout_landscape"])
    ttk.Checkbutton(window, text="Landscape", variable=layout_landscape).grid(
        sticky="w", row=current_row, column=2
    )

    current_row = separator(window, current_row, max_col)

    ttk.Button(window, text="Show Output", command=show_vpypeline).grid(
        pady=(0, 10), row=current_row, column=0
    )

    ttk.Button(window, text="Confirm", command=run_vpypeline).grid(
        pady=(0, 10), row=current_row, column=1
    )

    window.protocol("WM_DELETE_WINDOW", lambda arg=window: on_closing(arg))

    set_theme(window)
    window.mainloop()

    return tuple(return_val)


if __name__ == "__main__":
    init()
    selected_files = select_files()
    if len(selected_files) == 0:
        print("No Design Files Selected")
    else:
        main(input_files=selected_files)
