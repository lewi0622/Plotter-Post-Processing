# Plotter-Post-Processing
My personal approach to post processing my svg plotter files. This is not meant to be a complete GUI-fication of Vpype.

## Features:
- Process
    - Crop, Scale, Rotate, Center, Optimize
- Occult
    - Remove hidden lines
- Compose
    - Stack multiple designs or lay them out in a grid
- Decompose
    - Save layers to separate files or delete certain layers
- Paint
    - Break up designs, specify dip locations in between chunks of design
- File handling
    - Batch up the same Vpype operations on an arbitrary number of files
    - Automatically pass the files from one operation to the next

## Issues
If you have an issue or feature request, feel free to submit it. I will choose to fulfill feature requests if they are useful to me. Pull requests are always welcome.

## Dependencies
All of these utilities require [Vpype](https://github.com/abey79/vpype), and some of it's plug-ins, to be installed. I do not provide an installer.
Last tested using 
- Python Version 3.12.10
- Vpype Version 1.14.0
- Occult Version 0.4.0
- Optional:
    - sv_ttk for prettier UIs