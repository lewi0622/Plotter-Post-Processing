import subprocess, os
from tkinter import *
from tkinter import ttk
from utils import *
import Paint, Process

def main():
    def on_closing():
        main_app.destroy()

    def run_process():
        Process.main()


    def run_paint():
        Paint.main()

    #tk widgets and window
    current_row = 0 #helper row var, inc-ed every time used;

    main_app = Tk()
    Button(main_app, text="Process", command=run_process).grid(row=current_row, column=0)
    Button(main_app, text="Paint", command=run_paint).grid(row=current_row, column=1)

    main_app.protocol("WM_DELETE_WINDOW", on_closing)
    main_app.mainloop()
    #create tk interface with big buttons for launching Process and Paint
    #find ways to make common functions for TK interface shit


if __name__ == "__main__":
    main()