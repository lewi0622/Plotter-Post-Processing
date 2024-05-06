import subprocess, os
from tkinter import *
from tkinter import ttk
from utils import *
import settings

def main(input_files=()):
    def on_closing(): #clean up any temp files hanging around
        delete_temp_file(show_temp_file)
        print("Closing deCompose")
        window.quit()


    def run_vpypeline():
        global return_val

        if len(input_files) == 1 and last_shown_command == build_vpypeline(True):
            rename_replace(show_temp_file, output_filename)
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
        command = build_vpypeline(True)
        last_shown_command = command
        print("Showing: \n", command)
        subprocess.run(command)


    def build_vpypeline(show):
        global show_temp_file
        global output_filename
        global output_file_list

        #build output files list
        input_file_list = list(input_files)
        output_file_list = []
        for filename in input_file_list:
            file_parts = os.path.splitext(filename)
            show_temp_file = file_parts[0] + "_show_temp_file.svg"
            output_filename = file_parts[0] + "_deCOMPOSE.svg"
            output_file_list.append(output_filename)

        args = f'vpype eval "files_in={input_file_list}" eval "files_out={output_file_list}" '

        if separate.get():
            args += f' eval "%num_layers={n_layers_entry.get()}%" '

        repeat_num = len(input_file_list)
        if show:
            repeat_num = 1
        args += f" repeat {repeat_num} "

        # remove color layers
        remove_any = False
        for index, layer in enumerate(remove_layer_list):
            if layer.get():
                remove_any = True
        if remove_any:
            args += r" read -a stroke --no-crop %files_in[_i]% "
            for index, layer in enumerate(remove_layer_list):
                if layer.get():
                    args += f' ldelete {index+1}'

            if show and not remove_any and not separate.get():
                args += " end show "
                return args

            args += f' write "{show_temp_file}" ldelete all ' #save to temp so it can be read by the separate step

        # separate
        if separate.get():
            file_input = r'%files_in[_i]%'
            if remove_any:
                file_input = show_temp_file

            args += f" read -a d -a points --no-crop  {file_input} "
            args += f" filter --min-length {min_line_len_entry.get()}in "
            args += r" forlayer "
            if override_colors.get():
                args += r' color -l %_lid% "%255-_lid%%num_layers%" '
            args += r' lmove %_lid% "%_lid%%num_layers+1%" '
            args += r' end '
            if linesort.get():
                args += r' linesort '

            if show:
                args += f' write "{show_temp_file}" '

        if show:
            args += f' end ldelete all read -a stroke --no-crop "{show_temp_file}" show '
        else:
            args += r"write %files_out[_i]% end"

        return args

    global return_val, show_temp_file, last_shown_command, output_filename, remove_layer_list
    return_val = ()

    show_temp_file = ""
    last_shown_command = ""
    output_filename = ""

    if len(input_files) == 0:
        input_files = get_files()

    svg_width_inches, svg_height_inches = get_svg_width_height(input_files[0])

    max_num_colors = max_colors_per_file(input_files)

    #tk widgets and window
    current_row = 0 #helper row var, inc-ed every time used;

    global window
    window = Tk()
    title = ttk.Label(window, text="deCompose", foreground=settings.link_color, cursor="hand2")
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
    ttk.Checkbutton(window, text="Separate design in N equal layers", variable=separate).grid(sticky="w", row=current_row, column=0)

    ttk.Label(window, justify=CENTER, text="N").grid(row=current_row, column=1)
    n_layers_entry = ttk.Entry(window, width=7)
    n_layers_entry.insert(0, "8")
    n_layers_entry.grid(sticky="w", row=current_row, column=2)
    current_row += 1

    ttk.Label(window, justify=CENTER, text="Min. line length (inches)").grid(row=current_row, column=1)
    min_line_len_entry = ttk.Entry(window, width=7)
    min_line_len_entry.insert(0, "0.2")
    min_line_len_entry.grid(sticky="w", row=current_row, column=2)
    current_row += 1

    override_colors = IntVar(window, value=1)
    ttk.Checkbutton(window, text="Override layers with new colors", variable=override_colors).grid(sticky="w", row=current_row, column=1, columnspan=2)
    current_row += 1

    linesort = IntVar(window, value=1)
    ttk.Checkbutton(window, text="Sort after splitting into layers", variable=linesort).grid(sticky="w", row=current_row, column=1, columnspan=2)
    current_row += 1

    ttk.Separator(window, orient='horizontal').grid(sticky="we", row=current_row, column=0, columnspan=4, pady=10)
    current_row += 1

    ttk.Button(window, text="Show Output", command=show_vpypeline).grid(pady=(0,10), row=current_row, column=1)
    if len(input_files)>1:
        ttk.Button(window, text="Apply to All", command=run_vpypeline).grid(pady=(0,10), row=current_row, column=2)
    else:
        ttk.Button(window, text="Confirm", command=run_vpypeline).grid(pady=(0,10), row=current_row, column=2)

    window.protocol("WM_DELETE_WINDOW", on_closing)

    settings.set_theme(window)
    window.mainloop()

    return tuple(return_val)

if __name__ == "__main__":
    settings.init()
    main()