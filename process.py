"""General Vpype post-processing steps"""
from tkinter import Tk, IntVar, CENTER, END
from tkinter import ttk
from utils import thread_vpypelines, check_make_temp_folder, on_closing, find_closest_dimensions
from utils import select_files, file_info, generate_random_color, open_url_in_browser
from gui_helpers import separator, generate_file_names
from settings import THEME_SETTINGS, set_theme, init
from typing import Any

DEFAULTS: dict[str, str] = {
    "crop_x": "0, 0",
    "crop_y": "0, 0",
    "rotate_small": "90",
    "rotate_large": "0",
    "linemerge_tol": "0.0019",
    "linesimplify_tol": "0.0019",
    "squiggle_amp": "0.0196",
    "squiggle_period": "0.1181",
    "layout_w": "0",
    "layout_h": "0",
}

VPYPE_URLS: dict[str, str] = {
    "title": "https://vpype.readthedocs.io/en/latest/index.html",
    "crop_input": "https://vpype.readthedocs.io/en/latest/reference.html#cmdoption-read-c",
    "scale": "https://vpype.readthedocs.io/en/latest/reference.html#scaleto",
    "bbox": "https://vpype.readthedocs.io/en/latest/reference.html#bbox",
    "crop": "https://vpype.readthedocs.io/en/stable/reference.html#crop",
    "rotate": "https://vpype.readthedocs.io/en/latest/reference.html#rotate",
    "linemerge": "https://vpype.readthedocs.io/en/latest/reference.html#linemerge",
    "linesort": "https://vpype.readthedocs.io/en/latest/reference.html#linesort",
    "reloop": "https://vpype.readthedocs.io/en/latest/reference.html#reloop",
    "linesimplify": "https://vpype.readthedocs.io/en/latest/reference.html#linesimplify",
    "squiggles": "https://vpype.readthedocs.io/en/latest/reference.html#squiggles",
    "multipass": "https://vpype.readthedocs.io/en/latest/reference.html#multipass",
    "layout": "https://vpype.readthedocs.io/en/latest/reference.html#layout",
}


return_val: tuple
current_row: int
window: Any


def main(input_files: tuple = ()) -> tuple:
    """Builds and executes GUI of processing"""
    global return_val, current_row, last_shown_command, window
    return_val = ()
    current_row = 0  # helper row var, inc-ed every time used;
    link_color = THEME_SETTINGS["link_color"]

    def inc_row() -> int:
        """Increment the current row and return it"""
        global current_row
        current_row += 1
        return current_row

    def run_vpypeline(show_index: int = -1) -> None:
        global return_val

        show: bool = 0 <= show_index < len(input_files)

        commands, show_commands = build_vpypeline()
        show_info = {}
        if show:
            check_make_temp_folder()
            show_info = {
                "index": show_index,
                "show_path": show_file_list[show_index],
                "output_path": output_file_list[show_index]
            }
        thread_vpypelines(commands, show_commands, "Process", show_info)

        if not show:
            return_val = output_file_list
            print("Closing Process")
            on_closing(window)

    def build_vpypeline() -> tuple:
        """Builds vpype command based on GUI selections"""
        global show_file_list
        global output_file_list

        # build output files list
        output_file_list, show_file_list = generate_file_names(input_files, "_P.svg")

        args = r" read -a stroke "

        if not crop_input.get():
            args += r" --no-crop "

        args += r" %file_in% "

        if scale_option.get():
            args += f" scaleto {scale_width_entry.get()}in {scale_height_entry.get()}in "
            bbox_width = f"{scale_width_entry.get()}in"
            bbox_height = f"{scale_height_entry.get()}in"
        else:
            bbox_width = f"{svg_width_inches}in"
            bbox_height = f"{svg_height_inches}in"

        if bbox_option.get():
            args += r' forlayer lmove %_lid% %_lid+1% end '  # moves each layer up by one
            args += f" rect --layer 1 0 0 {bbox_width} {bbox_height} "
            args += f" color --layer 1 {bbox_color_entry.get()} "

        if center_geometries.get():
            args += " layout "
            if svg_width_inches > svg_height_inches:
                args += r" -l "
            args += f" {svg_width_inches}x{svg_height_inches}in "

        crop_x_start, crop_x_end = crop_x_entry.get().split(",")
        crop_y_start, crop_y_end = crop_y_entry.get().split(",")
        try:
            crop_x_start = float(crop_x_start)
            crop_x_end = float(crop_x_end)
            crop_y_start = float(crop_y_start)
            crop_y_end = float(crop_y_end)
            if crop_x_start != 0 or crop_x_end != 0 or crop_y_start != 0 or crop_y_end != 0:
                args += f" crop {crop_x_start}in {crop_y_start}in {crop_x_end}in {crop_y_end}in "
        except:
            print("Crop values unable to be parsed into floats")

        if rotate_entry.get() != 0:
            if "-" in rotate_entry.get():
                args += f" rotate -- {rotate_entry.get()} "
            else:
                args += f" rotate {rotate_entry.get()} "

        if linemerge.get():
            args += " linemerge "
            if linemerge_tolerance_entry.get() != "0.0019685":
                args += f" -t {linemerge_tolerance_entry.get()}in "

        if linesort.get():
            args += r" linesort "

        if reloop.get():
            args += r" reloop "

        if linesimplify.get():
            args += " linesimplify "
            if linesimplify_tolerance_entry.get() != "0.0019685":
                args += f" -t {linesimplify_tolerance_entry.get()}in "

        if squiggle.get():
            args += " squiggles "
            if squiggle_amplitude_entry.get() != "0.019685":
                args += f" -a {squiggle_amplitude_entry.get()}in "
            if squiggle_period_entry.get() != "0.11811":
                args += f" -p {squiggle_period_entry.get()}in "

        if multipass.get():
            args += " multipass "

        # layout as letter centers graphics within given page size
        if layout.get():
            args += r" layout "
            if layout_landscape.get():
                args += r" -l "
            args += f" {layout_width_entry.get()}x{layout_height_entry.get()}in "

            if crop_to_page_size.get():
                if layout_landscape.get():
                    args += f" crop 0 0 {layout_height_entry.get()}in {layout_width_entry.get()}in "
                else:
                    args += f" crop 0 0 {layout_width_entry.get()}in {layout_height_entry.get()}in "

        commands = []
        show_commands = []
        for input_file, output_file, show_file in zip(input_files, output_file_list, show_file_list):
            # prepend arg with files
            prepend = r"vpype "
            prepend += r' eval "file_in=' + f"'{input_file}'" + '"'
            prepend += r' eval "file_out=' + f"'{output_file}'" + '"'

            commands.append(prepend + args + r' write %file_out% ')
            show_commands.append(
                prepend + args + f' write "{show_file}" show ')

        return (commands, show_commands)

    def layout_selection_changed(e=None) -> None:
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
        elif selection == "11x17 in":
            layout_width_entry.insert(0, "11")
            layout_height_entry.insert(0, "17")
        elif selection == "A3":
            layout_width_entry.insert(0, "11.7")
            layout_height_entry.insert(0, "16.5")
        elif selection == "17x23 in":
            layout_width_entry.insert(0, "17")
            layout_height_entry.insert(0, "23")
        elif selection == "A2":
            layout_width_entry.insert(0, "16.5")
            layout_height_entry.insert(0, "23.4")
            layout.set(0)

    last_shown_command = [""]

    svg_width_inches = file_info["size_info"][0][0]  # first file first item
    svg_height_inches = file_info["size_info"][0][1]  # first file second item

    bbox_color = generate_random_color()

    # tk widgets and window
    window = Tk()

    title = ttk.Label(window, text="Vpype Options",
                      foreground=link_color, cursor="hand2")
    title.bind("<Button-1>", lambda e: open_url_in_browser(
        VPYPE_URLS["title"]))
    title.grid(pady=(10, 0), row=current_row, column=0, columnspan=4)

    ttk.Label(window, justify=CENTER, text=f"{len(input_files)} file(s) selected,\nInput file Width(in): {svg_width_inches}, Height(in): {svg_height_inches}").grid(
        row=inc_row(), column=0, columnspan=2)
    crop_input_label = ttk.Label(window, justify=CENTER, text="Crop to input\ndimensions on read",
                                 foreground=link_color, cursor="hand2")
    crop_input_label.bind("<Button-1>", lambda e: open_url_in_browser(
        VPYPE_URLS["crop_input"]))
    crop_input_label.grid(row=current_row, column=2)
    crop_input = IntVar(window, value=0)
    ttk.Checkbutton(window, text="Crop input", variable=crop_input).grid(
        sticky="w", row=current_row, column=3)

    current_row = separator(window, current_row, 4)

    scale_label = ttk.Label(window, justify=CENTER, text="Scale options\n(default: input file size)",
                            foreground=link_color, cursor="hand2")
    scale_label.bind("<Button-1>", lambda e: open_url_in_browser(
        VPYPE_URLS["scale"]))
    scale_label.grid(row=current_row, column=0)
    scale_option = IntVar(window, value=1)
    ttk.Checkbutton(window, text="Scale?", variable=scale_option).grid(
        sticky="w", row=current_row, column=1)

    ttk.Label(window, justify=CENTER, text="Width Scale to (in):").grid(
        row=current_row, column=2)
    scale_width_entry = ttk.Entry(window, width=7)
    scale_width_entry.insert(0, f"{svg_width_inches}")
    scale_width_entry.grid(sticky="w", row=current_row, column=3)

    ttk.Label(window, justify=CENTER, text="Height Scale to (in):").grid(
        row=inc_row(), column=2)
    scale_height_entry = ttk.Entry(window, width=7)
    scale_height_entry.insert(0, f"{svg_height_inches}")
    scale_height_entry.grid(sticky="w", row=current_row, column=3)

    current_row = separator(window, current_row, 4)

    bbox_option = IntVar(window, value=0)
    ttk.Checkbutton(window, text="Add bounding box?", variable=bbox_option).grid(
        row=current_row, column=0, columnspan=2)
    ttk.Label(window, justify=CENTER, text="Bounding Box color:").grid(
        row=current_row, column=2)
    bbox_color_entry = ttk.Entry(window, width=7)
    bbox_color_entry.insert(0, f"{bbox_color}")
    bbox_color_entry.grid(sticky="w", row=current_row, column=3)

    current_row = separator(window, current_row, 4)

    center_geometries = IntVar(window, value=1)
    ttk.Checkbutton(window, text="Center Geometries to Input File Size",
                    variable=center_geometries).grid(row=current_row, column=0, columnspan=2)

    crop_label = ttk.Label(window, justify=CENTER, text="Crop X Start, End (in):",
                           foreground=link_color, cursor="hand2")
    crop_label.bind("<Button-1>", lambda e: open_url_in_browser(
        VPYPE_URLS["crop"]))
    crop_label.grid(row=current_row, column=2)
    crop_x_entry = ttk.Entry(window, width=7)
    crop_x_entry.insert(0, DEFAULTS["crop_x"])
    crop_x_entry.grid(sticky="w", row=current_row, column=3)

    rotate_label = ttk.Label(window, justify=CENTER, text="Rotate Clockwise (deg):",
                             foreground=link_color, cursor="hand2")
    rotate_label.bind("<Button-1>", lambda e: open_url_in_browser(
        VPYPE_URLS["rotate"]))
    rotate_label.grid(row=inc_row(), column=0)
    rotate_entry = ttk.Entry(window, width=7)
    if float(svg_width_inches) < float(svg_height_inches) and float(svg_width_inches) < 12:
        # autorotate for small axidraw designs where the width is the long side
        rotate_entry.insert(0, DEFAULTS["rotate_small"])
    else:
        rotate_entry.insert(0, DEFAULTS["rotate_large"])
    rotate_entry.grid(sticky="w", row=current_row, column=1)

    ttk.Label(window, justify=CENTER, text="Crop Y Start, End (in):").grid(
        row=current_row, column=2)
    crop_y_entry = ttk.Entry(window, width=7)
    crop_y_entry.insert(0, DEFAULTS["crop_y"])
    crop_y_entry.grid(sticky="w", row=current_row, column=3)

    current_row = separator(window, current_row, 4)

    linemerge_label = ttk.Label(window, justify=CENTER, text="Merge Lines with\noverlapping line endings",
                                foreground=link_color, cursor="hand2")
    linemerge_label.bind("<Button-1>", lambda e: open_url_in_browser(
        VPYPE_URLS["linemerge"]))
    linemerge_label.grid(row=current_row, column=0)
    linemerge = IntVar(window, value=1)
    ttk.Checkbutton(window, text="linemerge", variable=linemerge).grid(
        sticky="w", row=current_row, column=1)
    ttk.Label(window, justify=CENTER, text="Linemerge tolerance (in):").grid(
        row=current_row, column=2)
    linemerge_tolerance_entry = ttk.Entry(window, width=7)
    linemerge_tolerance_entry.insert(0, DEFAULTS["linemerge_tol"])
    linemerge_tolerance_entry.grid(sticky="w", row=current_row, column=3)

    linesort_label = ttk.Label(window, justify=CENTER, text="Sort Lines",
                               foreground=link_color, cursor="hand2")
    linesort_label.bind("<Button-1>", lambda e: open_url_in_browser(
        VPYPE_URLS["linesort"]))
    linesort_label.grid(row=inc_row(), column=0)
    linesort = IntVar(window, value=1)
    ttk.Checkbutton(window, text="linesort", variable=linesort).grid(
        sticky="w", row=current_row, column=1)

    reloop_label = ttk.Label(window, justify=CENTER, text="Randomize seam location\non closed paths",
                             foreground=link_color, cursor="hand2")
    reloop_label.bind("<Button-1>", lambda e: open_url_in_browser(
        VPYPE_URLS["reloop"]))
    reloop_label.grid(row=current_row, column=2)
    reloop = IntVar(window, value=1)
    ttk.Checkbutton(window, text="reloop", variable=reloop).grid(
        sticky="w", row=current_row, column=3)

    linesimplify_label = ttk.Label(window, justify=CENTER, text="Reduce geometry complexity",
                                   foreground=link_color, cursor="hand2")
    linesimplify_label.bind("<Button-1>", lambda e: open_url_in_browser(
        VPYPE_URLS["linesimplify"]))
    linesimplify_label.grid(row=inc_row(), column=0)
    linesimplify = IntVar(window, value=1)
    ttk.Checkbutton(window, text="linesimplify", variable=linesimplify).grid(
        sticky="w", row=current_row, column=1)
    ttk.Label(window, justify=CENTER, text="Linesimplify tolerance (in):").grid(
        row=current_row, column=2)
    linesimplify_tolerance_entry = ttk.Entry(window, width=7)
    linesimplify_tolerance_entry.insert(0, DEFAULTS["linesimplify_tol"])
    linesimplify_tolerance_entry.grid(sticky="w", row=current_row, column=3)

    squiggle_label = ttk.Label(window, justify=CENTER, text="Add squiggle filter",
                               foreground=link_color, cursor="hand2")
    squiggle_label.bind("<Button-1>", lambda e: open_url_in_browser(
        VPYPE_URLS["squiggles"]))
    squiggle_label.grid(row=inc_row(), column=0)
    squiggle = IntVar(window, value=0)
    ttk.Checkbutton(window, text="squiggle", variable=squiggle).grid(
        sticky="w", row=current_row, column=1)

    ttk.Label(window, justify=CENTER, text="Amplitude of squiggle (in):").grid(
        row=current_row, column=2)
    squiggle_amplitude_entry = ttk.Entry(window, width=7)
    squiggle_amplitude_entry.insert(0, DEFAULTS["squiggle_amp"])
    squiggle_amplitude_entry.grid(sticky="w", row=current_row, column=3)

    ttk.Label(window, justify=CENTER, text="Period of squiggle (in):").grid(
        row=inc_row(), column=2)
    squiggle_period_entry = ttk.Entry(window, width=7)
    squiggle_period_entry.insert(0, DEFAULTS["squiggle_period"])
    squiggle_period_entry.grid(sticky="w", row=current_row, column=3)

    multipass_label = ttk.Label(window, justify=CENTER, text="Add multiple passes to all lines",
                                foreground=link_color, cursor="hand2")
    multipass_label.bind("<Button-1>", lambda e: open_url_in_browser(
        VPYPE_URLS["multipass"]))
    multipass_label.grid(row=inc_row(), column=0)
    multipass = IntVar(window, value=0)
    ttk.Checkbutton(window, text="multipass", variable=multipass).grid(
        sticky="w", row=current_row, column=1)

    current_row = separator(window, current_row, 4)

    layout_label = ttk.Label(window, justify=CENTER, text="Layout centers scaled\ndesign in page size)",
                             foreground=link_color, cursor="hand2")
    layout_label.bind("<Button-1>", lambda e: open_url_in_browser(
        VPYPE_URLS["layout"]))
    layout_label.grid(row=current_row, column=0)
    layout = IntVar(window, value=1)
    ttk.Checkbutton(window, text="Layout?", variable=layout).grid(
        sticky="w", row=current_row, column=1)

    ttk.Label(window, justify=CENTER, text="Page Layout Width(in):").grid(
        row=current_row, column=2)
    layout_width_entry = ttk.Entry(window, width=7)
    layout_width_entry.insert(0, DEFAULTS["layout_w"])
    layout_width_entry.grid(sticky="w", row=current_row, column=3)

    ttk.Label(window, justify=CENTER, text="Page Layout Height(in):").grid(
        row=inc_row(), column=2)
    layout_height_entry = ttk.Entry(window, width=7)
    layout_height_entry.insert(0, DEFAULTS["layout_h"])
    layout_height_entry.grid(sticky="w", row=current_row, column=3)

    page_size_values = ["Letter", "A4", "11x17 in", "A3", "17x23 in", "A2"]
    current_value_index = find_closest_dimensions(
        svg_width_inches, svg_height_inches)
    ttk.Label(window, justify=CENTER, text="Page Size").grid(
        row=current_row, column=0)
    layout_combobox = ttk.Combobox(
        window,
        width=7,
        state="readonly",
        values=page_size_values
    )
    layout_combobox.current(current_value_index)
    layout_combobox.grid(sticky="w", row=current_row, column=1)
    layout_combobox.bind("<<ComboboxSelected>>", layout_selection_changed)
    layout_selection_changed()

    layout_landscape_label = ttk.Label(
        window, justify=CENTER, text="By default, the larger layout size is the height,\nLandscape flips the orientation")
    layout_landscape_label.grid(row=inc_row(), column=0, columnspan=2)
    layout_landscape = IntVar(window, value=1)
    ttk.Checkbutton(window, text="Landscape", variable=layout_landscape).grid(
        sticky="w", row=current_row, column=2)

    crop_to_page_size = IntVar(window, value=1)
    ttk.Checkbutton(window, text="Crop to\nPage Size", variable=crop_to_page_size).grid(
        sticky="w", row=current_row, column=3)

    current_row = separator(window, current_row, 4)

    show_index = 0
    ttk.Button(window, text="Show Output", command=lambda: run_vpypeline(
        show_index)).grid(pady=(0, 10), row=current_row, column=2)
    if len(input_files) > 1:
        ttk.Button(window, text="Apply to All", command=run_vpypeline).grid(
            pady=(0, 10), row=current_row, column=3)
    else:
        ttk.Button(window, text="Confirm", command=run_vpypeline).grid(
            pady=(0, 10), row=current_row, column=3)

    window.protocol("WM_DELETE_WINDOW", lambda arg=window: on_closing(arg))

    set_theme(window)
    window.mainloop()

    return tuple(return_val)


if __name__ == "__main__":
    init()
    selected_files: tuple = select_files()
    if len(selected_files) == 0:
        print("No Design Files Selected")
    else:
        main(input_files=selected_files)
