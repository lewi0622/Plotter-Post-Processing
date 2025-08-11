"""Functions for stored graphical settings"""
import sys
try:
    import sv_ttk
except ImportError:
    pass

if "sv_ttk" in sys.modules:
    THEME: str = "dark"
else:
    THEME = ""

THEME_SETTINGS = { #default theme settings
    "theme": THEME,
    "link_color": "blue"
}

def init() -> None:
    """Initialization of theme settings for Tk Interface"""
    if THEME == "dark":
        THEME_SETTINGS["link_color"] = "#14AEEA"


def set_theme(root) -> None:
    """Applies theme to ttk"""
    if THEME != "":
        sv_ttk.set_theme(THEME, root)
