"""Commonly reused helper functions for simplifying GUI building"""
from tkinter import ttk
from typing import Any


def separator(parent: Any, r: int, span: int) -> int:
    """Pre and Post increments the row, creates a separator, returns row"""
    r += 1
    ttk.Separator(parent, orient='horizontal').grid(
        sticky="we", row=r, column=0, columnspan=span, pady=10)
    r += 1
    return r
