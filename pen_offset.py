"""Translate SVG layers to compensate for differences in pen barrel diameters."""

import math
import os
from posixpath import join
from tkinter import Frame, IntVar, StringVar, Tk, messagebox, ttk
from typing import Any

from gui_helpers import (
    create_scrollbar,
    create_url_label,
    disable_combobox_scroll,
    make_topmost_temp,
    separator,
    set_title_icon,
)
from links import VPYPE_URLS
from settings import PEN_OFFSET_DEFAULTS, init, set_theme
from utils import check_make_temp_folder, file_info, on_closing, thread_vpypelines


def parse_diameter(value: str, label: str) -> float:
    """Parse and validate a positive pen diameter in inches."""
    try:
        diameter = float(value)
    except ValueError as error:
        raise ValueError(f"{label} must be a number in inches.") from error

    if not math.isfinite(diameter) or diameter <= 0:
        raise ValueError(f"{label} must be a positive, finite number in inches.")

    return diameter


def build_vpype_command(
    input_file: str,
    output_file: str,
    parse_args: str,
    nominal_diameter: float,
    layer_diameters: dict[int, float],
    crop_to_page: bool,
    page_width: float,
    page_height: float,
) -> str:
    """Build a Vpype command translating each layer for its assigned pen."""
    nominal_diameter = parse_diameter(str(nominal_diameter), "Nominal diameter")
    command = f'vpype read {parse_args} --no-crop "{input_file}" '

    for layer_number, layer_diameter in layer_diameters.items():
        layer_diameter = parse_diameter(
            str(layer_diameter), f"Layer {layer_number} diameter"
        )
        translation = (nominal_diameter - layer_diameter) / 2
        if translation == 0:
            continue

        offset = format(round(translation, 3), ".12g")
        command += f"translate -l {layer_number} -- {offset}in {offset}in "

    if crop_to_page:
        command += f"crop 0in 0in {page_width}in {page_height}in "

    return command + f'write "{output_file}"'


def main(input_files: tuple = ()) -> tuple:
    """Create the pen-offset UI and preview or apply translations to SVG files."""
    global return_val, window
    return_val = ()
    input_files = tuple(input_files)
    window = Tk()
    disable_combobox_scroll(window)
    content = ttk.Frame(window, padding=(12, 0, 0, 0))
    content.grid(row=0, column=0, sticky="nsew")
    set_title_icon(window, "Pen Offset")

    pen_diameters: dict[str, str] = PEN_OFFSET_DEFAULTS["pens"]
    pen_names = list(pen_diameters)
    default_pen = PEN_OFFSET_DEFAULTS["nominal_pen"]
    layer_controls: list[dict[str, Any]] = []
    current_row = 0

    ttk.Label(content, text="Pen Offset").grid(
        pady=(10, 0), row=current_row, column=0, columnspan=5
    )
    current_row += 1
    instruction_frame = ttk.Frame(content)
    instruction_frame.grid(row=current_row, column=0, columnspan=5)
    create_url_label(instruction_frame, "Translate", VPYPE_URLS["translate"]).grid(
        row=0, column=0, padx=(0, 4)
    )
    ttk.Label(
        instruction_frame,
        text="each layer by (P0 - P1) / 2 inches on both axes.",
    ).grid(row=0, column=1)
    current_row += 1

    ttk.Label(content, text="Input parsing:").grid(
        row=current_row, column=0, sticky="e"
    )
    parse_entry = ttk.Entry(content, width=20)
    parse_entry.insert(0, PEN_OFFSET_DEFAULTS["default_parse"])
    parse_entry.grid(row=current_row, column=1, sticky="w", padx=4)
    crop_to_page = IntVar(window, value=PEN_OFFSET_DEFAULTS["crop_to_page"])
    current_row += 1

    nominal_frame = ttk.Frame(content)
    nominal_frame.grid(row=current_row, column=0, columnspan=5, sticky="w")
    ttk.Label(nominal_frame, text="Nominal pen (P0):").grid(row=0, column=0)
    nominal_combo = ttk.Combobox(
        nominal_frame, state="readonly", values=pen_names, width=24
    )
    nominal_combo.set(default_pen)
    nominal_combo.grid(row=0, column=1, padx=(4, 8))
    ttk.Label(nominal_frame, text="Diameter (in):").grid(row=0, column=2)
    nominal_diameter_entry = ttk.Entry(nominal_frame, width=10)
    nominal_diameter_entry.insert(0, pen_diameters[default_pen])
    nominal_diameter_entry.grid(row=0, column=3, padx=(4, 0))

    def update_diameter(combo: ttk.Combobox, entry: ttk.Entry) -> None:
        """Fill a diameter field when its pen selection changes."""
        selected_pen = combo.get()
        if selected_pen in pen_diameters:
            entry.delete(0, "end")
            entry.insert(0, pen_diameters[selected_pen])

    nominal_combo.bind(
        "<<ComboboxSelected>>",
        lambda event: update_diameter(event.widget, nominal_diameter_entry),
    )
    current_row += 1

    current_row = separator(content, current_row, 5)

    ttk.Label(content, text="Assign pen to checked layers:").grid(
        row=current_row, column=0, sticky="e"
    )
    batch_combo = ttk.Combobox(content, state="readonly", values=pen_names, width=24)
    batch_combo.set(default_pen)
    batch_combo.grid(row=current_row, column=1, sticky="w", padx=4)
    ttk.Label(content, text="Diameter (in):").grid(
        row=current_row, column=2, sticky="e"
    )
    batch_diameter_entry = ttk.Entry(content, width=10)
    batch_diameter_entry.insert(0, pen_diameters[default_pen])
    batch_diameter_entry.grid(row=current_row, column=3, sticky="w", padx=4)

    def assign_checked_layers() -> None:
        """Assign the selected batch pen and diameter to checked layers."""
        try:
            diameter = parse_diameter(batch_diameter_entry.get(), "Batch diameter")
        except ValueError as error:
            messagebox.showerror("Invalid diameter", str(error), parent=window)
            return

        for control in layer_controls:
            if control["selected"].get():
                control["pen"].set(batch_combo.get())
                control["diameter"].delete(0, "end")
                control["diameter"].insert(0, str(diameter))

    batch_combo.bind(
        "<<ComboboxSelected>>",
        lambda event: update_diameter(event.widget, batch_diameter_entry),
    )
    ttk.Button(content, text="Assign", command=assign_checked_layers).grid(
        row=current_row, column=4, padx=4
    )
    current_row += 1
    current_row = separator(content, current_row, 5)

    headers = ttk.Frame(content)
    headers.grid(row=current_row, column=0, columnspan=5, sticky="w")
    column_count = 5
    for column, heading in enumerate(
        ("Select", "Layer", "Color", "Pen", "Diameter (in)")
    ):
        ttk.Label(headers, text=heading).grid(
            row=0, column=column, padx=(8 if column == 0 else 4, 4)
        )
    current_row += 1

    total_layer_count = sum(
        max(1, len(file_info["color_dicts"][file_index]))
        for file_index in range(len(input_files))
    )
    visible_layer_count = max(1, min(5, total_layer_count))
    visible_height = visible_layer_count * 32 + min(len(input_files), 5) * 24
    layer_frame = create_scrollbar(content, row=current_row, span=5)
    layer_frame.master.configure(height=visible_height)
    layer_row = 0
    for file_index, input_file in enumerate(input_files):
        basename = os.path.basename(input_file)
        ttk.Label(layer_frame, text=basename).grid(
            row=layer_row, column=0, columnspan=5, sticky="w", pady=(6, 2)
        )
        layer_row += 1

        colors = list(file_info["color_dicts"][file_index])
        if not colors:
            colors = ["#ffffff"]

        for layer_number, color in enumerate(colors, start=1):
            selected = IntVar(window, value=0)
            ttk.Checkbutton(layer_frame, variable=selected).grid(
                row=layer_row, column=0, sticky="e", padx=(8, 4)
            )
            ttk.Label(layer_frame, text=f"Layer {layer_number}").grid(
                row=layer_row, column=1, sticky="w", padx=4
            )
            swatch_border = Frame(layer_frame, background="white", padx=1, pady=1)
            swatch_border.grid(row=layer_row, column=2, sticky="w", padx=4)
            Frame(
                swatch_border,
                background=color,
                width=14,
                height=14,
            ).pack()

            pen_var = StringVar(window, value=default_pen)
            pen_combo = ttk.Combobox(
                layer_frame,
                state="readonly",
                values=pen_names,
                width=24,
                textvariable=pen_var,
            )
            pen_combo.grid(row=layer_row, column=3, sticky="w", padx=4)
            diameter_entry = ttk.Entry(layer_frame, width=10)
            diameter_entry.insert(0, pen_diameters[default_pen])
            diameter_entry.grid(row=layer_row, column=4, sticky="w", padx=4)
            pen_combo.bind(
                "<<ComboboxSelected>>",
                lambda event, entry=diameter_entry: update_diameter(
                    event.widget, entry
                ),
            )

            layer_controls.append(
                {
                    "selected": selected,
                    "pen": pen_var,
                    "diameter": diameter_entry,
                    "file_index": file_index,
                    "layer_number": layer_number,
                }
            )
            layer_row += 1

    def align_layer_columns() -> None:
        """Match header columns to the requested widths of the layer widgets."""
        window.update_idletasks()
        column_widths = [0] * column_count
        for frame in (headers, layer_frame):
            for widget in frame.winfo_children():
                grid_info = widget.grid_info()
                if int(grid_info.get("columnspan", 1)) != 1:
                    continue

                column = int(grid_info["column"])
                padx = grid_info.get("padx", 0)
                if isinstance(padx, tuple):
                    horizontal_padding = sum(int(value) for value in padx)
                else:
                    horizontal_padding = 2 * int(padx)
                column_widths[column] = max(
                    column_widths[column],
                    widget.winfo_reqwidth() + horizontal_padding,
                )

        for column, width in enumerate(column_widths):
            headers.grid_columnconfigure(column, minsize=width, weight=0)
            layer_frame.grid_columnconfigure(column, minsize=width, weight=0)

    window.after_idle(align_layer_columns)

    def select_all_layers() -> None:
        """Check every layer selection box in the scrollable list."""
        for control in layer_controls:
            control["selected"].set(1)

    def deselect_all_layers() -> None:
        """Clear every layer selection box in the scrollable list."""
        for control in layer_controls:
            control["selected"].set(0)

    current_row = separator(content, current_row, 5)
    current_row += 1
    ttk.Button(content, text="Select all", command=select_all_layers).grid(
        row=current_row, column=0, sticky="e", padx=4
    )
    ttk.Button(content, text="Deselect all", command=deselect_all_layers).grid(
        row=current_row, column=1, sticky="w"
    )
    ttk.Checkbutton(content, text="Crop to page size", variable=crop_to_page).grid(
        row=current_row, column=2, columnspan=2, sticky="w"
    )
    current_row += 1
    options_row = current_row

    output_files: list[str] = []
    show_files: list[str] = []

    def build_commands() -> tuple[list[str], list[str]]:
        """Build apply and preview pipelines for every input file."""
        nominal_diameter = parse_diameter(
            nominal_diameter_entry.get(), "Nominal diameter"
        )
        if not parse_entry.get().strip():
            raise ValueError("Input parsing options cannot be blank.")

        output_files.clear()
        show_files.clear()
        commands = []
        show_commands = []

        for file_index, input_file in enumerate(input_files):
            head, tail = os.path.split(input_file)
            name = os.path.splitext(tail)[0]
            output_file = join(head, name + "_T.svg")
            show_file = join(file_info["temp_folder_path"], name + "_T.svg")
            output_files.append(output_file)
            show_files.append(show_file)

            layer_diameters = {
                control["layer_number"]: parse_diameter(
                    control["diameter"].get(),
                    f"{os.path.basename(input_file)} layer "
                    f"{control['layer_number']} diameter",
                )
                for control in layer_controls
                if control["file_index"] == file_index
            }
            page_width, page_height = file_info["size_info"][file_index]
            command = build_vpype_command(
                input_file,
                output_file,
                parse_entry.get().strip(),
                nominal_diameter,
                layer_diameters,
                bool(crop_to_page.get()),
                page_width,
                page_height,
            )
            show_command = build_vpype_command(
                input_file,
                show_file,
                parse_entry.get().strip(),
                nominal_diameter,
                layer_diameters,
                bool(crop_to_page.get()),
                page_width,
                page_height,
            )
            commands.append(command)
            show_commands.append(show_command + " show")

        return commands, show_commands

    def show_vpypeline() -> None:
        """Preview the first selected file using its current pen assignments."""
        try:
            commands, show_commands = build_commands()
        except ValueError as error:
            messagebox.showerror("Invalid pen settings", str(error), parent=window)
            return

        if not input_files:
            messagebox.showerror(
                "No files selected", "Select an SVG file first.", parent=window
            )
            return

        check_make_temp_folder()
        show_info = {
            "index": 0,
            "show_path": show_files[0],
            "output_path": output_files[0],
        }
        thread_vpypelines(commands, show_commands, "Pen Offset", show_info)
        make_topmost_temp(window)

    def run_vpypeline() -> None:
        """Apply pen offsets to all selected files and close the utility."""
        global return_val
        try:
            commands, show_commands = build_commands()
        except ValueError as error:
            messagebox.showerror("Invalid pen settings", str(error), parent=window)
            return

        if not input_files:
            messagebox.showerror(
                "No files selected", "Select an SVG file first.", parent=window
            )
            return

        thread_vpypelines(commands, show_commands, "Pen Offset", {})
        return_val = output_files.copy()
        on_closing(window)

    ttk.Button(content, text="Show", command=show_vpypeline).grid(
        row=options_row + 1, column=1, pady=(8, 10)
    )
    ttk.Button(content, text="Apply", command=run_vpypeline).grid(
        row=options_row + 1, column=2, pady=(8, 10)
    )

    window.protocol("WM_DELETE_WINDOW", lambda: on_closing(window))
    init()
    set_theme(window)
    window.mainloop()
    return return_val


if __name__ == "__main__":
    from utils import select_files

    init()
    selected_files: tuple = select_files()
    if len(selected_files) == 0:
        print("No Design Files Selected")
    else:
        main(input_files=selected_files)
