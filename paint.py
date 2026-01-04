import os
import subprocess
from posixpath import join
from tkinter import *
from tkinter import ttk

from gui_helpers import (
    create_scrollbar,
    create_toast,
    create_url_label,
    disable_combobox_scroll,
    make_topmost_temp,
    separator,
    set_title_icon,
)
from links import PPP_URLS, VPYPE_URLS
from settings import GLOBAL_DEFAULTS, PAINT_DEFAULTS, init, set_theme
from utils import *


def main(input_files=()):
    def generate_dips():
        input_file = list(input_files)[0]
        dip_detail_list = populate_dip_details()
        output_file = input_file.replace(".svg", "_DIPS.svg")

        command = f"""vpype \
eval "dip_details={dip_detail_list}" \
read -a stroke "{input_file}" \
forlayer \
eval "stroke_color=_prop.vp_color" \
eval "stroke_width=_prop.vp_pen_width" \
ldelete %_lid% \
read -l "%_lid%" %dip_details[_i][0]% \
rotate -l "%_lid%" "%dip_details[_i][3]%" \
translate -l "%_lid%" "%dip_details[_i][1]%in" "%dip_details[_i][2]%in" \
color -l %_lid% %stroke_color% \
propset -l %_lid% -t float vp_pen_width %stroke_width% \
end \
write "{output_file}" """
        print("Generating Dips with: \n", command)
        result = subprocess.run(
            command, stdout=subprocess.PIPE, universal_newlines=True
        )

        create_toast(window, 4000, f"Saved DIP file at: \n{output_file}")

        print("\nSaved Dips Only SVG at:\n", output_file)

    def run_vpypeline():
        global return_val

        if len(input_files) == 1 and last_shown_command == build_vpypeline(True):
            rename_replace(show_temp_file, output_filename)
            print("Same command as shown file, not re-running Vpype pipeline")
        else:
            command = build_vpypeline(False)
            print("Running: \n", command)
            result = subprocess.run(
                command, stdout=subprocess.PIPE, universal_newlines=True
            )
        return_val = output_file_list
        print("Closing Paint")
        on_closing(window)

    def show_vpypeline():
        """Runs given commands on first file, but only shows the output."""
        global last_shown_command
        check_make_temp_folder()
        last_shown_command = build_vpypeline(True)
        print("Showing: \n", last_shown_command)
        result = subprocess.run(
            last_shown_command, stdout=subprocess.PIPE, universal_newlines=True
        )
        make_topmost_temp(window)

    def populate_dip_details():
        dip_detail_list = []
        for i in range(max_num_colors):
            file_name = join(
                directory_name, "Dip_Locations", dip_details[i]["layer"].get()
            )
            dip_detail_list.append(
                [
                    file_name,
                    dip_details[i]["x"].get(),
                    dip_details[i]["y"].get(),
                    dip_details[i]["rotate"].get(),
                ]
            )
        return dip_detail_list

    def build_vpypeline(show):
        global show_temp_file
        global output_filename
        global output_file_list

        # build output files list
        input_file_list = list(input_files)
        output_file_list = []
        for filename in input_file_list:
            head, tail = os.path.split(filename)
            name, _ext = os.path.splitext(tail)
            show_temp_file = join(file_info["temp_folder_path"], name + "_PAINT.svg")
            output_filename = join(head, name + "_PAINT.svg")
            output_file_list.append(output_filename)

        dip_detail_list = populate_dip_details()

        splitall = ""
        linemerge = ""
        if split_all.get():
            splitall = "splitall"
            linemerge = "linemerge"

        if show:
            repeat_num = 1
            show_or_write = f' end write "{show_temp_file}" show '
        else:
            repeat_num = len(input_file_list)
            show_or_write = r"write %files_out[_i]% end"

        return f"""vpype \
eval "files_in={input_file_list}" \
eval "files_out={output_file_list}" \
eval "dip_details={dip_detail_list}" \
repeat {repeat_num} \
read -a stroke %files_in[_i]% \
forlayer \
eval "stroke_color=_prop.vp_color" \
eval "stroke_width=_prop.vp_pen_width" \
{splitall} \
splitdist {split_dist_entry.get()}in \
{linemerge} \
eval "j=_i" \
forlayer \
lmove %_lid% "%_lid*2%" \
read -l "%_lid*2-1%" %dip_details[j][0]% \
rotate -l "%_lid*2-1%" "%dip_details[j][3]%" \
translate -l "%_lid*2-1%" "%dip_details[j][1]%in" "%dip_details[j][2]%in" \
end \
lmove all %_lid% \
color -l %_lid% %stroke_color% \
propset -l %_lid% -t float vp_pen_width %stroke_width% \
end \
{show_or_write}"""

    global return_val, last_shown_command
    return_val = ()

    directory_name = get_directory_name("Paint.py")
    dip_options = os.listdir(join(directory_name, "Dip_Locations"))

    last_shown_command = ""

    svg_width_inches = file_info["size_info"][0][0]  # first file first item
    svg_height_inches = file_info["size_info"][0][1]  # first file second item

    max_num_colors = max_colors_per_file()

    # tk widgets and window
    current_row = 0  # helper row var, inc-ed every time used;
    max_col = 4

    global window
    window = Tk()
    disable_combobox_scroll(window)

    set_title_icon(window, "Paint")

    create_url_label(window, "Vpype Paint Recipe", VPYPE_URLS["dipping"]).grid(
        pady=(10, 0), row=current_row, column=0, columnspan=max_col
    )
    current_row += 1

    create_url_label(
        window, "Plotter Post Processing Paint Tutorial", PPP_URLS["paint"]
    ).grid(row=current_row, column=0, columnspan=max_col)
    current_row += 1

    ttk.Label(
        window,
        text="Input files should have already been processed and laid out with enough space for dipping trays",
    ).grid(row=current_row, column=0, columnspan=max_col)
    current_row += 1

    ttk.Label(
        window,
        text="Only batch files that have the same number of colors and you want to have the same dip details",
    ).grid(row=current_row, column=0, columnspan=max_col)
    current_row += 1

    create_url_label(
        window,
        "Dip locations match number of colors in file, file parsed with -a stroke.",
        VPYPE_URLS["attribute_parse"],
    ).grid(row=current_row, column=0, columnspan=max_col)
    current_row += 1

    ttk.Label(
        window,
        text=f"{len(input_files)} file(s) selected, Input file Width(in): {svg_width_inches}, Height(in): {svg_height_inches}, Max colors in file(s): {max_num_colors}",
    ).grid(row=current_row, column=0, columnspan=max_col)
    current_row += 1

    create_url_label(window, "Split All and Merge", VPYPE_URLS["splitall"]).grid(
        row=current_row, column=0
    )
    split_all = IntVar(window, value=PAINT_DEFAULTS["split_all"])
    ttk.Checkbutton(window, text="splitall", variable=split_all).grid(
        sticky="w", row=current_row, column=1
    )

    create_url_label(window, "Split Distance (in)", VPYPE_URLS["splitdist"]).grid(
        row=current_row, column=2
    )

    split_dist_entry = ttk.Entry(window, width=7)
    split_dist_entry.insert(0, PAINT_DEFAULTS["split_dist"])
    split_dist_entry.grid(row=current_row, column=3)

    current_row = separator(window, current_row, max_col)

    dip_details = []

    frame = window
    if max_num_colors > 2:
        frame = create_scrollbar(window, current_row, max_col)

    for i in range(max_num_colors):
        if i != 0:
            current_row = separator(frame, current_row, max_col)

        ttk.Label(frame, text=f"Dip Location {i}").grid(
            row=current_row, column=0, columnspan=max_col
        )
        current_row += 1

        ttk.Label(frame, text="Dip Layer").grid(row=current_row, column=0)
        dip_layer_combobox = ttk.Combobox(
            frame, width=20, state="readonly", values=dip_options
        )
        dip_layer_combobox.current(0)
        dip_layer_combobox.grid(sticky="w", row=current_row, column=1)

        create_url_label(
            frame, "Rotate Dip Clockwise (deg):", VPYPE_URLS["rotate"]
        ).grid(row=current_row, column=2)

        rotate_entry = ttk.Entry(frame, width=7)
        rotate_entry.insert(0, PAINT_DEFAULTS["rotate"])
        rotate_entry.grid(sticky="e", row=current_row, column=3)

        current_row += 1

        create_url_label(frame, "Translate X (in):", VPYPE_URLS["translate"]).grid(
            row=current_row, column=0
        )

        # TODO add dropdown options for populating x, y locations in different patterns
        # total number of dips (default is number of colors)
        # X spacing value or patterns, Y spacing value or patterns, cycle through dips if fewer dips than colors

        dip_loc_x_entry = ttk.Entry(frame, width=7)
        dip_loc_x_entry.insert(0, f"{i * 1 + 1}")
        dip_loc_x_entry.grid(sticky="w", row=current_row, column=1)

        ttk.Label(frame, text="Translate Y (in):").grid(row=current_row, column=2)
        dip_loc_y_entry = ttk.Entry(frame, width=7)
        dip_loc_y_entry.insert(0, "0")
        dip_loc_y_entry.grid(sticky="e", row=current_row, column=3)

        dip_details.append(
            {
                "x": dip_loc_x_entry,
                "y": dip_loc_y_entry,
                "rotate": rotate_entry,
                "layer": dip_layer_combobox,
            }
        )

    current_row = separator(window, current_row, max_col)
    ttk.Button(window, text="Save Dips Only SVG", command=generate_dips).grid(
        pady=(0, 10), row=current_row, column=0
    )

    ttk.Button(window, text="Show Output", command=show_vpypeline).grid(
        pady=(0, 10), row=current_row, column=2
    )
    if len(input_files) > 1:
        ttk.Button(window, text="Apply to All", command=run_vpypeline).grid(
            pady=(0, 10), row=current_row, column=3
        )
    else:
        ttk.Button(window, text="Confirm", command=run_vpypeline).grid(
            pady=(0, 10), row=current_row, column=3
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
