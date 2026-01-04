import os
import subprocess
from posixpath import join
from tkinter import CENTER, IntVar, Tk, ttk

from gui_helpers import (
    create_attribute_parse,
    create_url_label,
    disable_combobox_scroll,
    make_topmost_temp,
    separator,
    set_title_icon,
)
from links import OCCULT_URLS, PPP_URLS
from settings import GLOBAL_DEFAULTS, OCCULT_DEFAULTS, init, set_theme
from utils import (
    check_make_temp_folder,
    file_info,
    generate_random_color,
    on_closing,
    rename_replace,
    select_files,
)


def main(input_files=()):
    def run_vpypeline():
        global return_val

        if len(input_files) == 1 and last_shown_command == build_vpypeline(show=True):
            rename_replace(show_temp_file, output_filename)
            print("Same command as shown file, not re-running Vpype pipeline")
        else:
            command = build_vpypeline(show=False)
            print("Running: \n", command)
            subprocess.run(command, capture_output=True, shell=True, check=False)

        return_val = output_file_list
        print("Closing Occult")
        on_closing(window)

    def show_vpypeline():
        """Runs given commands on first file, but only shows the output. Cleans up any Occult generated temp files."""
        global last_shown_command
        check_make_temp_folder()

        last_shown_command = build_vpypeline(show=True)
        print("Showing: \n", last_shown_command)
        subprocess.run(last_shown_command, capture_output=True, shell=True, check=False)
        make_topmost_temp(window)

    def build_vpypeline(show):
        """Builds vpype command based on GUI selections"""
        global show_temp_file
        global output_filename
        global output_file_list
        global color_list

        # build output files list
        input_file_list = list(input_files)
        output_file_list = []
        for filename in input_file_list:
            head, tail = os.path.split(filename)
            name, _ext = os.path.splitext(tail)
            show_temp_file = join(file_info["temp_folder_path"], name + "_O.svg")
            output_filename = join(head, name + "_O.svg")
            output_file_list.append(output_filename)

        args = r"vpype "
        args += r' eval "files_in=' + f"{input_file_list}" + '"'
        args += r' eval "files_out=' + f"{output_file_list}" + '"'
        args += r' eval "random_colors=' + f"{color_list}" + '"'

        if show:
            repeat_num = 1
        else:
            repeat_num = len(input_file_list)
        # repeat for both single and batch operations
        args += f" repeat {repeat_num} "

        # FILE READING
        parse = attribute_parse_entry.get()

        args += f" read {parse} --no-crop %files_in[_i]% "

        args += r' forlayer eval "%last_layer=_lid%" end '
        if occult.get():
            args += r" occult "
            if occult_ignore.get():
                args += r" -i "
            elif occult_across.get():
                args += r" -a "
            if occult_keep_lines.get():
                args += r" -k "
                args += r' forlayer eval "%kept_layer=_lid%" end '
                args += f' eval "%last_color=random_colors[_i]%" '
                # recolor kept lines if there are any kept lines
                args += r' forlayer eval "%if(kept_layer<last_layer+1):last_color=_color%" end '
                args += r" color -l %kept_layer% %last_color% "

        if show:
            args += f' write "{show_temp_file}" end '
            if reparse_with_stroke.get():
                args += f'ldelete all read -a stroke --no-crop "{show_temp_file}" write "{show_temp_file}" '
            args += " show "

        else:
            args += r" write %files_out[_i]% end "
            if reparse_with_stroke.get():
                args += f"ldelete all read -a stroke --no-crop %files_out[_i]% write %files_out[_i]% "

        return args

    global return_val, last_shown_command, color_list
    return_val = ()
    last_shown_command = ""

    svg_width_inches = file_info["size_info"][0][0]  # first file first item
    svg_height_inches = file_info["size_info"][0][1]  # first file second item

    color_list = []
    # generate color list for each potential -k
    for _file in input_files:
        color_list.append(generate_random_color())

    max_col = 4

    # tk widgets and window
    current_row = 0  # helper row var, inc-ed every time used;

    global window
    window = Tk()
    disable_combobox_scroll(window)

    set_title_icon(window, "Occult")

    ttk.Label(window, text="Hidden Line Removal").grid(
        pady=(10, 0), row=current_row, column=0, columnspan=max_col
    )

    current_row += 1

    create_url_label(window, "Occult Help", OCCULT_URLS["occult"]).grid(
        row=current_row, column=0, columnspan=max_col
    )

    current_row += 1

    create_url_label(
        window, "Plotter Post Processing Occult Tutorial", PPP_URLS["occult"]
    ).grid(row=current_row, column=0, columnspan=max_col)

    current_row += 1

    ttk.Label(
        window,
        justify=CENTER,
        text=f"{len(input_files)} Design file(s) selected \nDesign file Width(in): {svg_width_inches}, Height(in): {svg_height_inches}",
    ).grid(row=current_row, column=0, columnspan=max_col)

    current_row = separator(window, current_row, max_col)

    entry_text = GLOBAL_DEFAULTS["parse_stroke_color"]
    if any(file_info["interleaved?"]):
        entry_text = GLOBAL_DEFAULTS["parse_individual_lines"]

    parse_label, attribute_parse_entry = create_attribute_parse(window, entry_text)
    parse_label.grid(row=current_row, column=0)
    attribute_parse_entry.grid(sticky="w", row=current_row, column=1)

    current_row = separator(window, current_row, max_col)

    occult = IntVar(window, value=OCCULT_DEFAULTS["occult"])
    ttk.Checkbutton(window, text="Occult", variable=occult).grid(
        sticky="w", row=current_row, column=0
    )
    occult_keep_lines = IntVar(window, value=OCCULT_DEFAULTS["keep_lines"])
    ttk.Checkbutton(
        window, text="Keep occulted lines", variable=occult_keep_lines
    ).grid(sticky="w", row=current_row, column=1)
    current_row += 1

    occult_ignore = IntVar(window, value=OCCULT_DEFAULTS["ignore_layers"])
    ttk.Checkbutton(window, text="Ignores layers", variable=occult_ignore).grid(
        sticky="w", row=current_row, column=0
    )
    occult_across = IntVar(window, value=OCCULT_DEFAULTS["across_layers"])
    ttk.Checkbutton(
        window, text="Occult across layers,\nnot within", variable=occult_across
    ).grid(sticky="w", row=current_row, column=1)

    current_row += 1

    reparse_val = OCCULT_DEFAULTS["reparse"]
    if any(file_info["interleaved?"]):
        reparse_val = OCCULT_DEFAULTS["reparse_interleaved"]
    reparse_with_stroke = IntVar(window, value=reparse_val)
    ttk.Checkbutton(
        window, text="Re-read parse file as -a stroke", variable=reparse_with_stroke
    ).grid(sticky="w", row=current_row, column=0)

    current_row = separator(window, current_row, max_col)

    ttk.Button(window, text="Show Output", command=show_vpypeline).grid(
        pady=(0, 10), row=current_row, column=0
    )
    if len(input_files) > 1:
        ttk.Button(window, text="Apply to All", command=run_vpypeline).grid(
            pady=(0, 10), row=current_row, column=1
        )
    else:
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
