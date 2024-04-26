def init():
    global theme, sv_ttk, link_color

    try:
        import sv_ttk
        theme = "dark"
    except ImportError:
        theme = None

    if theme == "dark":
        link_color = "#14AEEA"
    else:
        link_color = "blue"


def set_theme(root):
    if theme != None:
        sv_ttk.set_theme(theme, root)