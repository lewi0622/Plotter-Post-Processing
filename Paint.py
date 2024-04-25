import subprocess, os
from tkinter import *
from tkinter import ttk
from utils import *


def main():
    def on_closing(): #clean up any temp files hanging around
        delete_temp_file(show_temp_file)
        window.destroy()


    def run_vpypeline():
        window.quit()
        command = build_vpypeline(False)

        if len(input_files) == 1 and last_shown_command == build_vpypeline(True):
            rename_replace(show_temp_file, output_filename)
            print("Same command as shown file, not re-running Vpype pipeline")
        else:
            print("Running: \n", command)
            subprocess.run(command, capture_output=True, shell=True)

        delete_temp_file(show_temp_file)


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

        #build output files list
        input_file_list = list(input_files)
        output_file_list = []
        for filename in input_file_list:
            file_parts = os.path.splitext(filename)
            show_temp_file = file_parts[0] + "_show_temp_file.svg"
            output_filename = file_parts[0] + "_PAINT.svg"
            output_file_list.append(output_filename)
        
        dip_detail_list = []
        for i in range(max_num_colors):
            file_name = os.path.join(directory_name, "Dip_Locations", dip_details[i]['layer'].get())
            dip_detail_list.append([
                file_name,
                dip_details[i]["x"].get(), 
                dip_details[i]["y"].get()
                ])
        if split_all.get():
            splitall = "splitall"
            linemerge = "linemerge"
        else:
            splitall = ""
            linemerge = ""

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
{splitall} \
splitdist {split_dist_entry.get()}in \
{linemerge} \
eval "j=_i" \
forlayer \
lmove %_lid% "%_lid*2%" \
read -l "%_lid*2-1%" %dip_details[j][0]% \
translate -l "%_lid*2-1%" "%dip_details[j][1]%in" "%dip_details[j][2]%in" \
end \
lmove all %_lid% \
end \
{show_or_write}"""

    # global show_temp_file, last_shown_command, output_filename, window, input_files, dip_details, split_dist_entry, split_all, max_num_colors, directory_name
    directory_name = get_directory_name("Paint.py")
    dip_options = os.listdir(os.path.join(directory_name, "Dip_Locations"))

    show_temp_file = ""
    last_shown_command = ""
    output_filename = ""

    input_files = get_files()

    svg_width_inches, svg_height_inches = get_svg_width_height(input_files[0])

    max_num_colors = max_colors_per_file(input_files)

    #tk widgets and window
    current_row = 0 #helper row var, inc-ed every time used;

    window = Tk()
    title = Label(window, text="Vpype Paint", fg="blue", cursor="hand2")
    title.bind("<Button-1>", lambda e: open_url_in_browser("https://vpype.readthedocs.io/en/latest/cookbook.html#inserting-regular-dipping-patterns-for-plotting-with-paint"))
    title.grid(row=current_row,column=0, columnspan=4)
    current_row += 1

    Label(window, text="Input files should have already been processed\nand laid out with enough space for dipping trays").grid(row=current_row, column=0, columnspan=4)
    current_row +=1 

    Label(window, text=f"{len(input_files)} file(s) selected, Input file Width(in): {svg_width_inches}, Height(in): {svg_height_inches}, Max colors in file(s): {max_num_colors}").grid(row=current_row, column=0, columnspan=4)
    current_row +=1 

    split_all_label = Label(window, text="Split All and Merge?", fg="blue", cursor="hand2")
    split_all_label.bind("<Button-1>", lambda e: open_url_in_browser("https://vpype.readthedocs.io/en/latest/reference.html#splitall"))
    split_all_label.grid(row=current_row, column=0)
    split_all = IntVar(value=0)
    Checkbutton(window, text="splitall", variable=split_all).grid(sticky="w", row=current_row,column=1)

    split_dist_label = Label(window, text="Split Distance (in)", fg="blue", cursor="hand2")
    split_dist_label.bind("<Button-1>", lambda e: open_url_in_browser("https://vpype.readthedocs.io/en/latest/reference.html#cmd-splitdist"))
    split_dist_label.grid(row=current_row, column=2)

    split_dist_entry = Entry(window, width=7)
    split_dist_entry.insert(0,"4")
    split_dist_entry.grid(row=current_row, column=3)
    current_row +=1

    dip_details = []

    for i in range(max_num_colors):
        ttk.Separator(window, orient='horizontal').grid(sticky="we", row=current_row, column=0, columnspan=4)
        current_row += 1

        Label(window, text=f"Dip Loc {i}").grid(row=current_row, column=0, columnspan=4)
        current_row += 1

        Label(window, text="X (in)").grid(row=current_row, column=0)
        dip_loc_x_entry = Entry(window, width=7)
        dip_loc_x_entry.insert(0,f"{i * 2 + 1}")
        dip_loc_x_entry.grid(row=current_row, column=1)

        Label(window, text="Y (in)").grid(row=current_row, column=2)
        dip_loc_y_entry = Entry(window, width=7)
        dip_loc_y_entry.insert(0,"0")
        dip_loc_y_entry.grid(row=current_row, column=3)
        current_row += 1

        Label(window, text="Dip Layer").grid(row=current_row, column=0)
        dip_layer_combobox = ttk.Combobox(
            window,
            width=15,
            state="readonly",
            values=dip_options
        )
        dip_layer_combobox.current(0)
        dip_layer_combobox.grid(sticky="w", row=current_row, column=1)

        current_row += 1

        dip_details.append({
            "x": dip_loc_x_entry,
            "y": dip_loc_y_entry,
            "layer": dip_layer_combobox,
        })

    ttk.Separator(window, orient='horizontal').grid(sticky="we", row=current_row, column=0, columnspan=4)
    current_row += 1

    Button(window, text="Show Output", command=show_vpypeline).grid(row=current_row, column=2)
    if len(input_files)>1:
        Button(window, text="Apply to All", command=run_vpypeline).grid(row=current_row, column=3)
    else:
        Button(window, text="Confirm", command=run_vpypeline).grid(row=current_row, column=3)

    window.protocol("WM_DELETE_WINDOW", on_closing)
    window.mainloop()

if __name__ == "__main__":
    main()