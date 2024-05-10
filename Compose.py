import subprocess, os
from tkinter import *
from tkinter import ttk
from utils import *
import settings

def main(input_files=()):
    global on_closing
    def on_closing(): #clean up any temp files hanging around
        delete_temp_file(show_temp_file)
        print("Closing Compose")
        window.quit()


    def run_vpypeline():
        global return_val

        if last_shown_command == build_vpypeline(True):
            rename_replace(show_temp_file, output_file_list[0])
            print("Same command as shown file, not re-running Vpype pipeline")
        else:
            command = build_vpypeline(False)
            print("Running: \n", command)
            subprocess.run(command, capture_output=True, shell=True)

        return_val = output_file_list
        on_closing()


    def show_vpypeline():
        """Runs given commands on first file, but only shows the output."""
        global last_shown_command
        last_shown_command = build_vpypeline(True)
        print("Showing: \n", last_shown_command)
        subprocess.run(last_shown_command)


    def build_vpypeline(show):
        global show_temp_file
        global output_filename
        global output_file_list

        #build output files list
        input_file_list = list(input_files)
        output_file_list = []

        filename = input_file_list[0]
        file_parts = os.path.splitext(filename)
        show_temp_file = file_parts[0] + "_show_temp_file.svg"
        output_filename = file_parts[0] + "_C.svg"
        output_file_list.append(output_filename)
        #sort list in reverse, but load new files in lower number layers
        sorted_info_list = sorted(compose_info_list, key=lambda d: d['order'].get(), reverse=True)

        args = r"vpype "

        for index, info in enumerate(sorted_info_list):
            if index > 0:
                incoming_layer_number = 1
                if info["attribute"].get():
                    incoming_layer_number = max_colors_per_file([info["file"]])
                args += f' forlayer lmove "%_n-_i%" "%_n-_i+{incoming_layer_number}%" end ' #shift layers up the number of incoming layers
            if info["attribute"].get():
                args += f' read -a stroke "{info["file"]}" '
            else:
                args += r' forlayer eval "%last_layer=_lid%" end '
                args += f' read -l "%last_layer+1%" "{info["file"]}" '
                if info["overwrite_color"].get():
                    args += f' color -l "%last_layer+1%" {info["color_info"] }'

        if show:
            args += f' write "{show_temp_file}" show '
        else:
            args += f' write "{output_filename}" '

        return args


    global return_val, show_temp_file, last_shown_command, output_filename, compose_color_list, compose_info_list
    return_val = ()
    show_temp_file = ""
    last_shown_command = ""
    output_filename = ""

    if len(input_files) == 0:
        input_files = get_files("SELECT DESIGN FILE(s)")
        if len(input_files) == 0:
            print("No Design Files Selected")
            return ()
        else:
            print(f"Currently Loaded Design Files: {input_files}")

    svg_width_inches, svg_height_inches = get_svg_width_height(input_files[0])

    compose_color_list = []
    #generate color list for each potential -k
    for file in input_files:
        compose_color_list.append(generate_random_color(file, compose_color_list))

    #tk widgets and window
    current_row = 0 #helper row var, inc-ed every time used;

    global window
    window = Tk()

    ttk.Label(window, text="Compose").grid(pady=(10,0), row=current_row,column=0, columnspan=4)
    current_row += 1

    ttk.Label(window, justify=CENTER, text=f"{len(input_files)} Design file(s) selected,\nDesign file Width(in): {svg_width_inches}, Height(in): {svg_height_inches}").grid(row=current_row, column=0, columnspan=4)
    current_row +=1 

    ttk.Separator(window, orient='horizontal').grid(sticky="we", row=current_row, column=0, columnspan=4, pady=10)
    current_row += 1

    compose_info_list = []

    for index,file in enumerate(input_files):
        compose_info = {"file": file}

        name = os.path.basename(os.path.normpath(file))
        ttk.Label(window, text=f"File: {name}").grid(row=current_row, column=0, columnspan=2)

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

        ttk.Label(window, text=f"Colors in file: {max_colors_per_file([file])}").grid(row=current_row, column=0)

        attribute = IntVar(window, value=0)
        if max_colors_per_file(input_files) == 1:
            attribute = IntVar(window, value=1)
        compose_info["attribute"] = attribute
        ttk.Radiobutton(window, text="single layer", variable=attribute, value=0).grid(row=current_row, column=1)
        ttk.Radiobutton(window, text="stroke layer(s)", variable=attribute, value=1).grid(row=current_row, column=2)
        current_row += 1

        overwrite_color = IntVar(window, value=0)
        compose_info["overwrite_color"] = overwrite_color
        ttk.Checkbutton(window, text="If single layer, overwrite color?", variable=overwrite_color).grid(sticky="e", row=current_row, column=0, columnspan=2)
        compose_color_entry = ttk.Entry(window, width=7)
        compose_info["color_info"] = compose_color_entry
        compose_color_entry.insert(0,f"{compose_color_list[index]}")
        compose_color_entry.grid(sticky="w", row=current_row, column=2)
        current_row += 1

        ttk.Separator(window, orient='horizontal').grid(sticky="we", row=current_row, column=0, columnspan=4, pady=10)
        current_row += 1

        compose_info_list.append(compose_info)

    ttk.Button(window, text="Show Output", command=show_vpypeline).grid(pady=(0,10), row=current_row, column=0)

    ttk.Button(window, text="Confirm", command=run_vpypeline).grid(pady=(0,10), row=current_row, column=1)

    window.protocol("WM_DELETE_WINDOW", on_closing)

    settings.set_theme(window)
    window.mainloop()

    return tuple(return_val)

if __name__ == "__main__":
    settings.init()
    main()