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
- Clipper
    - Remove hidden lines with Clipper2, or clip paths to a closed masking path
    - Also available as the standalone `ppp-clipper` command-line tool
- Compose
    - Stack multiple designs or lay them out in a grid
- Decompose
    - Break up designs into separate layers
    - Save layers to separate files or delete certain layers
- Paint
    - Insert dips into design at specified intervals
    - Specify dip locations and patterns
- Pen Offset
    - Translate layers to compensate for differences in pen barrel diameters
    - Optionally crop translated geometry to the page boundaries
- File handling
    - Batch up the same Vpype operations on an arbitrary number of files
    - Automatically pass the files from one operation to the next
    - Occult and Clipper print the elapsed time from confirmation until outputs are returned to the main app

## Issues
If you have an issue or feature request, feel free to submit it. I will choose to fulfill feature requests if they are useful to me. Pull requests are always welcome.

## Dependencies
All of these utilities require [Vpype](https://github.com/abey79/vpype), and some of it's plug-ins, to be installed. I do not provide an installer.
Clipper additionally requires [pyclipr](https://pypi.org/project/pyclipr/), which is installed with the project dependencies.
Clipper automatically runs Vpype to flatten and simplify SVGs that contain curves, transforms, or unconverted shapes. This modifies the input SVG in place before clipping; in mask mode, it may also modify the separate mask SVG.
Clipper uses a scale factor of 1,000, so clipping precision is 0.001 SVG user units.

### Clipper command line

The CLI can also be run directly from the project directory with `python clipper.py`:

```text
ppp-clipper hidden-line input.svg output.svg
ppp-clipper mask input.svg output.svg --mask-file mask.svg --outside --exclude-mask
```

Mask mode requires a separate SVG via `--mask-file`. All closed paths in that file are combined as one mask and must use the same coordinate system as the input SVG. The operation keeps the inside and includes the mask geometry in the output by default; `--outside` keeps the outside, and `--exclude-mask` omits the mask geometry.
Hidden-line removal and masking skip Clipper operations when the subject and masking path bounding boxes are disjoint.
When an SVG has a `viewBox`, hidden-line removal clips subjects and closed occluders to that page before testing overlaps; off-page geometry is excluded from the result. Closed paths still define full masks before their filled regions are intersected with the page.
Clipper prints per-file benchmark details to the console, including SVG parsing, geometry and Clipper execution, output rewriting/writing, and bounding-box rejection counts. The GUI also reports output reload time and confirmation-to-return total.
Last tested using on:
- Windows 11 
- Python Version 3.13.10
- lxml Version 6.0.2
- Pipx Version 1.8.0
- Vpype Version 1.15.0
- Occult Version 0.4.0
- Optional:
    - sv_ttk 2.6.1 for prettier UIs
