"""Main app gets files, launches apps, and passes files between apps"""
from tkinter import Tk
from tkinter import ttk
from utils import select_files, file_info, on_closing, open_url_in_browser
import occult
import paint
import process
import compose
import de_compose
import settings
from gui_helpers import set_title_icon, make_topmost_temp, disable_combobox_scroll
from settings import THEME_SETTINGS
from links import VPYPE_URLS, PPP_URLS

version = "1.1.2"

def main():
    """Creates Tk gui for launching apps"""
    def verify_output_files(files, util_name):
        if len(files) == 0:
            print(f"Files unchanged from {util_name}")
        else:
            select_files(files)

        make_topmost_temp(main_app)

    def run_occult():
        main_app.wm_state("icon")
        returned_files = occult.main(file_info["files"])
        occult.window.destroy()
        verify_output_files(returned_files, "Occult")

    def run_process():
        main_app.wm_state("icon")
        returned_files = process.main(file_info["files"])
        process.window.destroy()
        verify_output_files(returned_files, "Process")

    def run_paint():
        main_app.wm_state("icon")
        returned_files = paint.main(file_info["files"])
        paint.window.destroy()
        verify_output_files(returned_files, "Paint")

    def run_compose():
        main_app.wm_state("icon")
        returned_files = compose.main(file_info["files"])
        compose.window.destroy()
        verify_output_files(returned_files, "Compose")

    def run_decompose():
        main_app.wm_state("icon")
        returned_files = de_compose.main(file_info["files"])
        de_compose.window.destroy()
        verify_output_files(returned_files, "deCompose")

    # tk widgets and window
    current_row = 0  # helper row var
    max_col = 3

    main_app = Tk()

    disable_combobox_scroll(main_app)

    set_title_icon(main_app, f"Plotter Post Processing v{version}")

    print("\n", f"Plotter Post Processing v{version}", "\n")

    current_row += 1

    if len(select_files()) == 0:
        print("No files selected, quitting Plotter Post Processing")
        return

    ttk.Button(main_app, text="Occult", command=run_occult
               ).grid(padx=(10,10), pady=(10, 2), row=current_row, column=0)
    ttk.Button(main_app, text="Process", command=run_process
               ).grid(padx=(10,10), pady=(10, 2), row=current_row, column=1)
    ttk.Button(main_app, text="Paint", command=run_paint
               ).grid(padx=(10,10), pady=(10, 2), row=current_row, column=2)
    current_row += 1
    ttk.Button(main_app, text="Compose", command=run_compose
               ).grid(padx=(10,10), pady=(2, 2), row=current_row, column=0)
    ttk.Button(main_app, text="deCompose", command=run_decompose
               ).grid(padx=(10,10), pady=(2, 2), row=current_row, column=1)

    current_row += 1

    ttk.Button(main_app, text="Re-Select Files", command=select_files
               ).grid(padx=(10,10), pady=(2, 10), row=current_row, column=0)
    ttk.Label(
        main_app,
        text="""By default, output files from one utility are taken as
        the new input files. Reselect files if necessary."""
    ).grid(padx=(10,10), pady=(2, 10), row=current_row, column=1, columnspan=2)
    current_row += 1

    documentation_label = ttk.Label(main_app, text="Vpype Documentation",
                      foreground=THEME_SETTINGS["link_color"], cursor="hand2")
    documentation_label.bind("<Button-1>", lambda e: open_url_in_browser(
        VPYPE_URLS["vpype"]))
    documentation_label.grid(pady=(0,10), padx=(10, 0), sticky="w", row=current_row, column=0, columnspan=max_col)

    current_row += 1

    youtube_label = ttk.Label(main_app, text="Plotter Post Processing Tutorials",
                      foreground=THEME_SETTINGS["link_color"], cursor="hand2")
    youtube_label.bind("<Button-1>", lambda e: open_url_in_browser(
        PPP_URLS["playlist"]))
    youtube_label.grid(pady=(0,10), padx=(10, 0), sticky="w", row=current_row, column=0, columnspan=max_col)

    main_app.protocol("WM_DELETE_WINDOW", lambda arg=main_app: on_closing(arg))

    settings.set_theme(main_app)
    main_app.mainloop()


if __name__ == "__main__":
    settings.init()
    main()
