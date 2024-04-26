import subprocess, os
from tkinter import *
from tkinter import ttk
from utils import *
import Paint, Process
import sv_ttk

def main():
    def on_closing():
        main_app.destroy()

    def run_process():
        processed_files = Process.main(input_files)
        Process.window.destroy()
        if len(processed_files) == 0:
            print("Files unchanged from Process")
        else:
            select_files(processed_files)

    def run_paint():
        painted_files = Paint.main(input_files)
        Paint.window.destroy()
        if len(painted_files) == 0:
            print("Files unchanged from Paint")
        else:
            select_files(painted_files)

    def select_files(files=()):
        global input_files, file_info_text
        if len(files) == 0:
            input_files = get_files() #prompt user to select files
        else:
            input_files = files
        print("main app: ", input_files)
        svg_width_inches, svg_height_inches = get_svg_width_height(input_files[0])
        max_num_colors = max_colors_per_file(input_files)
        file_info_text.set(f"{len(input_files)} file(s) selected, Input file Width(in): {svg_width_inches}, Height(in): {svg_height_inches}, Max colors in file(s): {max_num_colors}")

    #tk widgets and window
    current_row = 0 #helper row var

    main_app = Tk()

    global file_info_text
    file_info_text = StringVar(main_app)
    ttk.Label(main_app, textvariable= file_info_text).grid(pady=(10,0), row=current_row, column=0, columnspan=2)
    current_row += 1

    select_files()

    ttk.Button(main_app, text="Process", command=run_process).grid(row=current_row, column=0)
    ttk.Button(main_app, text="Paint", command=run_paint).grid(row=current_row, column=1)
    current_row += 1

    ttk.Button(main_app, text="Re-Select Files", command=select_files).grid(row=current_row, column=0)
    current_row += 1

    main_app.protocol("WM_DELETE_WINDOW", on_closing)

    sv_ttk.set_theme("dark")
    main_app.mainloop()

    #find ways to make common functions for TK interface shit


if __name__ == "__main__":
    main()