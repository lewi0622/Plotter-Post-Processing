"""Functions for stored graphical settings"""

import sys
import tomllib
from typing import Any

try:
    import sv_ttk
except ImportError:
    pass

if "sv_ttk" in sys.modules:
    THEME: str = "dark"
else:
    THEME = ""

THEME_SETTINGS = {"theme": THEME, "link_color": "blue"}  # default theme settings


def init() -> None:
    """Initialization of theme settings for Tk Interface"""
    if THEME == "dark":
        THEME_SETTINGS["link_color"] = "#14AEEA"


def set_theme(root: Any) -> None:
    """Applies theme to ttk"""
    if THEME != "":
        sv_ttk.set_theme(THEME, root)


with open("pyproject.toml", "rb") as f:
    pyproject_data = tomllib.load(f)
    VERSION = pyproject_data.get("project", {}).get("version", "")

GLOBAL_DEFAULTS: dict[str, Any] = {}
COMPOSE_DEFAULTS: dict[str, Any] = {}
DECOMPOSE_DEFAULTS: dict[str, Any] = {}
MAIN_APPLICATION_DEFAULTS: dict[str, Any] = {}
OCCULT_DEFAULTS: dict[str, Any] = {}
PAINT_DEFAULTS: dict[str, Any] = {}
PROCESS_DEFAULTS: dict[str, Any] = {}

with open("defaults.toml", "rb") as f:
    settings_data = tomllib.load(f)
    GLOBAL_DEFAULTS = settings_data.get("global", {})
    COMPOSE_DEFAULTS = settings_data.get("compose", {})
    DECOMPOSE_DEFAULTS = settings_data.get("decompose", {})
    MAIN_APPLICATION_DEFAULTS = settings_data.get("main_application", {})
    OCCULT_DEFAULTS = settings_data.get("occult", {})
    PAINT_DEFAULTS = settings_data.get("paint", {})
    PROCESS_DEFAULTS = settings_data.get("process", {})
