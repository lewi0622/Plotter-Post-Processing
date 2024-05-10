from tkinter import *
from tkinter import ttk
from utils import *
import Occult, Paint, Process, Compose, deCompose, settings

def main():
    def on_closing():
        main_app.destroy()
        print("HERE")
        try:
            Occult.on_closing()
        except:
            pass
        try:
            Process.on_closing()
        except:
            pass
        try:
            Paint.on_closing()
        except:
            pass
        try:
            deCompose.on_closing()
        except:
            pass
        try:
            Compose.on_closing()
        except:
            pass

    def verify_output_files(files, util_name):
        if len(files) == 0:
            print(f"Files unchanged from {util_name}")
        else:
            select_files(files)

    def run_occult():
        occulted_files = Occult.main(input_files)
        Occult.window.destroy()
        verify_output_files(occulted_files, "Occult")

    def run_process():
        processed_files = Process.main(input_files)
        Process.window.destroy()
        verify_output_files(processed_files, "Process")

    def run_paint():
        painted_files = Paint.main(input_files)
        Paint.window.destroy()
        verify_output_files(painted_files, "Paint")

    def run_compose():
        painted_files = Compose.main(input_files)
        Compose.window.destroy()
        verify_output_files(painted_files, "Compose")

    def run_deCompose():
        painted_files = deCompose.main(input_files)
        deCompose.window.destroy()
        verify_output_files(painted_files, "deCompose")

    def select_files(files=()):
        global input_files, file_info_text
        if len(files) == 0:
            recieved_files = get_files() #prompt user to select files
            if len(recieved_files) > 0:
                input_files = recieved_files
        else:
            input_files = files
        print("Currently Loaded Files: ", input_files)
        svg_width_inches, svg_height_inches = get_svg_width_height(input_files[0])
        max_num_colors = max_colors_per_file(input_files)
        file_info_text.set(f"{len(input_files)} file(s) selected, Input file Width(in): {svg_width_inches}, Height(in): {svg_height_inches}, Max colors in file(s): {max_num_colors}")

    #tk widgets and window
    current_row = 0 #helper row var

    main_app = Tk()

    global file_info_text
    file_info_text = StringVar(main_app)
    ttk.Label(main_app, textvariable= file_info_text).grid(pady=(10,0), row=current_row, column=0, columnspan=3)
    current_row += 1

    select_files()

    ttk.Button(main_app, text="Occult", command=run_occult).grid(pady=(2,2), row=current_row, column=0)
    ttk.Button(main_app, text="Process", command=run_process).grid(pady=(2,2), row=current_row, column=1)
    ttk.Button(main_app, text="Paint", command=run_paint).grid(pady=(2,2), row=current_row, column=2)
    current_row += 1
    ttk.Button(main_app, text="Compose", command=run_compose).grid(pady=(2,2), row=current_row, column=0)
    ttk.Button(main_app, text="deCompose", command=run_deCompose).grid(pady=(2,2), row=current_row, column=1)

    current_row += 1

    ttk.Button(main_app, text="Re-Select Files", command=select_files).grid(pady=(0,10), row=current_row, column=0)
    ttk.Label(main_app, text="By default, output files from one utility are taken as\nthe new input files. Reselect files if necessary.").grid(pady=(0,10), row=current_row, column=1, columnspan=2)
    current_row += 1

    main_app.protocol("WM_DELETE_WINDOW", on_closing)

    settings.set_theme(main_app)
    main_app.mainloop()

    #find ways to make common functions for TK interface shit


if __name__ == "__main__":
    settings.init()
    main()