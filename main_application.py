"""Main app gets files, launches apps, and passes files between apps"""
from tkinter import Tk, StringVar
from tkinter import ttk
from utils import select_files, file_info, on_closing
import occult
import paint
import process
import compose
import de_compose
import settings

def main():
    """Creates Tk gui for launching apps"""
    def verify_output_files(files, util_name):
        if len(files) == 0:
            print(f"Files unchanged from {util_name}")
        else:
            select_files(files)

    def run_occult():
        occulted_files = occult.main(file_info["files"])
        occult.window.destroy()
        verify_output_files(occulted_files, "Occult")

    def run_process():
        processed_files = process.main(file_info["files"])
        process.window.destroy()
        verify_output_files(processed_files, "Process")

    def run_paint():
        painted_files = paint.main(file_info["files"])
        paint.window.destroy()
        verify_output_files(painted_files, "Paint")

    def run_compose():
        painted_files = compose.main(file_info["files"])
        compose.window.destroy()
        verify_output_files(painted_files, "Compose")

    def run_decompose():
        painted_files = de_compose.main(file_info["files"])
        de_compose.window.destroy()
        verify_output_files(painted_files, "deCompose")

    #tk widgets and window
    current_row = 0 #helper row var

    main_app = Tk()

    file_info_text = StringVar(main_app)
    ttk.Label(main_app, textvariable= file_info_text
        ).grid(pady=(10,0), row=current_row, column=0, columnspan=2)
    #TODO add button to launch separate window for file details
    current_row += 1

    select_files()
    file_info_text.set(f"{len(file_info["files"])} file(s) selected")

    ttk.Button(main_app, text="Occult", command=run_occult
        ).grid(pady=(2,2),row=current_row, column=0)
    ttk.Button(main_app, text="Process", command=run_process
        ).grid(pady=(2,2), row=current_row, column=1)
    ttk.Button(main_app, text="Paint", command=run_paint
        ).grid(pady=(2,2), row=current_row, column=2)
    current_row += 1
    ttk.Button(main_app, text="Compose", command=run_compose
        ).grid(pady=(2,2), row=current_row, column=0)
    ttk.Button(main_app, text="deCompose", command=run_decompose
        ).grid(pady=(2,2), row=current_row, column=1)

    current_row += 1

    ttk.Button(main_app, text="Re-Select Files", command=select_files
        ).grid(pady=(0,10), row=current_row, column=0)
    ttk.Label(
        main_app,
        text="""By default, output files from one utility are taken as
        the new input files. Reselect files if necessary."""
        ).grid(pady=(0,10), row=current_row, column=1, columnspan=2)
    current_row += 1

    main_app.protocol("WM_DELETE_WINDOW", lambda arg=main_app: on_closing(arg))

    settings.set_theme(main_app)
    main_app.mainloop()


if __name__ == "__main__":
    settings.init()
    main()
