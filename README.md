# Plotter-Post-Processing
GUI wrapper around Vpype for my most used recipes for processing SVGs before plotting them. In most cases, the SVGs I'm processing come from [p5.js-svg](https://github.com/zenozeng/p5.js-svg).

This is my personal approach to post processing my svg plotter files. This is not meant to be a one-size-fits-all tool, nor a complete GUI-fication of [Vpype](https://github.com/abey79/vpype).

## Installation
To install, follow the directions provided in my [video](https://www.youtube.com/watch?v=9a-bJFNydFQ&list=PL9Kq-2ltl3B4Dl3438KB67FPoJSAxnbli&index=3)

## Apps and Features:
For an overview of the features and how to use the tool, view my [playlist on youtube](https://www.youtube.com/playlist?list=PL9Kq-2ltl3B4Dl3438KB67FPoJSAxnbli)
- Process
    - Crop, Scale, Rotate, Center, Optimize
- Occult (requires [Occult plugin](https://github.com/LoicGoulefert/occult) to be injected)
    - Remove hidden lines or apply cutout shapes
- Compose
    - Stack multiple designs or lay them out in a grid
- Decompose
    - Break up designs into separate layers
    - Save layers to separate files or delete certain layers
- Paint
    - Insert dips into design at specified intervals
    - Specify dip locations and patterns
- File handling
    - Batch up the same Vpype operations on an arbitrary number of files
    - Automatically pass the files from one operation to the next

## Issues
If you have an issue or feature request, feel free to submit it. I will choose to fulfill feature requests if they are useful to me. Pull requests are always welcome.

## Dependencies
All of these utilities require [Vpype](https://github.com/abey79/vpype), and some of it's plug-ins, to be installed. I do not provide an installer.
Last tested using on:
- Windows 11 
- Python Version 3.13.10
- lxml Version 6.0.2
- Pipx Version 1.8.0
- Vpype Version 1.15.0
- Occult Version 0.4.0
- Optional:
    - sv_ttk 2.6.1 for prettier UIs

