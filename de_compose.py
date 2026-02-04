import os
import subprocess
from posixpath import join
from tkinter import CENTER, IntVar, Tk, ttk

from gui_helpers import (
    create_attribute_parse,
    create_url_label,
    disable_combobox_scroll,
    make_topmost_temp,
    on_focus_in,
    on_focus_out,
    separator,
    set_title_icon,
)
from links import PPP_URLS, VPYPE_URLS
from settings import DECOMPOSE_DEFAULTS, GLOBAL_DEFAULTS, init, set_theme
from utils import *


def main(input_files=()):
    """ "Run Decompose utility"""

    def run_vpypeline():
        global return_val
        check_make_temp_folder()
        if (
            not separate_files.get()
            and len(input_files) == 1
            and last_shown_command == build_vpypeline(True)
        ):
            rename_replace(show_temp_file, output_file_list[0])
            print("Same command as shown file, not re-running Vpype pipeline")
        else:
            command = build_vpypeline(False)
            print("Running: \n", command)
            result = subprocess.run(
                command, stdout=subprocess.PIPE, universal_newlines=True
            )
            if separate_files.get():
                return_val = str.splitlines(result.stdout)
            else:
                return_val = output_file_list

        print("Closing deCompose")
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
        global color_list

        # build output files list
        input_file_list = list(input_files)
        output_file_list = []
        for index, filename in enumerate(input_file_list):
            head, tail = os.path.split(filename)
            name, _ext = os.path.splitext(tail)
            show_temp_file = join(file_info["temp_folder_path"], name + "_deC.svg")
            output_filename = join(head, name + "_deC.svg")

            output_file_list.append(output_filename)

        # build color list
        num_layers = int(n_layers_entry.get())
        if len(color_list) != num_layers:
            color_list = []
            # generate color list for
            for _n in range(num_layers):
                color_list.append(generate_random_color())

        args = f'vpype eval "files_in={input_file_list}" eval "files_out={output_file_list}" '
        args += r' eval "random_colors=' + f"{color_list}" + '"'

        repeat_num = len(input_file_list)
        if show:
            repeat_num = 1

        args += f" repeat {repeat_num} "

        # keep track of last parsed used so that we can re-parse as necessary
        last_parse = ""

        file_input = r"%files_in[_i]%"

        sort = False
        if pre_linesort.get() or pre_line_shuffle.get():
            sort = True
            last_parse = pre_attribute_parse_entry.get()
            args += f' read {last_parse} --no-crop "{file_input}" '

        # presort/shuffle
        if pre_linesort.get():
            args += " linesort "

        if pre_line_shuffle.get():
            args += " lineshuffle "

        # separate design into layers
        if separate.get():
            args += f' eval "%num_layers={n_layers_entry.get()}%" '

            if last_parse != "":
                args += f' write "{show_temp_file}" ldelete all '  # TODO this would be a problem if I moved to multi-threading
                file_input = show_temp_file

            if separator_type.get():  # by distance
                last_parse = "single_layer"
                args += f' read --no-crop "{file_input}" '  # read as single layer

                if split_all.get():
                    args += " splitall "
                args += f" splitdist {split_dist_entry.get()}in "
                if split_all.get():
                    args += " linemerge "
                args += r' forlayer eval "%new_id=_i%%num_layers+1%" '
                args += r' lmove %_lid% "%new_id%" '
                args += r' color -l "%new_id%" "%random_colors[_lid%%num_layers]%" end '
            else:  # uniformly
                last_parse = uniform_attribute_parse_entry.get()
                args += f' read {last_parse} --no-crop "{file_input}" '
                args += r" forlayer "
                args += r' color -l %_lid% "%random_colors[_lid%%num_layers]%" '
                args += r' lmove %_lid% "%_lid%%num_layers+1%" '
                args += r" end "

        # remove layers
        def layer_parse(num_str, placeholder):
            """Takes a string with mixed numbers, commas, and dashes to create a list of numberered layers"""
            num = []
            if num_str == placeholder:
                return num

            "".join(num_str.split())  # strip out all whitespace

            for part in num_str.split(","):
                p1 = part.split("-")
                if len(p1) == 1:
                    num.append(int(p1[0]))
                else:
                    num.extend(list(range(int(p1[0]), int(p1[1]) + 1)))
            return num

        layers_to_remove = layer_parse(
            remove_layer_entry.get(), DECOMPOSE_DEFAULTS["remove_placeholder"]
        )

        remove_any = len(layers_to_remove) > 0

        if remove_any:
            remove_parse = remove_attribute_parse_entry.get()
            if last_parse == "":
                args += f' read {remove_parse} --no-crop "{file_input}" '
            elif last_parse != remove_parse:
                args += f' write "{show_temp_file}" ldelete all '  # TODO this would be a problem if I moved to multi-threading
                file_input = show_temp_file
                args += f' read {remove_parse} --no-crop "{file_input}" '

            last_parse = remove_parse

            for layer in layers_to_remove:
                args += f" ldelete {layer} "

        # Post sort/shuffle
        if linesort.get() or line_shuffle.get():
            sort = True
            post_parse = post_attribute_parse_entry.get()

            if last_parse == "":
                args += f' read {post_parse} --no-crop "{file_input}" '
            elif last_parse != post_parse:
                args += f' write "{show_temp_file}" ldelete all '  # TODO this would be a problem if I moved to multi-threading
                file_input = show_temp_file
                args += f' read {post_parse} --no-crop "{file_input}" '
            last_parse = post_parse

        if linesort.get():
            args += " linesort "

        if line_shuffle.get():
            args += " lineshuffle "

        # Split into separate files
        if separate_files.get() and not show:  # doesn't work with show
            separate_parse = files_attribute_parse_entry.get()

            if last_parse == "":
                args += f' read {separate_parse} --no-crop "{file_input}" '
            elif last_parse != separate_parse:
                args += f' write "{show_temp_file}" ldelete all '  # TODO this would be a problem if I moved to multi-threading
                file_input = show_temp_file
                args += f' read {separate_parse} --no-crop "{file_input}" '
            last_parse = separate_parse

            args += r' eval "%k=_i%" '
            args += r" forlayer "
            args += (
                r' eval "%filename = files_out[k].replace('
                + r"'.svg'"
                + r", str(_lid)+"
                + r"'.svg'"
                + r')%" '
            )
            args += r' eval "%print(filename)%"'  # to be captured after running command
            args += r' write "%filename%" '
            args += r" end end"

            return args

        # CHECK IF NO OPTIONS ARE SELECTED AND RETURN AN EMPTY ARG AND FILE LIST
        if (
            not remove_any
            and not separate.get()
            and not separate_files.get()
            and not sort
        ):  # no operations
            if not show:
                output_file_list = []
                return ""
            else:  # if show is selected with no operations, parse as stroke and show
                args += f' read -a stroke --no-crop "{file_input}" '

        if show:
            args += f' write "{show_temp_file}" end show'
            return args
        else:
            args += r" write %files_out[_i]% end "

        return args

    global return_val, last_shown_command, remove_layer_list, color_list
    return_val = ()

    last_shown_command = ""
    color_list = []

    svg_width_inches = file_info["size_info"][0][0]  # first file first item
    svg_height_inches = file_info["size_info"][0][1]  # first file second item

    max_num_colors = max_colors_per_file()

    max_col = 4

    # tk widgets and window
    current_row = 0  # helper row var, inc-ed every time used;

    global window
    window = Tk()
    disable_combobox_scroll(window)

    set_title_icon(window, "deCompose")

    ttk.Label(window, text="deCompose").grid(
        pady=(10, 0), row=current_row, column=0, columnspan=max_col
    )
    current_row += 1

    create_url_label(
        window,
        "Plotter Post Processing deCompose Tutorial",
        PPP_URLS["decompose"],
    ).grid(row=current_row, column=0, columnspan=max_col)
    current_row += 1

    ttk.Label(
        window,
        text=f"{len(input_files)} file(s) selected, Input file Width(in): {svg_width_inches}, Height(in): {svg_height_inches}, Max colors in file(s): {max_num_colors}",
    ).grid(row=current_row, column=0, columnspan=max_col)

    current_row = separator(window, current_row, max_col)

    parse_label, pre_attribute_parse_entry = create_attribute_parse(
        window, GLOBAL_DEFAULTS["parse_stroke_color"]
    )
    parse_label.grid(row=current_row, column=0)
    pre_attribute_parse_entry.grid(sticky="w", row=current_row, column=1)

    current_row += 1

    create_url_label(window, "Sort Lines", VPYPE_URLS["linesort"]).grid(
        sticky="e", row=current_row, column=0
    )

    pre_linesort = IntVar(window, value=DECOMPOSE_DEFAULTS["pre_linesort"])
    ttk.Checkbutton(window, text="linesort", variable=pre_linesort).grid(
        sticky="w", row=current_row, column=1
    )

    create_url_label(window, "Shuffle Lines", VPYPE_URLS["lineshuffle"]).grid(
        sticky="e", row=current_row, column=2
    )

    pre_line_shuffle = IntVar(window, value=DECOMPOSE_DEFAULTS["pre_line_shuffle"])
    ttk.Checkbutton(window, text="lineshuffle", variable=pre_line_shuffle).grid(
        sticky="w", row=current_row, column=3
    )

    current_row = separator(window, current_row, max_col)

    separate = IntVar(window, value=DECOMPOSE_DEFAULTS["separate"])
    ttk.Checkbutton(window, text="Separate design in N layers", variable=separate).grid(
        sticky="w", row=current_row, column=0
    )

    ttk.Label(window, justify=CENTER, text="N").grid(row=current_row, column=1)
    n_layers_entry = ttk.Entry(window, width=7)
    n_layers_entry.insert(0, DECOMPOSE_DEFAULTS["n_layers"])
    n_layers_entry.grid(pady=(0, 10), sticky="w", row=current_row, column=2)

    current_row += 1

    separator_type = IntVar(window, value=DECOMPOSE_DEFAULTS["separate_by_dist"])
    ttk.Radiobutton(
        window,
        text="Uniform",
        variable=separator_type,
        value=DECOMPOSE_DEFAULTS["separate_uniformly"],
    ).grid(row=current_row, column=0)
    ttk.Radiobutton(
        window,
        text="By Distance (parse as single layer)",
        variable=separator_type,
        value=DECOMPOSE_DEFAULTS["separate_by_dist"],
    ).grid(row=current_row, column=2)
    current_row += 1

    parse_label, uniform_attribute_parse_entry = create_attribute_parse(
        window, GLOBAL_DEFAULTS["parse_individual_lines"]
    )
    parse_label.grid(row=current_row, column=0)
    uniform_attribute_parse_entry.grid(sticky="w", row=current_row, column=1)

    create_url_label(window, "Split Distance (in)", VPYPE_URLS["splitdist"]).grid(
        row=current_row, column=2
    )

    split_dist_entry = ttk.Entry(window, width=7)
    split_dist_entry.insert(0, DECOMPOSE_DEFAULTS["split_dist"])
    split_dist_entry.grid(sticky="w", row=current_row, column=3)
    current_row += 1

    create_url_label(window, "Split All and Merge", VPYPE_URLS["splitall"]).grid(
        row=current_row, column=2
    )

    split_all = IntVar(window, value=DECOMPOSE_DEFAULTS["split_all"])
    ttk.Checkbutton(window, text="splitall", variable=split_all).grid(
        sticky="w", row=current_row, column=3
    )

    current_row = separator(window, current_row, max_col)

    parse_label, remove_attribute_parse_entry = create_attribute_parse(
        window, GLOBAL_DEFAULTS["parse_stroke_color"]
    )
    parse_label.grid(row=current_row, column=0)
    remove_attribute_parse_entry.grid(sticky="w", row=current_row, column=1)

    create_url_label(window, "Remove Layers", VPYPE_URLS["ldelete"]).grid(
        row=current_row, column=2
    )

    remove_layer_list = []

    remove_layer_entry = ttk.Entry(window, width=12)
    remove_layer_entry.insert(0, DECOMPOSE_DEFAULTS["remove_placeholder"])
    remove_layer_entry.grid(sticky="w", row=current_row, column=3)

    remove_layer_entry.bind(
        "<Button-1>",
        lambda x: on_focus_in(
            remove_layer_entry, DECOMPOSE_DEFAULTS["remove_placeholder"]
        ),
    )
    remove_layer_entry.bind(
        "<FocusOut>",
        lambda x: on_focus_out(
            remove_layer_entry, DECOMPOSE_DEFAULTS["remove_placeholder"]
        ),
    )

    current_row = separator(window, current_row, max_col)

    parse_label, post_attribute_parse_entry = create_attribute_parse(
        window, GLOBAL_DEFAULTS["parse_stroke_color"]
    )
    parse_label.grid(row=current_row, column=0)
    post_attribute_parse_entry.grid(sticky="w", row=current_row, column=1)
    current_row += 1

    create_url_label(window, "Sort Lines", VPYPE_URLS["linesort"]).grid(
        sticky="e", row=current_row, column=0
    )

    linesort = IntVar(window, value=DECOMPOSE_DEFAULTS["linesort"])
    ttk.Checkbutton(window, text="linesort", variable=linesort).grid(
        sticky="w", row=current_row, column=1
    )

    create_url_label(window, "Shuffle Lines", VPYPE_URLS["lineshuffle"]).grid(
        sticky="e", row=current_row, column=2
    )

    line_shuffle = IntVar(window, value=DECOMPOSE_DEFAULTS["line_shuffle"])
    ttk.Checkbutton(window, text="lineshuffle", variable=line_shuffle).grid(
        sticky="w", row=current_row, column=3
    )

    current_row = separator(window, current_row, max_col)

    parse_label, files_attribute_parse_entry = create_attribute_parse(
        window, GLOBAL_DEFAULTS["parse_stroke_color"]
    )
    parse_label.grid(row=current_row, column=0)
    files_attribute_parse_entry.grid(sticky="w", row=current_row, column=1)

    create_url_label(
        window,
        "Separate SVG Layers into individual files\n(doesn't work with Show)",
        VPYPE_URLS["separate_files"],
    ).grid(row=current_row, column=2)

    separate_files = IntVar(window, value=DECOMPOSE_DEFAULTS["separate_files"])
    ttk.Checkbutton(window, text="Separate\nFiles", variable=separate_files).grid(
        sticky="w", row=current_row, column=3
    )

    current_row = separator(window, current_row, max_col)

    ttk.Button(window, text="Show Output", command=show_vpypeline).grid(
        pady=(0, 10), row=current_row, column=1
    )
    if len(input_files) > 1:
        ttk.Button(window, text="Apply to All", command=run_vpypeline).grid(
            pady=(0, 10), row=current_row, column=2
        )
    else:
        ttk.Button(window, text="Confirm", command=run_vpypeline).grid(
            pady=(0, 10), row=current_row, column=2
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
