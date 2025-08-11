import subprocess
import os
from tkinter import Tk, IntVar, CENTER
from tkinter import ttk
from utils import select_files, generate_random_color, file_info, get_files, max_colors_per_file
from utils import rename_replace, on_closing, check_make_temp_folder, open_url_in_browser
import settings


def main(input_files=()):
    def run_vpypeline():
        global return_val

        if len(input_files) == 1 and last_shown_command == build_vpypeline(show=True):
            rename_replace(show_temp_file, output_filename)
            print("Same command as shown file, not re-running Vpype pipeline")
        else:
            command = build_vpypeline(show=False)
            print("Running: \n", command)
            subprocess.run(command, capture_output=True, shell=True)
        
        return_val = output_file_list
        print("Closing Occult")
        on_closing(window)

    def show_vpypeline():
        """Runs given commands on first file, but only shows the output. Cleans up any Occult generated temp files."""
        global last_shown_command
        check_make_temp_folder()

        last_shown_command = build_vpypeline(show=True)
        print("Showing: \n", last_shown_command)
        subprocess.run(last_shown_command, capture_output=True, shell=True)

    def build_vpypeline(show):
        """Builds vpype command based on GUI selections"""
        global show_temp_file
        global output_filename
        global output_file_list
        global color_list

        #build output files list
        input_file_list = list(input_files)
        output_file_list = []
        for filename in input_file_list:
            head, tail = os.path.split(filename)
            name, _ext = os.path.splitext(tail)
            show_temp_file = head + "/ppp_temp/" + name + "_O.svg"
            output_filename = head + "/" + name + "_O.svg"
            output_file_list.append(output_filename)

        sorted_occult_info_list = sorted(occult_info_list, key=lambda d: d['order'].get())

        args = r"vpype "
        args += r' eval "files_in=' + f"{input_file_list}" + '"'
        args += r' eval "files_out=' + f"{output_file_list}" + '"'
        args += r' eval "random_colors=' + f"{color_list}" + '"'

        if show:
            repeat_num = 1
        else:
            repeat_num = len(input_file_list)
        args += f" repeat {repeat_num} " #repeat for both single and batch operations

        # FILE READING
        parse = "-a stroke" # default value
        if attribute.get() == 0:
            parse = "-a d -a points"

        args += f" read {parse} --no-crop %files_in[_i]% "

        for occult_info in sorted_occult_info_list:
            if "file" in occult_info:
                args += r' forlayer eval "%last_layer=_lid%" end '
                args += r' read '
                if not occult_file_info["crop"].get():
                    args += r' --no-crop '
                args += r' --layer "%last_layer+1%" '
                args += f' "{occult_info["file"]}" '
                if occult_info["color"].get():
                    args += f' color -l "%last_layer+1%" {occult_info["color_info"].get()} '

            args += r' forlayer eval "%last_layer=_lid%" end '
            if occult_info["occult"].get():
                args += r" occult "
                if occult_info["ignore"].get():
                    args += r" -i "
                elif occult_info["across"].get():
                    args += r" -a "
                if occult_info["keep"].get():
                    args += r" -k "
                    args += r' forlayer eval "%kept_layer=_lid%" end '
                    args += f' eval "%last_color=random_colors[{occult_info["order"].get()}]%" '
                    args += r' forlayer eval "%if(kept_layer<last_layer+1):last_color=_color%" end ' #recolor kept lines if there are any kept lines
                    args += r' color -l %kept_layer% %last_color% '
        
        if show:
            reread_file_cmd = ""
            if attribute.get() == 0:
                reread_file_cmd = f'ldelete all read -a stroke --no-crop "{show_temp_file}"'

            args += f' write "{show_temp_file}" end {reread_file_cmd} show '

            return args
        else:
            args += r' write %files_out[_i]% end'

            return args


    global return_val, last_shown_command, color_list, occult_color_list
    return_val = ()
    last_shown_command = ""

    occlusion_file_list = get_files("SELECT OCCLUSION FILE(s) (OPTIONAL)")
    if len(occlusion_file_list) > 0:
        print(f"Currently Loaded Occlusion Files: {occlusion_file_list}")
    else:
        print("No Occlusion files selected")

    svg_width_inches = file_info["size_info"][0][0] #first file first item
    svg_height_inches = file_info["size_info"][0][1] #first file second item

    color_list = []
    #generate color list for each potential -k
    for file in input_files + occlusion_file_list:
        color_list.append(generate_random_color())

    occult_color_list = []
    for file in occlusion_file_list:
        occult_color_list.append(generate_random_color())

    #tk widgets and window
    current_row = 0 #helper row var, inc-ed every time used;

    global window
    window = Tk()

    title = ttk.Label(window, text="Occluded Line Removal", foreground=settings.THEME_SETTINGS["link_color"], cursor="hand2")
    title.bind("<Button-1>", lambda e: open_url_in_browser("https://github.com/LoicGoulefert/occult"))
    title.grid(pady=(10,0), row=current_row,column=0, columnspan=4)
    current_row += 1

    ttk.Label(window, justify=CENTER, text=f"{len(input_files)} Design file(s) selected, {len(occlusion_file_list)} Occlusion file(s) selected, \nDesign file Width(in): {svg_width_inches}, Height(in): {svg_height_inches}").grid(row=current_row, column=0, columnspan=4)
    current_row +=1 

    ttk.Label(window, text="Parse Design file using: ").grid(row=current_row, column=0)
    attribute = IntVar(window, value=0)
    if max_colors_per_file() == 1 or len(occlusion_file_list) > 0:
        attribute = IntVar(window, value=1)
    ttk.Radiobutton(window, text="d/point", variable=attribute, value=0).grid(row=current_row, column=1)
    ttk.Radiobutton(window, text="stroke", variable=attribute, value=1).grid(row=current_row, column=2)

    current_row += 1

    ttk.Separator(window, orient='horizontal').grid(sticky="we", row=current_row, column=0, columnspan=4, pady=10)
    current_row += 1

    occult_info_list = []

    if len(occlusion_file_list) == 0:
        occult_file_info = {}
        occult_order = ttk.Combobox(
            window,
            values=[0]
        )
        occult_order.current(0)
        occult_file_info["order"] = occult_order

        occult = IntVar(window, value=1)
        occult_file_info["occult"] = occult
        ttk.Checkbutton(window, text="Occult", variable=occult).grid(sticky="w", row=current_row, column=0)
        occult_keep_lines = IntVar(window, value=0)
        occult_file_info["keep"] = occult_keep_lines
        ttk.Checkbutton(window, text="Keep occulted lines", variable=occult_keep_lines).grid(sticky="w", row=current_row, column=1)
        current_row += 1 

        occult_ignore = IntVar(window, value=1)
        occult_file_info["ignore"] = occult_ignore
        ttk.Checkbutton(window, text="Ignores layers", variable=occult_ignore).grid(sticky="w", row=current_row, column=0)
        occult_across = IntVar(window, value=0)
        occult_file_info["across"] = occult_across
        ttk.Checkbutton(window, text="Occult across layers,\nnot within", variable=occult_across).grid(sticky="w", row=current_row, column=1)
        current_row +=1 

        ttk.Separator(window, orient='horizontal').grid(sticky="we", row=current_row, column=0, columnspan=4, pady=10)
        current_row += 1

        occult_info_list.append(occult_file_info)
    else:
        for index,file in enumerate(occlusion_file_list):
            occult_file_info = {"file": file}

            name = os.path.basename(os.path.normpath(file))
            ttk.Label(window, text=f"File: {name}").grid(row=current_row, column=0, columnspan=2)

            ttk.Label(window, text=f"Order: ").grid(row=current_row, column=2)
            occult_order = ttk.Combobox(
                window,
                width=4,
                state="readonly",
                values=[*range(len(occlusion_file_list))]
            )
            occult_order.current(index)
            occult_order.grid(sticky="w", row=current_row, column=3)
            occult_file_info["order"] = occult_order
            current_row += 1
            
            occult_crop = IntVar(window, value=0)
            occult_file_info["crop"] = occult_crop
            ttk.Checkbutton(window, text="Crop", variable=occult_crop).grid(sticky="e", row=current_row, column=0)
            occult_color = IntVar(window, value=0)
            occult_file_info["color"] = occult_color
            ttk.Radiobutton(window, text="Use File Color", variable=occult_color, value=0).grid(row=current_row, column=1)
            ttk.Radiobutton(window, text="Overwrite Color", variable=occult_color, value=1).grid(row=current_row, column=2)
            occult_color_entry = ttk.Entry(window, width=7)
            occult_file_info["color_info"] = occult_color_entry
            occult_color_entry.insert(0,f"{occult_color_list[index]}")
            occult_color_entry.grid(sticky="w", row=current_row, column=3)
            current_row += 1

            occult = IntVar(window, value=1)
            occult_file_info["occult"] = occult
            ttk.Checkbutton(window, text="Occult", variable=occult).grid(sticky="e", row=current_row, column=0)
            occult_keep_lines = IntVar(window, value=0)
            occult_file_info["keep"] = occult_keep_lines
            ttk.Checkbutton(window, text="Keep occulted lines", variable=occult_keep_lines).grid(sticky="w", row=current_row, column=1)
            occult_ignore = IntVar(window, value=1)
            occult_file_info["ignore"] = occult_ignore
            ttk.Checkbutton(window, text="Ignores layers", variable=occult_ignore).grid(sticky="w", row=current_row, column=2)
            occult_across = IntVar(window, value=0)
            occult_file_info["across"] = occult_across
            ttk.Checkbutton(window, text="Occult across layers,\nnot within", variable=occult_across).grid(sticky="w", row=current_row, column=3)
            current_row +=1 

            ttk.Separator(window, orient='horizontal').grid(sticky="we", row=current_row, column=0, columnspan=4, pady=10)
            current_row += 1

            occult_info_list.append(occult_file_info)

    ttk.Button(window, text="Show Output", command=show_vpypeline).grid(pady=(0,10), row=current_row, column=0)
    if len(input_files)>1:
        ttk.Button(window, text="Apply to All", command=run_vpypeline).grid(pady=(0,10), row=current_row, column=1)
    else:
        ttk.Button(window, text="Confirm", command=run_vpypeline).grid(pady=(0,10), row=current_row, column=1)

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
