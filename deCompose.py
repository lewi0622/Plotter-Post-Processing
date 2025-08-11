import subprocess, os
from tkinter import *
from tkinter import ttk
from utils import *
import settings

def main(input_files=()):
    def run_vpypeline():
        global return_val

        if len(input_files) == 1 and last_shown_command == build_vpypeline(True):
            rename_replace(show_temp_file, output_file_list[0])
            print("Same command as shown file, not re-running Vpype pipeline")
        else:
            command = build_vpypeline(False)
            print("Running: \n", command)
            subprocess.run(command, capture_output=True, shell=True)

        return_val = output_file_list
        print("Closing deCompose")
        on_closing(window)


    def show_vpypeline():
        """Runs given commands on first file, but only shows the output."""
        global last_shown_command
        check_make_temp_folder()
        last_shown_command = build_vpypeline(True)
        print("Showing: \n", last_shown_command)
        subprocess.run(last_shown_command)
        if separate_files.get(): #hacky solution to the separate files portion not being included in the show command
            last_shown_command = ""


    def build_vpypeline(show):
        global show_temp_file
        global output_filename
        global output_file_list
        global color_list

        #build output files list
        input_file_list = list(input_files)
        output_file_list = []
        for index, filename in enumerate(input_file_list):
            head, tail = os.path.split(filename)
            name, _ext = os.path.splitext(tail)
            show_temp_file = head + "/ppp_temp/" + name + "_deC.svg"
            output_filename = head + "/" + name + "_deC"

            if separate_files.get():
                for i in range(len(file_info["color_dicts"][index])):
                    output_file_list.append(output_filename + str(i) + ".svg")
            else:
                output_file_list.append(output_filename + ".svg")

        #build color list
        num_layers = int(n_layers_entry.get())
        if len(color_list) != num_layers:
            color_list = []
            #generate color list for 
            for _n in range(num_layers):
                color_list.append(generate_random_color())

        args = f'vpype eval "files_in={input_file_list}" eval "files_out={output_file_list}" '
        args += r' eval "random_colors=' + f"{color_list}" + '"'

        if separate_files.get() and not show:
            args += r' eval "%k=0%" '

        if separate.get():
            args += f' eval "%num_layers={n_layers_entry.get()}%" '

        repeat_num = len(input_file_list)
        if show:
            repeat_num = 1
        args += f" repeat {repeat_num} "

        #check for any layer removal
        remove_any = False
        for index, layer in enumerate(remove_layer_list):
            if layer.get():
                remove_any = True

        if not remove_any and not separate.get() and show: #just show case
            args += r" read -a stroke --no-crop %files_in[_i]%  end show"
            return args

        # remove color layers
        if remove_any:
            args += r" read -a stroke --no-crop %files_in[_i]% "
            for index, layer in enumerate(remove_layer_list):
                if layer.get():
                    args += f' ldelete {index+1} '

            if show and not separate.get():
                args += f' write "{show_temp_file}" end show '
                return args

        # separate
        if separate.get():
            if remove_any:
                args += f' write "{show_temp_file}" ldelete all ' #save to temp so it can be read by the separate step

            file_input = r'%files_in[_i]%'
            if remove_any:
                file_input = show_temp_file

            if separator_type.get():
                args += f" read --no-crop {file_input} "
                if split_all.get():
                    args += " splitall "
                args += f" splitdist {split_dist_entry.get()}in "
                if split_all.get():
                    args += " linemerge "
                args += r' forlayer eval "%new_id=_i%%num_layers+1%" '
                args += r' lmove %_lid% "%new_id%" '
                args += r' color -l "%new_id%" "%random_colors[_lid%%num_layers]%" end '
            else:
                args += f" read -a d -a points --no-crop {file_input} "
                args += f" filter --min-length {min_line_len_entry.get()}in "
                args += r" forlayer "
                args += r' color -l %_lid% "%random_colors[_lid%%num_layers]%" '
                args += r' lmove %_lid% "%_lid%%num_layers+1%" '
                args += r' end '
            
            if linesort.get():
                args += r' linesort '

            if show:
                args += f' write "{show_temp_file}" ldelete all'

        if separate_files.get() and not show:
            file_input = r'%files_in[_i]%'
            if remove_any or separate.get():
                file_input = show_temp_file
            args += f" read -a stroke --no-crop {file_input} "
            args += r" forlayer write " 
            args += r' %files_out[k]% '
            args += r' eval "k=k+1" '
            args += r" end end"

            return args

        if show:
            args += f' end ldelete all read -a stroke --no-crop "{show_temp_file}" show '
        else:
            args += r" write %files_out[_i]% end "

        # CHECK IF NO OPTIONS ARE SELECTED AND RETURN AN EMPTY ARG AND FILE LIST
        if not show and not remove_any and not separate.get() and not separate_files.get():
            output_file_list = []
            return ""

        return args

    global return_val, last_shown_command, remove_layer_list, color_list
    return_val = ()

    last_shown_command = ""
    color_list = []

    if len(input_files) == 0:
        input_files = select_files()

    svg_width_inches = file_info["size_info"][0][0] #first file first item
    svg_height_inches = file_info["size_info"][0][1] #first file second item

    max_num_colors = max_colors_per_file()

    #tk widgets and window
    current_row = 0 #helper row var, inc-ed every time used;

    global window
    window = Tk()
    title = ttk.Label(window, text="deCompose")
    title.grid(pady=(10,0), row=current_row,column=0, columnspan=4)
    current_row += 1

    ttk.Label(window, text=f"{len(input_files)} file(s) selected, Input file Width(in): {svg_width_inches}, Height(in): {svg_height_inches}, Max colors in file(s): {max_num_colors}").grid(row=current_row, column=0, columnspan=4)
    current_row +=1 

    ttk.Separator(window, orient='horizontal').grid(sticky="we", row=current_row, column=0, columnspan=4, pady=10)
    current_row += 1

    ttk.Label(window, justify=CENTER, text="Remove Layers").grid(row=current_row, column=0)
    remove_layer_list = []
    for index in range(max_num_colors):
        remove_layer = IntVar(window, value=0)
        remove_layer_list.append(remove_layer)
        ttk.Checkbutton(window, text=f"Layer {index + 1}", variable=remove_layer).grid(sticky="w", row=current_row, column=3)
        current_row += 1

    ttk.Separator(window, orient='horizontal').grid(sticky="we", row=current_row, column=0, columnspan=4, pady=10)
    current_row += 1

    separate = IntVar(window, value=0)
    ttk.Checkbutton(window, text="Separate design in N layers", variable=separate).grid(sticky="w", row=current_row, column=0)

    ttk.Label(window, justify=CENTER, text="N").grid(row=current_row, column=1)
    n_layers_entry = ttk.Entry(window, width=7)
    n_layers_entry.insert(0, "2")
    n_layers_entry.grid(sticky="w", row=current_row, column=2)
    current_row += 1

    ttk.Separator(window, orient='horizontal').grid(sticky="we", row=current_row, column=0, columnspan=4, padx=10, pady=10)
    current_row += 1

    separator_type = IntVar(window, value=1)
    ttk.Radiobutton(window, text="Uniform", variable=separator_type, value=0).grid(row=current_row, column=0)
    ttk.Radiobutton(window, text="By Distance", variable=separator_type, value=1).grid(row=current_row, column=2)
    current_row += 1

    ttk.Label(window, justify=CENTER, text="Min. line length (inches)").grid(row=current_row, column=0)
    min_line_len_entry = ttk.Entry(window, width=7)
    min_line_len_entry.insert(0, "0.2")
    min_line_len_entry.grid(sticky="w", row=current_row, column=1)

    ttk.Label(window, justify=CENTER, text="SplitDist (inches)").grid(row=current_row, column=2)
    split_dist_entry = ttk.Entry(window, width=7)
    split_dist_entry.insert(0, "20")
    split_dist_entry.grid(sticky="w", row=current_row, column=3)
    current_row += 1

    split_all_label = ttk.Label(window, text="Split All and Merge", foreground=settings.THEME_SETTINGS["link_color"], cursor="hand2")
    split_all_label.bind("<Button-1>", lambda e: open_url_in_browser("https://vpype.readthedocs.io/en/latest/reference.html#splitall"))
    split_all_label.grid(row=current_row, column=2)
    split_all = IntVar(window, value=0)
    ttk.Checkbutton(window, text="splitall", variable=split_all).grid(sticky="w", row=current_row,column=3)
    current_row += 1

    ttk.Separator(window, orient='horizontal').grid(sticky="we", row=current_row, column=0, columnspan=4, padx=10, pady=10)
    current_row += 1

    linesort = IntVar(window, value=1)
    ttk.Checkbutton(window, text="Sort after splitting into layers", variable=linesort).grid(sticky="w", row=current_row, column=0, columnspan=2)
    current_row += 1

    ttk.Separator(window, orient='horizontal').grid(sticky="we", row=current_row, column=0, columnspan=4, pady=10)
    current_row += 1

    separate_files_label = ttk.Label(window, justify=CENTER, text="Separate SVG Layers into individual files\n(doesn't work with Show)", foreground=settings.THEME_SETTINGS["link_color"], cursor="hand2")
    separate_files_label.bind("<Button-1>", lambda e: open_url_in_browser("https://vpype.readthedocs.io/en/latest/cookbook.html#saving-each-layer-as-a-separate-file"))
    separate_files_label.grid(row=current_row, column=0, columnspan=2)
    separate_files = IntVar(window, value=0)
    ttk.Checkbutton(window, text="Separate\nFiles", variable=separate_files).grid(sticky="w", row=current_row, column=2)
    current_row += 1

    ttk.Separator(window, orient='horizontal').grid(sticky="we", row=current_row, column=0, columnspan=4, pady=10)
    current_row += 1

    ttk.Button(window, text="Show Output", command=show_vpypeline).grid(pady=(0,10), row=current_row, column=1)
    if len(input_files)>1:
        ttk.Button(window, text="Apply to All", command=run_vpypeline).grid(pady=(0,10), row=current_row, column=2)
    else:
        ttk.Button(window, text="Confirm", command=run_vpypeline).grid(pady=(0,10), row=current_row, column=2)

    window.protocol("WM_DELETE_WINDOW", lambda arg=window: on_closing(arg))

    settings.set_theme(window)
    window.mainloop()

    return tuple(return_val)

if __name__ == "__main__":
    settings.init()
    main()