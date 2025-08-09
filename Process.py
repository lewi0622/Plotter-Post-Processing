import subprocess, os
from tkinter import *
from tkinter import ttk
from utils import *
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
        print("Closing Process")
        on_closing(window)

    def show_vpypeline():
        """Runs given commands on first file, but only shows the output."""
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

        #build output files list
        input_file_list = list(input_files)
        if show:
            input_file_list = [input_file_list[0]]
        output_file_list = []
        for filename in input_file_list:
            head, tail = os.path.split(filename)
            name, _ext = os.path.splitext(tail)
            show_temp_file = head + "/ppp_temp/" + name + "_P.svg"
            output_filename = head + "/" + name + "_P.svg"

            output_file_list.append(output_filename)

        args = r"vpype "
        args += r' eval "files_in=' + f"{input_file_list}" + '"'
        args += r' eval "files_out=' + f"{output_file_list}" + '"'

        if show:
            repeat_num = 1
        else:
            repeat_num = len(input_file_list)
        args += f" repeat {repeat_num} "

        args += r" read -a stroke "

        if not crop_input.get():
            args += r" --no-crop "

        args += r" %files_in[_i]% "

        if scale_option.get():
            args += f" scaleto {scale_width_entry.get()}in {scale_height_entry.get()}in "
            bbox_width = f"{scale_width_entry.get()}in"
            bbox_height = f"{scale_height_entry.get()}in"
        else:
            bbox_width = f"{svg_width_inches}in"
            bbox_height = f"{svg_height_inches}in"

        if bbox_option.get():
            args += r' forlayer lmove %_lid% %_lid+1% end ' #moves each layer up by one
            args += f" rect --layer 1 0 0 {bbox_width} {bbox_height} "
            args += f" color --layer 1 {bbox_color_entry.get()} "

        if center_geometries.get():
            args += " layout "
            if svg_width_inches > svg_height_inches:
                args += r" -l "
            args += f" {svg_width_inches}x{svg_height_inches}in "

        crop_x_start, crop_x_end = crop_x_entry.get().split(",")
        crop_y_start, crop_y_end = crop_y_entry.get().split(",")
        try:
            crop_x_start = float(crop_x_start)
            crop_x_end = float(crop_x_end)
            crop_y_start = float(crop_y_start)
            crop_y_end = float(crop_y_end)
            if crop_x_start != 0 or crop_x_end !=0 or crop_y_start != 0 or crop_y_end !=0:
                args += f" crop {crop_x_start}in {crop_y_start}in {crop_x_end}in {crop_y_end}in "
        except:
            print("Crop values unable to be parsed into floats")

        if rotate_entry.get() != 0:
            if "-" in rotate_entry.get():
                args += f" rotate -- {rotate_entry.get()} "
            else:
                args += f" rotate {rotate_entry.get()} "

        if linemerge.get():
            args += f" linemerge "
            if linemerge_tolerance_entry.get() != "0.0019685":
                args += f" -t {linemerge_tolerance_entry.get()}in "

        if linesort.get():
            args += r" linesort "

        if reloop.get():
            args += r" reloop "  

        if linesimplify.get():
            args += f" linesimplify "
            if linesimplify_tolerance_entry.get() != "0.0019685":
                args += f" -t {linesimplify_tolerance_entry.get()}in "

        if squiggle.get():
            args += f" squiggles "
            if squiggle_amplitude_entry.get() != "0.019685":
                args += f" -a {squiggle_amplitude_entry.get()}in "
            if squiggle_period_entry.get() != "0.11811":
                args += f" -p {squiggle_period_entry.get()}in "

        if multipass.get():
            args += f" multipass "

        #layout as letter centers graphics within given page size
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
        if show:
            args += r" end "
            args += f' write "{show_temp_file}" show '
        else:
            args += r' write %files_out[_i]% end'

        return args


    def layout_selection_changed(event):
        """Event from changing the layout dropdown box, sets the width and height accordingly"""
        selection = layout_combobox.get()
        layout_width_entry.delete(0,END)
        layout_height_entry.delete(0,END)
        if selection == "Letter":
            layout_width_entry.insert(0,"8.5")
            layout_height_entry.insert(0,"11")
            layout.set(1)
        elif selection == "A4":
            layout_width_entry.insert(0,"8.3")
            layout_height_entry.insert(0,"11.7")
        elif selection == "11x17 in":
            layout_width_entry.insert(0,"11")
            layout_height_entry.insert(0,"17")
        elif selection == "A3":
            layout_width_entry.insert(0,"11.7")
            layout_height_entry.insert(0,"16.5")
        elif selection == "17x23 in":
            layout_width_entry.insert(0,"17")
            layout_height_entry.insert(0,"23")
        elif selection == "A2":
            layout_width_entry.insert(0,"16.5")
            layout_height_entry.insert(0,"23.4")
            layout.set(0)

    global return_val, last_shown_command
    return_val = ()

    last_shown_command = ""

    if len(input_files) == 0:
        input_files = select_files()
    svg_width_inches = file_info["size_info"][0][0] #first file first item
    svg_height_inches = file_info["size_info"][0][1] #first file second item

    bbox_color = generate_random_color()

    #tk widgets and window
    current_row = 0 #helper row var, inc-ed every time used;

    global window
    window = Tk()

    title = ttk.Label(window, text="Vpype Options", foreground=settings.link_color, cursor="hand2")
    title.bind("<Button-1>", lambda e: open_url_in_browser("https://vpype.readthedocs.io/en/latest/index.html"))
    title.grid(pady=(10,0), row=current_row,column=0, columnspan=4)
    current_row += 1

    ttk.Label(window, justify=CENTER, text=f"{len(input_files)} file(s) selected,\nInput file Width(in): {svg_width_inches}, Height(in): {svg_height_inches}").grid(row=current_row, column=0, columnspan=2)
    crop_input_label = ttk.Label(window, justify=CENTER, text="Crop to input\ndimensions on read", foreground=settings.link_color, cursor="hand2")
    crop_input_label.bind("<Button-1>", lambda e: open_url_in_browser("https://vpype.readthedocs.io/en/latest/reference.html#cmdoption-read-c"))
    crop_input_label.grid(row=current_row,column=2)
    crop_input = IntVar(window, value=0)
    ttk.Checkbutton(window, text="Crop input", variable=crop_input).grid(sticky="w", row=current_row,column=3)
    current_row +=1 

    ttk.Separator(window, orient='horizontal').grid(sticky="we", row=current_row, column=0, columnspan=4, pady=10)
    current_row += 1

    scale_label = ttk.Label(window, justify=CENTER, text="Scale options\n(default: input file size)", foreground=settings.link_color, cursor="hand2")
    scale_label.bind("<Button-1>", lambda e: open_url_in_browser("https://vpype.readthedocs.io/en/latest/reference.html#scaleto"))
    scale_label.grid(row=current_row, column=0)
    scale_option = IntVar(window, value=1)
    ttk.Checkbutton(window, text="Scale?", variable=scale_option).grid(sticky="w", row=current_row,column=1)

    ttk.Label(window, justify=CENTER, text="Width Scale to (in):").grid(row=current_row, column=2)
    scale_width_entry = ttk.Entry(window, width=7)
    scale_width_entry.insert(0,f"{svg_width_inches}")
    scale_width_entry.grid(sticky="w", row=current_row, column=3)
    current_row +=1 

    ttk.Label(window, justify=CENTER, text="Height Scale to (in):").grid(row=current_row, column=2)
    scale_height_entry = ttk.Entry(window, width=7)
    scale_height_entry.insert(0,f"{svg_height_inches}")
    scale_height_entry.grid(sticky="w", row=current_row, column=3)
    current_row +=1 

    ttk.Separator(window, orient='horizontal').grid(sticky="we", row=current_row, column=0, columnspan=4, pady=10)
    current_row += 1

    bbox_option = IntVar(window, value=0)
    ttk.Checkbutton(window, text="Add bounding box?", variable=bbox_option).grid(row=current_row, column=0, columnspan=2)
    ttk.Label(window, justify=CENTER, text="Bounding Box color:").grid(row=current_row, column=2)
    bbox_color_entry = ttk.Entry(window, width=7)
    bbox_color_entry.insert(0,f"{bbox_color}")
    bbox_color_entry.grid(sticky="w", row=current_row, column=3)
    current_row += 1

    ttk.Separator(window, orient='horizontal').grid(sticky="we", row=current_row, column=0, columnspan=4, pady=10)
    current_row += 1

    center_geometries = IntVar(window, value=1)
    ttk.Checkbutton(window, text="Center Geometries to Input File Size", variable=center_geometries).grid(row=current_row, column=0, columnspan=2)

    crop_label = ttk.Label(window, justify=CENTER, text="Crop X Start, End (in):", foreground=settings.link_color, cursor="hand2")
    crop_label.bind("<Button-1>", lambda e: open_url_in_browser("https://vpype.readthedocs.io/en/stable/reference.html#crop"))
    crop_label.grid(row=current_row, column=2)
    crop_x_entry = ttk.Entry(window, width=7)
    crop_x_entry.insert(0, "0, 0")
    crop_x_entry.grid(sticky="w", row=current_row, column=3)
    current_row += 1

    rotate_label = ttk.Label(window, justify=CENTER, text="Rotate Clockwise (deg):", foreground=settings.link_color, cursor="hand2")
    rotate_label.bind("<Button-1>", lambda e: open_url_in_browser("https://vpype.readthedocs.io/en/latest/reference.html#rotate"))
    rotate_label.grid(row=current_row, column=0)
    rotate_entry = ttk.Entry(window, width=7)
    if float(svg_width_inches) < float(svg_height_inches) and float(svg_width_inches)<12:
        rotate_entry.insert(0, "90") #autorotate for small axidraw designs where the width is the long side
    else:
        rotate_entry.insert(0, "0") 
    rotate_entry.grid(sticky="w", row=current_row, column=1)

    ttk.Label(window, justify=CENTER, text="Crop Y Start, End (in):").grid(row=current_row, column=2)
    crop_y_entry = ttk.Entry(window, width=7)
    crop_y_entry.insert(0, "0, 0")
    crop_y_entry.grid(sticky="w", row=current_row, column=3)
    current_row +=1 

    ttk.Separator(window, orient='horizontal').grid(sticky="we", row=current_row, column=0, columnspan=4, pady=10)
    current_row += 1

    linemerge_label = ttk.Label(window, justify=CENTER, text="Merge Lines with\noverlapping line endings", foreground=settings.link_color, cursor="hand2")
    linemerge_label.bind("<Button-1>", lambda e: open_url_in_browser("https://vpype.readthedocs.io/en/latest/reference.html#linemerge"))
    linemerge_label.grid(row=current_row, column=0)
    linemerge = IntVar(window, value=1)
    ttk.Checkbutton(window, text="linemerge", variable=linemerge).grid(sticky="w", row=current_row, column=1)
    ttk.Label(window, justify=CENTER, text="Linemerge tolerance (in):").grid(row=current_row, column=2)
    linemerge_tolerance_entry = ttk.Entry(window, width=7)
    linemerge_tolerance_entry.insert(0, "0.0019")
    linemerge_tolerance_entry.grid(sticky="w", row=current_row, column=3)
    current_row +=1 

    linesort_label = ttk.Label(window, justify=CENTER, text="Sort Lines", foreground=settings.link_color, cursor="hand2")
    linesort_label.bind("<Button-1>", lambda e: open_url_in_browser("https://vpype.readthedocs.io/en/latest/reference.html#linesort"))
    linesort_label.grid(row=current_row, column=0)
    linesort = IntVar(window, value=1)
    ttk.Checkbutton(window, text="linesort", variable=linesort).grid(sticky="w", row=current_row, column=1)

    reloop_label = ttk.Label(window, justify=CENTER, text="Randomize seam location\non closed paths", foreground=settings.link_color, cursor="hand2")
    reloop_label.bind("<Button-1>", lambda e: open_url_in_browser("https://vpype.readthedocs.io/en/latest/reference.html#reloop"))
    reloop_label.grid(row=current_row, column=2)
    reloop = IntVar(window, value=1)
    ttk.Checkbutton(window, text="reloop", variable=reloop).grid(sticky="w", row=current_row, column=3)
    current_row +=1 

    linesimplify_label = ttk.Label(window, justify=CENTER, text="Reduce geometry complexity", foreground=settings.link_color, cursor="hand2")
    linesimplify_label.bind("<Button-1>", lambda e: open_url_in_browser("https://vpype.readthedocs.io/en/latest/reference.html#linesimplify"))
    linesimplify_label.grid(row=current_row, column=0)
    linesimplify = IntVar(window, value=1)
    ttk.Checkbutton(window, text="linesimplify", variable=linesimplify).grid(sticky="w", row=current_row, column=1)
    ttk.Label(window, justify=CENTER, text="Linesimplify tolerance (in):").grid(row=current_row, column=2)
    linesimplify_tolerance_entry = ttk.Entry(window, width=7)
    linesimplify_tolerance_entry.insert(0, "0.0019")
    linesimplify_tolerance_entry.grid(sticky="w", row=current_row, column=3)
    current_row +=1 

    squiggle_label = ttk.Label(window, justify=CENTER, text="Add squiggle filter", foreground=settings.link_color, cursor="hand2")
    squiggle_label.bind("<Button-1>", lambda e: open_url_in_browser("https://vpype.readthedocs.io/en/latest/reference.html#squiggles"))
    squiggle_label.grid(row=current_row, column=0)
    squiggle = IntVar(window, value=0)
    ttk.Checkbutton(window, text="squiggle", variable=squiggle).grid(sticky="w", row=current_row, column=1)

    ttk.Label(window, justify=CENTER, text="Amplitude of squiggle (in):").grid(row=current_row, column=2)
    squiggle_amplitude_entry = ttk.Entry(window, width=7)
    squiggle_amplitude_entry.insert(0, "0.0196")
    squiggle_amplitude_entry.grid(sticky="w", row=current_row, column=3)
    current_row +=1 

    ttk.Label(window, justify=CENTER, text="Period of squiggle (in):").grid(row=current_row, column=2)
    squiggle_period_entry = ttk.Entry(window, width=7)
    squiggle_period_entry.insert(0, "0.1181")
    squiggle_period_entry.grid(sticky="w", row=current_row, column=3)
    current_row +=1 

    multipass_label = ttk.Label(window, justify=CENTER, text="Add multiple passes to all lines", foreground=settings.link_color, cursor="hand2")
    multipass_label.bind("<Button-1>", lambda e: open_url_in_browser("https://vpype.readthedocs.io/en/latest/reference.html#multipass"))
    multipass_label.grid(row=current_row, column=0)
    multipass = IntVar(window, value=0)
    ttk.Checkbutton(window, text="multipass", variable=multipass).grid(sticky="w", row=current_row, column=1)

    current_row += 1

    ttk.Separator(window, orient='horizontal').grid(sticky="we", row=current_row, column=0, columnspan=4, pady=10)
    current_row += 1

    layout_label = ttk.Label(window, justify=CENTER, text="Layout centers scaled\ndesign in page size)", foreground=settings.link_color, cursor="hand2")
    layout_label.bind("<Button-1>", lambda e: open_url_in_browser("https://vpype.readthedocs.io/en/latest/reference.html#layout"))
    layout_label.grid(row=current_row, column=0)
    layout = IntVar(window, value=1)
    ttk.Checkbutton(window, text="Layout?", variable=layout).grid(sticky="w", row=current_row, column=1)

    ttk.Label(window, justify=CENTER, text="Page Layout Width(in):").grid(row=current_row, column=2)
    layout_width_entry = ttk.Entry(window, width=7)
    layout_width_entry.insert(0, f"0")
    layout_width_entry.grid(sticky="w", row=current_row, column=3)
    current_row +=1 

    ttk.Label(window, justify=CENTER, text="Page Layout Height(in):").grid(row=current_row, column=2)
    layout_height_entry = ttk.Entry(window, width=7)
    layout_height_entry.insert(0, f"0")
    layout_height_entry.grid(sticky="w", row=current_row, column=3)

    page_size_values=["Letter", "A4", "11x17 in", "A3", "17x23 in", "A2"]
    current_value_index = find_closest_dimensions(svg_width_inches, svg_height_inches)
    ttk.Label(window, justify=CENTER, text="Page Size").grid(row=current_row, column=0)
    layout_combobox = ttk.Combobox(
        window,
        width=7,
        state="readonly",
        values=page_size_values
    )
    layout_combobox.current(current_value_index)
    layout_combobox.grid(sticky="w", row=current_row, column=1)
    layout_combobox.bind("<<ComboboxSelected>>", layout_selection_changed)
    layout_selection_changed(None)
    current_row +=1

    layout_landscape_label = ttk.Label(window, justify=CENTER, text="By default, the larger layout size is the height,\nLandscape flips the orientation")
    layout_landscape_label.grid(row=current_row, column=0, columnspan=2)
    layout_landscape = IntVar(window, value=1)
    ttk.Checkbutton(window, text="Landscape", variable=layout_landscape).grid(sticky="w", row=current_row, column=2)

    crop_to_page_size = IntVar(window, value=1)
    ttk.Checkbutton(window, text="Crop to\nPage Size", variable=crop_to_page_size).grid(sticky="w", row=current_row, column=3)
    current_row +=1 

    ttk.Separator(window, orient='horizontal').grid(sticky="we", row=current_row, column=0, columnspan=4, pady=10)
    current_row += 1

    ttk.Button(window, text="Show Output", command=show_vpypeline).grid(pady=(0,10), row=current_row, column=2)
    if len(input_files)>1:
        ttk.Button(window, text="Apply to All", command=run_vpypeline).grid(pady=(0,10), row=current_row, column=3)
    else:
        ttk.Button(window, text="Confirm", command=run_vpypeline).grid(pady=(0,10), row=current_row, column=3)

    window.protocol("WM_DELETE_WINDOW", lambda arg=window: on_closing(arg))

    settings.set_theme(window)
    window.mainloop()

    return tuple(return_val)

if __name__ == "__main__":
    settings.init()
    main()