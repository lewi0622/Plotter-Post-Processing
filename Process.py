import subprocess, os
from tkinter import *
from tkinter import ttk
from utils import *
import settings


def main(input_files=()):
    def on_closing(): #clean up any temp files hanging around
        delete_temp_file(show_temp_file)
        print("Closing Process")
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
        """Runs given commands on first file, but only shows the output."""
        global last_shown_command

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
        output_file_list = []
        for filename in input_file_list:
            file_parts = os.path.splitext(filename)
            show_temp_file = file_parts[0] + "_show_temp_file.svg"
            output_filename = file_parts[0] + "_PROCESSED.svg"
            output_file_list.append(output_filename)

        args = r"vpype "

        # determine if grid is necessary
        cols = grid_col_entry.get()
        rows = grid_row_entry.get()
        width = grid_col_width_entry.get()
        height = grid_row_height_entry.get()

        cols = int(cols)
        rows = int(rows)
        col_size = float(width)
        row_size = float(height)

        slots = cols * rows
        grid = slots > 1

        # Declare globals before the block operator (grid or repeat)
        if grid:
            while len(input_file_list) < slots: #crude way to make sure there's enough files per grid slot
                input_file_list = input_file_list + input_file_list
                output_file_list = output_file_list + output_file_list

            args += r' eval "%grid_layer_count=1%" '

        args += r' eval "files_in=' + f"{input_file_list}" + '"'
        args += r' eval "files_out=' + f"{output_file_list}" + '"'

        #block operator grid or repeat
        if grid:
            args += f" grid -o {col_size}in {row_size}in {cols} {rows} "
        else: #repeat for both single and batch operations
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

        if center_geometries.get():
            args += f" layout {svg_width_inches}x{svg_height_inches}in "

        crop_x_end = float(crop_x_end_entry.get())
        crop_y_end = float(crop_y_end_entry.get())
        if crop_x_end > 0 or crop_y_end > 0:
            args += f" crop 0 0 {crop_x_end_entry.get()}in {crop_y_end_entry.get()}in "

        if rotate_entry.get() != 0:
            args += f" rotate {rotate_entry.get()} "

        if linemerge.get():
            args += f" linemerge "
            if linemerge_tolerance_entry.get() != "0.0019685":
                args += f" -t {linemerge_tolerance_entry.get()} "

        if linesort.get():
            args += r" linesort "

        if reloop.get():
            args += r" reloop "  

        if linesimplify.get():
            args += f" linesimplify "
            if linesimplify_tolerance_entry.get() != "0.0019685":
                args += f" -t {linesimplify_tolerance_entry.get()} "

        if squiggle.get():
            args += f" squiggles "
            if squiggle_amplitude_entry.get() != "0.019685":
                args += f" -a {squiggle_amplitude_entry.get()} "
            if squiggle_period_entry.get() != "0.11811":
                args += f" -p {squiggle_period_entry.get()} "

        if multipass.get():
            args += f" multipass "

        if grid: 
            args += r' forlayer '
            args += r' lmove %_lid% %grid_layer_count% ' #moves each layer onto it's own unique layer so there's no merging
            args += r' eval "%grid_layer_count=grid_layer_count+1%" end end' #inc the global layer counter
        
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
            if not grid:
                args += r" end "
            args += f' write "{show_temp_file}" show '

            return args
        else:
            if grid:
                args += r' write %files_out[0]% '
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
        elif selection == "A3":
            layout_width_entry.insert(0,"11.7")
            layout_height_entry.insert(0,"16.5")
        elif selection == "A2":
            layout_width_entry.insert(0,"16.5")
            layout_height_entry.insert(0,"23.4")
            layout.set(0)

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

    grid_label = ttk.Label(window, justify=CENTER, text="Merge Multiple SVGs into Grid", foreground=settings.link_color, cursor="hand2")
    grid_label.bind("<Button-1>", lambda e: open_url_in_browser("https://vpype.readthedocs.io/en/latest/cookbook.html#faq-merge-to-grid"))
    grid_label.grid(row=current_row, column=0, columnspan=4)
    # ttk.Label(window, justify=CENTER, text="Color Options:").grid(row=current_row, column=1)
    # grid_color_options_combobox = ttk.Combobox(
    #     width=20,
    #     state="readonly",
    #     values=["Keep Original Colors", "Different Color Per File", "All One Color"]
    # )
    # grid_color_options_combobox.current(0)
    # grid_color_options_combobox.grid(sticky="w", row=current_row, column=2, columnspan=2)
    current_row += 1

    ttk.Label(window, justify=CENTER, text="Grid Col Width(in):").grid(row=current_row, column=0)
    grid_col_width_entry = ttk.Entry(window, width=7)
    grid_col_width_entry.grid(sticky="w", row=current_row, column=1)

    ttk.Label(window, justify=CENTER, text="Grid Row Height(in):").grid(row=current_row, column=2)
    grid_row_height_entry = ttk.Entry(window, width=7)
    grid_row_height_entry.grid(sticky="w", row=current_row, column=3)
    current_row += 1 

    ttk.Label(window, justify=CENTER, text="Grid Columns:").grid(row=current_row, column=0)
    grid_col_entry = ttk.Entry(window, width=7)
    grid_col_entry.grid(sticky="w", row=current_row, column=1)

    ttk.Label(window, justify=CENTER, text="Grid Rows:").grid(row=current_row, column=2)
    grid_row_entry = ttk.Entry(window, width=7)
    grid_row_entry.grid(sticky="w", row=current_row, column=3)
    current_row += 1 

    # insert after creation of the size entries so
    grid_col_width_entry.insert(0,f"{svg_width_inches}")
    grid_row_height_entry.insert(0,f"{svg_height_inches}")
    grid_col_entry.insert(0, "1")
    grid_row_entry.insert(0, "1")

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

    center_geometries = IntVar(window, value=1)
    ttk.Checkbutton(window, text="Center Geometries to Input File Size", variable=center_geometries).grid(row=current_row, column=0, columnspan=2)

    crop_label = ttk.Label(window, justify=CENTER, text="Crop X (in):", foreground=settings.link_color, cursor="hand2")
    crop_label.bind("<Button-1>", lambda e: open_url_in_browser("https://vpype.readthedocs.io/en/stable/reference.html#crop"))
    crop_label.grid(row=current_row, column=2)
    crop_x_end_entry = ttk.Entry(window, width=7)
    crop_x_end_entry.insert(0, str(0))
    crop_x_end_entry.grid(sticky="w", row=current_row, column=3)
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

    ttk.Label(window, justify=CENTER, text="Crop Y (in):").grid(row=current_row, column=2)
    crop_y_end_entry = ttk.Entry(window, width=7)
    crop_y_end_entry.insert(0, str(0))
    crop_y_end_entry.grid(sticky="w", row=current_row, column=3)
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
    layout_width_entry.insert(0,f"8.5")
    layout_width_entry.grid(sticky="w", row=current_row, column=3)
    current_row +=1 

    ttk.Label(window, justify=CENTER, text="Page Size").grid(row=current_row, column=0)
    layout_combobox = ttk.Combobox(
        window,
        width=7,
        state="readonly",
        values=["Letter", "A4", "A3", "A2"]
    )
    layout_combobox.current(0)
    layout_combobox.grid(sticky="w", row=current_row, column=1)
    layout_combobox.bind("<<ComboboxSelected>>", layout_selection_changed)

    ttk.Label(window, justify=CENTER, text="Page Layout Height(in):").grid(row=current_row, column=2)
    layout_height_entry = ttk.Entry(window, width=7)
    layout_height_entry.insert(0,f"11")
    layout_height_entry.grid(sticky="w", row=current_row, column=3)
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

    window.protocol("WM_DELETE_WINDOW", on_closing)

    settings.set_theme(window)
    window.mainloop()

    return tuple(return_val)

if __name__ == "__main__":
    settings.init()
    main()