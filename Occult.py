import subprocess, os
from tkinter import *
from tkinter import ttk
from utils import *
import settings


def main(input_files=()):
    def on_closing(): #clean up any temp files hanging around
        delete_temp_file(show_temp_file)
        print("Closing Occult")
        window.quit()

    def run_vpypeline():
        """calls vpype cli to process """
        global return_val

        if len(input_files) == 1 and last_shown_command == build_vpypeline(show=True):
            rename_replace(show_temp_file, output_filename)
            print("Same command as shown file, not re-running Vpype pipeline")
        else:
            command = build_vpypeline(show=False)
            print("Running: \n", command)
            subprocess.run(command, capture_output=True, shell=True)

        delete_temp_file(show_temp_file)
        
        return_val = output_file_list
        on_closing()

    def show_vpypeline():
        """Runs given commands on first file, but only shows the output. Cleans up any Occult generated temp files."""
        global last_shown_command

        command = build_vpypeline(show=True)
        last_shown_command = command
        print("Showing: \n", command)
        subprocess.run(command, capture_output=True, shell=True)

    def build_vpypeline(show):
        """Builds vpype command based on GUI selections"""
        global show_temp_file
        global output_filename
        global output_file_list

        #build output files list
        input_file_list = list(input_files)
        output_file_list = []
        for filename in input_file_list:
            file_parts = os.path.splitext(filename)
            show_temp_file = file_parts[0] + "_show_temp_file.svg"
            output_filename = file_parts[0] + "_OCCLUDED.svg"
            output_file_list.append(output_filename)

        if occult_keep_lines.get():
            color_list = []
            for filename in input_file_list:
                color_list.append(generate_random_color(filename))

        args = r"vpype "
        args += r' eval "files_in=' + f"{input_file_list}" + '"'
        args += r' eval "files_out=' + f"{output_file_list}" + '"'
        if occult_keep_lines.get():
            args += r' eval "random_colors=' + f"{color_list}" + '"'

        if show:
            repeat_num = 1
        else:
            repeat_num = len(input_file_list)
        args += f" repeat {repeat_num} " #repeat for both single and batch operations

        if occult.get():

            if attribute.get() == 0:
                parse = "-a d -a points"
            elif attribute.get() == 1:
                parse = "-a stroke"

            args += f" read {parse} --no-crop %files_in[_i]% "

            if occult_keep_lines.get():
                #random color is applied to the added -k kept lines layer if it exists
                args += r' eval "%last_color=random_colors[_i]%" '
                args += r' forlayer eval "%num_layers=_n%" end '

            #occult function uses most recently drawn closed shapes to erase lines that are below the shape
            # the flag -i ignores layers and occults everything
            args += r" occult "
            if occult_ignore.get():
                args += r" -i "
            elif occult_accross.get():
                args += r" -a "
            if occult_keep_lines.get():
                args += r" -k "

                #check if -k kept lines, and overwrite color of kept lines with random color
                args += r' forlayer eval "%new_num_layers=_n%" '
                args += r' eval "%if(new_num_layers<=num_layers):last_color=_color%" end '
                args += r" color -l %new_num_layers% %last_color% "
        
        if show:
            reread_file_cmd = ""
            if attribute.get() == 0:
                reread_file_cmd = f'ldelete all read -a stroke --no-crop "{show_temp_file}"'

            args += f' write "{show_temp_file}" end {reread_file_cmd} show '

            return args
        else:
            args += r' write %files_out[_i]% end'

            return args


    global return_val, show_temp_file, last_shown_command, output_filename
    return_val = ()

    show_temp_file = ""
    last_shown_command = ""
    output_filename = ""

    if len(input_files) == 0:
        input_files = get_files()

    svg_width_inches, svg_height_inches = get_svg_width_height(input_files[0])

    #tk widgets and window
    current_row = 0 #helper row var, inc-ed every time used;

    global window
    window = Tk()

    title = ttk.Label(window, text="Occluded Line Removal", foreground=settings.link_color, cursor="hand2")
    title.bind("<Button-1>", lambda e: open_url_in_browser("https://github.com/LoicGoulefert/occult"))
    title.grid(pady=(10,0), row=current_row,column=0, columnspan=4)
    current_row += 1

    ttk.Label(window, justify=CENTER, text=f"{len(input_files)} file(s) selected,\nInput file Width(in): {svg_width_inches}, Height(in): {svg_height_inches}").grid(row=current_row, column=0, columnspan=2)
    current_row +=1 

    ttk.Label(window, text="Parse file using: ").grid(row=current_row, column=0)
    attribute = IntVar(window, value=0)
    ttk.Radiobutton(window, text="d/point", variable=attribute, value=0).grid(row=current_row, column=1)
    ttk.Radiobutton(window, text="stroke", variable=attribute, value=1).grid(row=current_row, column=2)
    current_row += 1

    ttk.Separator(window, orient='horizontal').grid(sticky="we", row=current_row, column=0, columnspan=4, pady=10)
    current_row += 1

    occult = IntVar(window, value=1)
    ttk.Checkbutton(window, text="Occult", variable=occult).grid(sticky="w", row=current_row, column=0)
    occult_keep_lines = IntVar(window, value=0)
    ttk.Checkbutton(window, text="Keep occulted lines", variable=occult_keep_lines).grid(sticky="w", row=current_row, column=1)
    current_row += 1 

    occult_ignore = IntVar(window, value=1)
    ttk.Checkbutton(window, text="Ignores layers", variable=occult_ignore).grid(sticky="w", row=current_row, column=0)
    occult_accross = IntVar(window, value=0)
    ttk.Checkbutton(window, text="Occult accross layers,\nnot within", variable=occult_accross).grid(sticky="w", row=current_row, column=1)
    current_row +=1 

    ttk.Separator(window, orient='horizontal').grid(sticky="we", row=current_row, column=0, columnspan=4, pady=10)
    current_row += 1

    ttk.Button(window, text="Show Output", command=show_vpypeline).grid(pady=(0,10), row=current_row, column=0)
    if len(input_files)>1:
        ttk.Button(window, text="Apply to All", command=run_vpypeline).grid(pady=(0,10), row=current_row, column=1)
    else:
        ttk.Button(window, text="Confirm", command=run_vpypeline).grid(pady=(0,10), row=current_row, column=1)

    window.protocol("WM_DELETE_WINDOW", on_closing)

    settings.set_theme(window)
    window.mainloop()

    return tuple(return_val)

if __name__ == "__main__":
    settings.init()
    main()