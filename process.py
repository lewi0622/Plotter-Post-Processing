"""General Vpype post-processing steps"""

from tkinter import CENTER, IntVar, Tk, ttk
from typing import Any

from gui_helpers import (
    create_page_layout_combobox,
    create_scrollbar,
    create_url_label,
    disable_combobox_scroll,
    generate_file_names,
    make_topmost_temp,
    separator,
    set_title_icon,
)
from links import PPP_URLS, VPYPE_URLS
from settings import GLOBAL_DEFAULTS, PROCESS_DEFAULTS, init, set_theme
from utils import (
    check_make_temp_folder,
    file_info,
    generate_random_color,
    on_closing,
    select_files,
    thread_vpypelines,
)

return_val: tuple
current_row: int
window: Any


def main(input_files: tuple = ()) -> tuple:
    """Builds and executes GUI of processing"""
    global return_val, current_row, last_shown_command, window
    return_val = ()
    current_row = 0  # helper row var, inc-ed every time used;

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
                "output_path": output_file_list[show_index],
            }

        thread_vpypelines(commands, show_commands, "Process", show_info)
        make_topmost_temp(window)

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

        attribute_parse = attribute_parse_entry.get()

        args = f" read {attribute_parse} "

        if not crop_input.get():
            args += r" --no-crop "

        args += r" %file_in% "

        if scale_option.get():
            args += (
                f" scaleto {scale_width_entry.get()}in {scale_height_entry.get()}in "
            )

        if bbox_option.get():
            bbox_x, bbox_y = bbox_xy_entry.get().split(",")
            bbox_w, bbox_h = bbox_wh_entry.get().split(",")
            try:
                bbox_x = float(bbox_x)
                bbox_y = float(bbox_y)
                bbox_w = float(bbox_w)
                bbox_h = float(bbox_h)

            except:
                print("Bounding Box values unable to be parsed into floats")

            args += (
                r" forlayer lmove %_lid% %_lid+1% end "  # moves each layer up by one
            )
            args += f" rect --layer 1 {bbox_x}in {bbox_y}in {bbox_w}in {bbox_h}in "
            args += f" color --layer 1 {bbox_color_entry.get()} "

        if center_geometries.get():
            args += " layout "
            if svg_width_inches > svg_height_inches:
                args += r" -l "
            args += f" {svg_width_inches}x{svg_height_inches}in "

        crop_x, crop_y = crop_xy_entry.get().split(",")
        crop_w, crop_h = crop_wh_entry.get().split(",")
        try:
            crop_x = float(crop_x)
            crop_y = float(crop_y)
            crop_w = float(crop_w)
            crop_h = float(crop_h)

            if crop_w > 0 and crop_h > 0:
                args += f" crop {crop_x}in {crop_y}in {crop_w}in {crop_h}in "
        except:
            print("Crop values unable to be parsed into floats")

        if rotate_entry.get() != 0:
            if "-" in rotate_entry.get():
                args += f" rotate -- {rotate_entry.get()} "
            else:
                args += f" rotate {rotate_entry.get()} "

        if linemerge.get():
            args += " linemerge "
            if (
                linemerge_tolerance_entry.get()
                != PROCESS_DEFAULTS["linemerge_tolerance"]
            ):
                args += f" -t {linemerge_tolerance_entry.get()}in "

        if linesort.get():
            args += r" linesort "

        if reloop.get():
            args += r" reloop "

        if linesimplify.get():
            args += " linesimplify "
            if (
                linesimplify_tolerance_entry.get()
                != PROCESS_DEFAULTS["linesimplify_tolerance"]
            ):
                args += f" -t {linesimplify_tolerance_entry.get()}in "

        if squiggle.get():
            args += " squiggles "
            if squiggle_amplitude_entry.get() != PROCESS_DEFAULTS["squiggle_amp"]:
                args += f" -a {squiggle_amplitude_entry.get()}in "
            if squiggle_period_entry.get() != PROCESS_DEFAULTS["squiggle_period"]:
                args += f" -p {squiggle_period_entry.get()}in "

        num_multipass = multipass_entry.get()
        try:
            num_multipass = int(num_multipass)
            if num_multipass > 1:
                args += f" multipass -n {num_multipass} "
        except:
            pass

        if lineshuffle.get():
            args += " lineshuffle "

        if reverse_order.get():
            args += " reverse "
            if flip_paths.get():
                args += " -f "

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
        for input_file, output_file, show_file in zip(
            input_files, output_file_list, show_file_list
        ):
            # prepend arg with files
            prepend = r"vpype "
            prepend += r' eval "file_in=' + f"'{input_file}'" + '"'
            prepend += r' eval "file_out=' + f"'{output_file}'" + '"'

            commands.append(prepend + args + r" write %file_out% ")
            show_commands.append(prepend + args + f' write "{show_file}" show ')

        return (commands, show_commands)

    last_shown_command = [""]

    svg_width_inches = file_info["size_info"][0][0]  # first file first item
    svg_height_inches = file_info["size_info"][0][1]  # first file second item

    bbox_color = generate_random_color()

    max_col = 4

    # tk widgets and window
    window = Tk()

    disable_combobox_scroll(window)

    window.geometry(PROCESS_DEFAULTS["window_size"])

    set_title_icon(window, "Process")

    window.grid_rowconfigure(0, weight=1)
    window.grid_columnconfigure(0, weight=1)

    frame = create_scrollbar(window)

    create_url_label(
        frame, "Plotter Post Processing Tutorial", PPP_URLS["process"]
    ).grid(pady=(10, 0), row=current_row, column=0, columnspan=max_col)
    current_row += 1

    ttk.Label(
        frame,
        justify=CENTER,
        text=f"{len(input_files)} file(s) selected, Input file Width(in): {svg_width_inches}, Height(in): {svg_height_inches}",
    ).grid(row=current_row, column=0, columnspan=max_col)

    current_row = separator(frame, current_row, max_col)

    create_url_label(frame, "Attribute Parse", VPYPE_URLS["attribute_parse"]).grid(
        row=current_row, column=0
    )
    attribute_parse_entry = ttk.Entry(frame, width=7)
    attribute_parse_entry.insert(0, GLOBAL_DEFAULTS["parse_stroke_color"])
    attribute_parse_entry.grid(sticky="w", row=current_row, column=1)

    create_url_label(
        frame, "Crop to input\ndimensions on read", VPYPE_URLS["crop_input"]
    ).grid(row=current_row, column=2)

    crop_input = IntVar(frame, value=PROCESS_DEFAULTS["crop"])
    ttk.Checkbutton(frame, text="Crop input", variable=crop_input).grid(
        sticky="w", row=current_row, column=3
    )

    current_row = separator(frame, current_row, max_col)

    create_url_label(
        frame, "Scale options\n(default: input file size)", VPYPE_URLS["scale"]
    ).grid(row=current_row, column=0)

    scale_option = IntVar(frame, value=PROCESS_DEFAULTS["scale"])
    ttk.Checkbutton(frame, text="Scale?", variable=scale_option).grid(
        sticky="w", row=current_row, column=1
    )

    ttk.Label(frame, justify=CENTER, text="Width Scale to (in):").grid(
        row=current_row, column=2
    )
    scale_width_entry = ttk.Entry(frame, width=7)
    scale_width_entry.insert(0, f"{svg_width_inches}")
    scale_width_entry.grid(sticky="w", row=current_row, column=3)
    current_row += 1

    ttk.Label(frame, justify=CENTER, text="Height Scale to (in):").grid(
        row=current_row, column=2
    )
    scale_height_entry = ttk.Entry(frame, width=7)
    scale_height_entry.insert(0, f"{svg_height_inches}")
    scale_height_entry.grid(sticky="w", row=current_row, column=3)

    current_row = separator(frame, current_row, max_col)

    bbox_option = IntVar(frame, value=PROCESS_DEFAULTS["bbox"])
    ttk.Checkbutton(frame, text="Add bounding box?", variable=bbox_option).grid(
        row=current_row, column=0, columnspan=2
    )

    create_url_label(frame, "Bbox Start, X, Y(in):", VPYPE_URLS["rect"]).grid(
        row=current_row, column=2
    )

    bbox_xy_entry = ttk.Entry(frame, width=7)
    bbox_xy_entry.insert(0, PROCESS_DEFAULTS["bbox_xy"])
    bbox_xy_entry.grid(sticky="w", row=current_row, column=3)

    current_row += 1

    ttk.Label(frame, justify=CENTER, text="Bounding Box color:").grid(
        row=current_row, column=0
    )
    bbox_color_entry = ttk.Entry(frame, width=7)
    bbox_color_entry.insert(0, f"{bbox_color}")
    bbox_color_entry.grid(sticky="w", row=current_row, column=1)

    ttk.Label(frame, justify=CENTER, text="Bbox Width, Height(in)").grid(
        row=current_row, column=2
    )
    bbox_wh_entry = ttk.Entry(frame, width=7)
    bbox_wh_entry.insert(0, f"{svg_width_inches}, {svg_height_inches}")
    bbox_wh_entry.grid(sticky="w", row=current_row, column=3)

    current_row = separator(frame, current_row, max_col)

    center_geometries = IntVar(frame, value=PROCESS_DEFAULTS["center"])
    ttk.Checkbutton(
        frame, text="Center Geometries to Input File Size", variable=center_geometries
    ).grid(row=current_row, column=0, columnspan=2)

    create_url_label(frame, "Crop Start, X, Y(in):", VPYPE_URLS["crop"]).grid(
        row=current_row, column=2
    )

    crop_xy_entry = ttk.Entry(frame, width=7)
    crop_xy_entry.insert(0, PROCESS_DEFAULTS["crop_xy"])
    crop_xy_entry.grid(sticky="w", row=current_row, column=3)
    current_row += 1

    create_url_label(frame, "Rotate Clockwise (deg):", VPYPE_URLS["rotate"]).grid(
        row=current_row, column=0
    )

    rotate_entry = ttk.Entry(frame, width=7)
    if (
        float(svg_width_inches) < float(svg_height_inches)
        and float(svg_width_inches) < 12
    ):
        # autorotate for small axidraw designs where the width is the long side
        rotate_entry.insert(0, PROCESS_DEFAULTS["rotate_small"])
    else:
        rotate_entry.insert(0, PROCESS_DEFAULTS["rotate_large"])
    rotate_entry.grid(sticky="w", row=current_row, column=1)

    ttk.Label(frame, justify=CENTER, text="Crop Width, Height(in)").grid(
        row=current_row, column=2
    )
    crop_wh_entry = ttk.Entry(frame, width=7)
    crop_wh_entry.insert(0, PROCESS_DEFAULTS["crop_wh"])
    crop_wh_entry.grid(sticky="w", row=current_row, column=3)

    current_row = separator(frame, current_row, max_col)

    create_url_label(
        frame, "Merge Lines with\noverlapping line endings", VPYPE_URLS["linemerge"]
    ).grid(row=current_row, column=0)

    linemerge = IntVar(frame, value=PROCESS_DEFAULTS["linemerge"])
    ttk.Checkbutton(frame, text="linemerge", variable=linemerge).grid(
        sticky="w", row=current_row, column=1
    )
    ttk.Label(frame, justify=CENTER, text="Linemerge tolerance (in):").grid(
        row=current_row, column=2
    )
    linemerge_tolerance_entry = ttk.Entry(frame, width=7)
    linemerge_tolerance_entry.insert(0, PROCESS_DEFAULTS["linemerge_tolerance"])
    linemerge_tolerance_entry.grid(sticky="w", row=current_row, column=3)
    current_row += 1

    create_url_label(frame, "Sort Lines", VPYPE_URLS["linesort"]).grid(
        row=current_row, column=0
    )

    linesort = IntVar(frame, value=PROCESS_DEFAULTS["linesort"])
    ttk.Checkbutton(frame, text="linesort", variable=linesort).grid(
        sticky="w", row=current_row, column=1
    )

    create_url_label(
        frame, "Randomize seam location\non closed paths", VPYPE_URLS["reloop"]
    ).grid(row=current_row, column=2)

    reloop = IntVar(frame, value=PROCESS_DEFAULTS["reloop"])
    ttk.Checkbutton(frame, text="reloop", variable=reloop).grid(
        sticky="w", row=current_row, column=3
    )
    current_row += 1

    create_url_label(
        frame, "Reduce geometric complexity", VPYPE_URLS["linesimplify"]
    ).grid(row=current_row, column=0)

    linesimplify = IntVar(frame, value=PROCESS_DEFAULTS["linesimplify"])
    ttk.Checkbutton(frame, text="linesimplify", variable=linesimplify).grid(
        sticky="w", row=current_row, column=1
    )
    ttk.Label(frame, justify=CENTER, text="Linesimplify tolerance (in):").grid(
        row=current_row, column=2
    )
    linesimplify_tolerance_entry = ttk.Entry(frame, width=7)
    linesimplify_tolerance_entry.insert(0, PROCESS_DEFAULTS["linesimplify_tolerance"])
    linesimplify_tolerance_entry.grid(sticky="w", row=current_row, column=3)

    current_row = separator(frame, current_row, max_col)

    create_url_label(frame, "Add squiggle filter", VPYPE_URLS["squiggles"]).grid(
        row=current_row, column=0
    )

    squiggle = IntVar(frame, value=PROCESS_DEFAULTS["squiggle"])
    ttk.Checkbutton(frame, text="squiggle", variable=squiggle).grid(
        sticky="w", row=current_row, column=1
    )

    ttk.Label(frame, justify=CENTER, text="Amplitude of squiggle (in):").grid(
        row=current_row, column=2
    )
    squiggle_amplitude_entry = ttk.Entry(frame, width=7)
    squiggle_amplitude_entry.insert(0, PROCESS_DEFAULTS["squiggle_amp"])
    squiggle_amplitude_entry.grid(sticky="w", row=current_row, column=3)
    current_row += 1

    ttk.Label(frame, justify=CENTER, text="Period of squiggle (in):").grid(
        row=current_row, column=2
    )
    squiggle_period_entry = ttk.Entry(frame, width=7)
    squiggle_period_entry.insert(0, PROCESS_DEFAULTS["squiggle_period"])
    squiggle_period_entry.grid(sticky="w", row=current_row, column=3)

    current_row = separator(frame, current_row, max_col)

    create_url_label(frame, "Number of passes", VPYPE_URLS["multipass"]).grid(
        row=current_row, column=0
    )
    multipass_entry = ttk.Entry(frame, width=7)
    multipass_entry.insert(0, PROCESS_DEFAULTS["multipass"])
    multipass_entry.grid(sticky="w", row=current_row, column=1)

    create_url_label(frame, "Randomize line order", VPYPE_URLS["lineshuffle"]).grid(
        row=current_row, column=2
    )

    lineshuffle = IntVar(frame, value=PROCESS_DEFAULTS["lineshuffle"])
    ttk.Checkbutton(frame, text="lineshuffle", variable=lineshuffle).grid(
        sticky="w", row=current_row, column=3
    )
    current_row += 1

    create_url_label(
        frame,
        "Reverse Drawing Order",
        VPYPE_URLS["reverse"],
    ).grid(row=current_row, column=0)

    reverse_order = IntVar(frame, value=PROCESS_DEFAULTS["reverse"])
    flip_paths = IntVar(frame, value=PROCESS_DEFAULTS["reverse_flip"])
    ttk.Checkbutton(frame, text="Reverse", variable=reverse_order).grid(
        sticky="w", row=current_row, column=1
    )
    ttk.Checkbutton(frame, text="Flip Path Direction", variable=flip_paths).grid(
        sticky="w", row=current_row, column=2
    )

    current_row = separator(frame, current_row, max_col)

    create_url_label(
        frame,
        "Layout centers scaled\ndesign in page size)",
        VPYPE_URLS["layout"],
    ).grid(row=current_row, column=0)

    layout = IntVar(frame, value=PROCESS_DEFAULTS["layout"])
    ttk.Checkbutton(frame, text="Layout?", variable=layout).grid(
        sticky="w", row=current_row, column=1
    )

    ttk.Label(frame, justify=CENTER, text="Page Layout Width(in):").grid(
        row=current_row, column=2
    )
    layout_width_entry = ttk.Entry(frame, width=7)
    layout_width_entry.grid(sticky="w", row=current_row, column=3)
    current_row += 1

    ttk.Label(frame, justify=CENTER, text="Page Layout Height(in):").grid(
        row=current_row, column=2
    )
    layout_height_entry = ttk.Entry(frame, width=7)
    layout_height_entry.grid(sticky="w", row=current_row, column=3)

    ttk.Label(frame, justify=CENTER, text="Page Size").grid(row=current_row, column=0)

    create_page_layout_combobox(
        frame,
        svg_width_inches,
        svg_height_inches,
        layout_width_entry,
        layout_height_entry,
    ).grid(sticky="w", row=current_row, column=1)

    current_row += 1

    ttk.Label(
        frame,
        justify=CENTER,
        text="By default, the larger layout size is the height,\nLandscape flips the orientation",
    ).grid(row=current_row, column=0, columnspan=2)
    layout_landscape = IntVar(frame, value=PROCESS_DEFAULTS["layout_landscape"])
    ttk.Checkbutton(frame, text="Landscape", variable=layout_landscape).grid(
        sticky="w", row=current_row, column=2
    )

    crop_to_page_size = IntVar(frame, value=PROCESS_DEFAULTS["crop_to_page_size"])
    ttk.Checkbutton(frame, text="Crop to\nPage Size", variable=crop_to_page_size).grid(
        sticky="w", row=current_row, column=3
    )

    current_row = separator(frame, current_row, max_col)

    show_index = 0
    ttk.Button(
        frame, text="Show Output", command=lambda: run_vpypeline(show_index)
    ).grid(pady=(0, 10), row=current_row, column=2)
    if len(input_files) > 1:
        ttk.Button(frame, text="Apply to All", command=run_vpypeline).grid(
            pady=(0, 10), row=current_row, column=3
        )
    else:
        ttk.Button(frame, text="Confirm", command=run_vpypeline).grid(
            pady=(0, 10), row=current_row, column=3
        )

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
