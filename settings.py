"""Functions for stored graphical settings"""
try:
    import sv_ttk
    THEME = "dark"
except ImportError:
    THEME = None

THEME_SETTINGS = { #default theme settings
    "theme": THEME,
    "link_color": "blue"
}

def init():
    """Initialization of theme settings for Tk Interface"""
    if THEME == "dark":
        THEME_SETTINGS["link_color"] = "#14AEEA"


def set_theme(root):
    """Applies theme to ttk"""
    if THEME is not None:
        sv_ttk.set_theme(THEME, root)
