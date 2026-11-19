#!/usr/bin/env python3
"""
Notepadxx - A full-featured Notepad-like editor with IDE extras
Built with pure Python + Tkinter (no external dependencies)

Features:
- Classic Windows Notepad look & feel with modern enhancements
- Themes (Light / Dark / High Contrast / Classic)
- Line numbers (synced, clickable)
- Word wrap toggle
- Basic syntax highlighting (Python, JSON, HTML/XML, Markdown, C-like)
- File manager / explorer sidebar
- Integrated terminal panel
- Find & Replace
- Go to Line
- Status bar (line/col, encoding, wrap, theme)
- Font selection & zoom
- Undo/Redo, standard editing shortcuts
"""

from __future__ import annotations

import os
import re
import sys
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, font as tkfont, simpledialog
from pathlib import Path
from typing import Optional, Dict, List, Tuple

APP_NAME = "Notepadxx"
VERSION = "1.0.0"
DEFAULT_ENCODING = "utf-8"


# ---------------------------------------------------------------------------
# Themes
# ---------------------------------------------------------------------------
THEMES: Dict[str, Dict[str, str]] = {
    "Light": {
        "bg": "#ffffff",
        "fg": "#000000",
        "insertbg": "#000000",
        "selectbg": "#cce8ff",
        "selectfg": "#000000",
        "linenum_bg": "#f0f0f0",
        "linenum_fg": "#606060",
        "status_bg": "#f0f0f0",
        "status_fg": "#000000",
        "sidebar_bg": "#f5f5f5",
        "terminal_bg": "#1e1e1e",
        "terminal_fg": "#d4d4d4",
        "menu_bg": "#f0f0f0",
        "highlight_current": "#e8f4ff",
        "keyword": "#0000ff",
        "string": "#a31515",
        "comment": "#008000",
        "number": "#098658",
        "builtin": "#267f99",
    },
    "Dark": {
        "bg": "#1e1e1e",
        "fg": "#d4d4d4",
        "insertbg": "#aeafad",
        "selectbg": "#264f78",
        "selectfg": "#ffffff",
        "linenum_bg": "#252526",
        "linenum_fg": "#858585",
        "status_bg": "#007acc",
        "status_fg": "#ffffff",
        "sidebar_bg": "#252526",
        "terminal_bg": "#0c0c0c",
        "terminal_fg": "#cccccc",
        "menu_bg": "#2d2d30",
        "highlight_current": "#2a2d2e",
        "keyword": "#569cd6",
        "string": "#ce9178",
        "comment": "#6a9955",
        "number": "#b5cea8",
        "builtin": "#4ec9b0",
    },
    "High Contrast": {
        "bg": "#000000",
        "fg": "#ffffff",
        "insertbg": "#ffffff",
        "selectbg": "#ffff00",
        "selectfg": "#000000",
        "linenum_bg": "#000000",
        "linenum_fg": "#ffff00",
        "status_bg": "#000000",
        "status_fg": "#ffff00",
        "sidebar_bg": "#000000",
        "terminal_bg": "#000000",
        "terminal_fg": "#00ff00",
        "menu_bg": "#000000",
        "highlight_current": "#1a1a00",
        "keyword": "#00ffff",
        "string": "#00ff00",
        "comment": "#ff00ff",
        "number": "#ffff00",
        "builtin": "#ff8800",
    },
    "Classic": {
        "bg": "#ffffff",
        "fg": "#000000",
        "insertbg": "#000000",
        "selectbg": "#000080",
        "selectfg": "#ffffff",
        "linenum_bg": "#c0c0c0",
        "linenum_fg": "#000000",
        "status_bg": "#c0c0c0",
        "status_fg": "#000000",
        "sidebar_bg": "#f0f0f0",
        "terminal_bg": "#000000",
        "terminal_fg": "#c0c0c0",
        "menu_bg": "#f0f0f0",
        "highlight_current": "#e0e0e0",
        "keyword": "#0000ff",
        "string": "#800000",
        "comment": "#008000",
        "number": "#000080",
        "builtin": "#800080",
    },
}


# ---------------------------------------------------------------------------
# Simple syntax highlighters (regex based)
# ---------------------------------------------------------------------------
PYTHON_KEYWORDS = {
    "False", "None", "True", "and", "as", "assert", "async", "await",
    "break", "class", "continue", "def", "del", "elif", "else", "except",
    "finally", "for", "from", "global", "if", "import", "in", "is",
    "lambda", "nonlocal", "not", "or", "pass", "raise", "return",
    "try", "while", "with", "yield",
}
PYTHON_BUILTINS = {
    "abs", "all", "any", "bin", "bool", "bytearray", "bytes", "callable",
    "chr", "classmethod", "compile", "complex", "delattr", "dict", "dir",
    "divmod", "enumerate", "eval", "exec", "filter", "float", "format",
    "frozenset", "getattr", "globals", "hasattr", "hash", "help", "hex",
    "id", "input", "int", "isinstance", "issubclass", "iter", "len",
    "list", "locals", "map", "max", "memoryview", "min", "next", "object",
    "oct", "open", "ord", "pow", "print", "property", "range", "repr",
    "reversed", "round", "set", "setattr", "slice", "sorted", "staticmethod",
    "str", "sum", "super", "tuple", "type", "vars", "zip", "__import__",
}

SYNTAX_PATTERNS: Dict[str, List[Tuple[str, str]]] = {
    "python": [
        (r"#.*?$", "comment"),
        (r'"""[\s\S]*?"""', "string"),
        (r"'''[\s\S]*?'''", "string"),
        (r'"(?:\\.|[^"\\])*"', "string"),
        (r"'(?:\\.|[^'\\])*'", "string"),
        (r"\b\d+\.?\d*\b", "number"),
        (r"\b(" + "|".join(PYTHON_KEYWORDS) + r")\b", "keyword"),
        (r"\b(" + "|".join(PYTHON_BUILTINS) + r")\b", "builtin"),
    ],
    "json": [
        (r'"(?:\\.|[^"\\])*"\s*:', "keyword"),  # keys
        (r'"(?:\\.|[^"\\])*"', "string"),
        (r"\b(true|false|null)\b", "keyword"),
        (r"\b-?\d+\.?\d*([eE][+-]?\d+)?\b", "number"),
    ],
    "html": [
        (r"<!--[\s\S]*?-->", "comment"),
        (r"</?[a-zA-Z][^>]*>", "keyword"),
        (r'"[^"]*"', "string"),
        (r"'[^']*'", "string"),
    ],
    "markdown": [
        (r"^#{1,6}\s.*$", "keyword"),
        (r"`[^`]+`", "string"),
        (r"\*\*[^*]+\*\*", "builtin"),
        (r"\*[^*]+\*", "builtin"),
        (r"\[([^\]]+)\]\([^)]+\)", "string"),
    ],
    "c": [
        (r"//.*?$", "comment"),
        (r"/\*[\s\S]*?\*/", "comment"),
        (r'"(?:\\.|[^"\\])*"', "string"),
        (r"'(?:\\.|[^'\\])*'", "string"),
        (r"\b\d+\.?\d*[fFlL]?\b", "number"),
        (r"\b(auto|break|case|char|const|continue|default|do|double|else|enum|extern|float|for|goto|if|int|long|register|return|short|signed|sizeof|static|struct|switch|typedef|union|unsigned|void|volatile|while)\b", "keyword"),
    ],
}

EXT_TO_LANG = {
    ".py": "python",
    ".pyw": "python",
    ".json": "json",
    ".html": "html",
    ".htm": "html",
    ".xml": "html",
    ".md": "markdown",
    ".markdown": "markdown",
    ".c": "c",
    ".h": "c",
    ".cpp": "c",
    ".hpp": "c",
    ".cc": "c",
}


# ---------------------------------------------------------------------------
# Line Numbers Canvas
# ---------------------------------------------------------------------------
class LineNumbers(tk.Canvas):
    def __init__(self, master, text_widget: tk.Text, **kwargs):
        super().__init__(master, width=48, highlightthickness=0, **kwargs)
        self.text = text_widget
        self.bind("<Button-1>", self._on_click)
        self.text.bind("<KeyRelease>", self._schedule_redraw)
        self.text.bind("<ButtonRelease-1>", self._schedule_redraw)
        self.text.bind("<MouseWheel>", self._schedule_redraw)
        self.text.bind("<Configure>", self._schedule_redraw)
        self.text.bind("<<Modified>>", self._on_modified)
        self._after_id = None

    def _on_modified(self, event=None):
        self.text.edit_modified(False)
        self._schedule_redraw()

    def _schedule_redraw(self, event=None):
        if self._after_id:
            self.after_cancel(self._after_id)
        self._after_id = self.after(10, self.redraw)

    def redraw(self, event=None):
        self.delete("all")
        try:
            first = self.text.index("@0,0")
            last = self.text.index(f"@0,{self.winfo_height()}")
        except tk.TclError:
            return

        i = self.text.index(f"{first} linestart")
        while True:
            dline = self.text.dlineinfo(i)
            if dline is None:
                break
            y = dline[1]
            linenum = str(i).split(".")[0]
            self.create_text(
                40, y, anchor="ne", text=linenum,
                fill=self["fg"] if "fg" in self.keys() else "#858585",
                font=self.text["font"],
            )
            if self.text.compare(i, ">=", last):
                break
            i = self.text.index(f"{i}+1line")

    def _on_click(self, event):
        # Jump cursor to that line
        y = event.y
        index = self.text.index(f"@0,{y}")
        self.text.mark_set("insert", f"{index} linestart")
        self.text.see("insert")
        self.text.focus_set()


# ---------------------------------------------------------------------------
# Main Application
# ---------------------------------------------------------------------------
class Notepadxx(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"Untitled - {APP_NAME}")
        self.geometry("1100x720")
        self.minsize(700, 450)

        # State
        self.current_file: Optional[Path] = None
        self.encoding = DEFAULT_ENCODING
        self.word_wrap = tk.BooleanVar(value=True)
        self.show_line_numbers = tk.BooleanVar(value=True)
        self.show_file_manager = tk.BooleanVar(value=True)
        self.show_terminal = tk.BooleanVar(value=False)
        self.current_theme = tk.StringVar(value="Dark")
        self.font_family = "Consolas"
        self.font_size = 11
        self.syntax_enabled = tk.BooleanVar(value=True)
        self.current_lang: Optional[str] = None

        # Build UI
        self._create_menu()
        self._create_toolbar()
        self._create_main_layout()
        self._create_status_bar()
        self._bind_shortcuts()
        self._apply_theme("Dark")
        self._update_title()
        self._update_status()

        # Initial focus
        self.text.focus_set()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------
    def _create_menu(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        # File
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New", accelerator="Ctrl+N", command=self.new_file)
        file_menu.add_command(label="Open...", accelerator="Ctrl+O", command=self.open_file)
        file_menu.add_command(label="Save", accelerator="Ctrl+S", command=self.save_file)
        file_menu.add_command(label="Save As...", accelerator="Ctrl+Shift+S", command=self.save_as)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", accelerator="Alt+F4", command=self._on_close)

        # Edit
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Undo", accelerator="Ctrl+Z", command=lambda: self.text.event_generate("<<Undo>>"))
        edit_menu.add_command(label="Redo", accelerator="Ctrl+Y", command=lambda: self.text.event_generate("<<Redo>>"))
        edit_menu.add_separator()
        edit_menu.add_command(label="Cut", accelerator="Ctrl+X", command=lambda: self.text.event_generate("<<Cut>>"))
        edit_menu.add_command(label="Copy", accelerator="Ctrl+C", command=lambda: self.text.event_generate("<<Copy>>"))
        edit_menu.add_command(label="Paste", accelerator="Ctrl+V", command=lambda: self.text.event_generate("<<Paste>>"))
        edit_menu.add_command(label="Delete", accelerator="Del", command=lambda: self.text.event_generate("<<Clear>>"))
        edit_menu.add_separator()
        edit_menu.add_command(label="Find...", accelerator="Ctrl+F", command=self.find_dialog)
        edit_menu.add_command(label="Replace...", accelerator="Ctrl+H", command=self.replace_dialog)
        edit_menu.add_command(label="Go to Line...", accelerator="Ctrl+G", command=self.goto_line)
        edit_menu.add_separator()
        edit_menu.add_command(label="Select All", accelerator="Ctrl+A", command=lambda: self.text.event_generate("<<SelectAll>>"))

        # Format
        format_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Format", menu=format_menu)
        format_menu.add_checkbutton(label="Word Wrap", variable=self.word_wrap, command=self._toggle_wrap)
        format_menu.add_command(label="Font...", command=self.choose_font)

        # View
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_checkbutton(label="Line Numbers", variable=self.show_line_numbers, command=self._toggle_line_numbers)
        view_menu.add_checkbutton(label="File Manager", variable=self.show_file_manager, command=self._toggle_file_manager)
        view_menu.add_checkbutton(label="Terminal", variable=self.show_terminal, command=self._toggle_terminal)
        view_menu.add_separator()
        theme_menu = tk.Menu(view_menu, tearoff=0)
        view_menu.add_cascade(label="Theme", menu=theme_menu)
        for name in THEMES:
            theme_menu.add_radiobutton(
                label=name, variable=self.current_theme, value=name,
                command=lambda n=name: self._apply_theme(n)
            )
        view_menu.add_separator()
        view_menu.add_checkbutton(label="Syntax Highlighting", variable=self.syntax_enabled, command=self._rehighlight)
        view_menu.add_command(label="Zoom In", accelerator="Ctrl++", command=self.zoom_in)
        view_menu.add_command(label="Zoom Out", accelerator="Ctrl+-", command=self.zoom_out)
        view_menu.add_command(label="Reset Zoom", accelerator="Ctrl+0", command=self.zoom_reset)

        # Help
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About Notepadxx", command=self.show_about)

    def _create_toolbar(self):
        self.toolbar = ttk.Frame(self, padding=(4, 2))
        self.toolbar.pack(side=tk.TOP, fill=tk.X)

        btn_style = {"width": 4}
        ttk.Button(self.toolbar, text="New", command=self.new_file, width=5).pack(side=tk.LEFT, padx=1)
        ttk.Button(self.toolbar, text="Open", command=self.open_file, width=5).pack(side=tk.LEFT, padx=1)
        ttk.Button(self.toolbar, text="Save", command=self.save_file, width=5).pack(side=tk.LEFT, padx=1)
        ttk.Separator(self.toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=4)
        ttk.Button(self.toolbar, text="Cut", command=lambda: self.text.event_generate("<<Cut>>"), width=4).pack(side=tk.LEFT, padx=1)
        ttk.Button(self.toolbar, text="Copy", command=lambda: self.text.event_generate("<<Copy>>"), width=4).pack(side=tk.LEFT, padx=1)
        ttk.Button(self.toolbar, text="Paste", command=lambda: self.text.event_generate("<<Paste>>"), width=4).pack(side=tk.LEFT, padx=1)
        ttk.Separator(self.toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=4)
        ttk.Button(self.toolbar, text="Find", command=self.find_dialog, width=5).pack(side=tk.LEFT, padx=1)

    def _create_main_layout(self):
        # Main horizontal paned window: File Manager | Editor
        self.main_paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True)

        # ---- File Manager (left) ----
        self.fm_frame = ttk.Frame(self.main_paned, width=220)
        self.main_paned.add(self.fm_frame, weight=0)

        fm_header = ttk.Frame(self.fm_frame)
        fm_header.pack(fill=tk.X, padx=4, pady=2)
        ttk.Label(fm_header, text="Explorer", font=("", 9, "bold")).pack(side=tk.LEFT)
        ttk.Button(fm_header, text="↻", width=3, command=self._refresh_file_tree).pack(side=tk.RIGHT)

        self.fm_path_var = tk.StringVar(value=os.getcwd())
        path_entry = ttk.Entry(self.fm_frame, textvariable=self.fm_path_var, font=("", 8))
        path_entry.pack(fill=tk.X, padx=4, pady=2)
        path_entry.bind("<Return>", lambda e: self._set_explorer_root(self.fm_path_var.get()))

        self.file_tree = ttk.Treeview(self.fm_frame, show="tree", selectmode="browse")
        self.file_tree.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        self.file_tree.bind("<Double-1>", self._on_tree_double_click)
        self.file_tree.bind("<<TreeviewOpen>>", self._on_tree_expand)

        # Scrollbar for tree
        tree_scroll = ttk.Scrollbar(self.file_tree, orient=tk.VERTICAL, command=self.file_tree.yview)
        self.file_tree.configure(yscrollcommand=tree_scroll.set)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self._populate_file_tree(os.getcwd())

        # ---- Editor area (right) ----
        editor_container = ttk.Frame(self.main_paned)
        self.main_paned.add(editor_container, weight=1)

        # Vertical paned: Editor | Terminal
        self.vert_paned = ttk.PanedWindow(editor_container, orient=tk.VERTICAL)
        self.vert_paned.pack(fill=tk.BOTH, expand=True)

        # Text + Line numbers
        editor_frame = ttk.Frame(self.vert_paned)
        self.vert_paned.add(editor_frame, weight=4)

        self.line_numbers = LineNumbers(editor_frame, None)  # placeholder, set later
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)

        text_frame = ttk.Frame(editor_frame)
        text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.v_scroll = ttk.Scrollbar(text_frame, orient=tk.VERTICAL)
        self.h_scroll = ttk.Scrollbar(text_frame, orient=tk.HORIZONTAL)

        self.text = tk.Text(
            text_frame,
            wrap=tk.WORD,
            undo=True,
            maxundo=-1,
            font=(self.font_family, self.font_size),
            padx=6,
            pady=4,
            insertwidth=2,
            relief=tk.FLAT,
            borderwidth=0,
            highlightthickness=0,
        )
        self.line_numbers.text = self.text  # link

        self.v_scroll.config(command=self._on_text_scroll)
        self.h_scroll.config(command=self.text.xview)
        self.text.config(yscrollcommand=self._on_text_yscroll, xscrollcommand=self.h_scroll.set)

        self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Configure tags for syntax & current line
        self.text.tag_configure("current_line", background="#2a2d2e")
        self.text.bind("<KeyRelease>", self._on_key_release)
        self.text.bind("<ButtonRelease-1>", self._on_cursor_move)
        self.text.bind("<<Modified>>", self._on_text_modified)

        # ---- Terminal ----
        self.term_frame = ttk.Frame(self.vert_paned)
        # Initially not added; will be toggled

        term_header = ttk.Frame(self.term_frame)
        term_header.pack(fill=tk.X)
        ttk.Label(term_header, text="Terminal", font=("", 9, "bold")).pack(side=tk.LEFT, padx=4)
        ttk.Button(term_header, text="Clear", width=6, command=self._clear_terminal).pack(side=tk.RIGHT, padx=2)

        self.term_output = tk.Text(
            self.term_frame, height=10, state=tk.DISABLED,
            font=("Consolas", 10), relief=tk.FLAT, borderwidth=0,
        )
        self.term_output.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        term_input_frame = ttk.Frame(self.term_frame)
        term_input_frame.pack(fill=tk.X, padx=2, pady=2)
        ttk.Label(term_input_frame, text="❯").pack(side=tk.LEFT)
        self.term_input = ttk.Entry(term_input_frame)
        self.term_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)
        self.term_input.bind("<Return>", self._run_terminal_command)
        ttk.Button(term_input_frame, text="Run", width=5, command=self._run_terminal_command).pack(side=tk.RIGHT)

        # Start with terminal hidden
        self._term_visible = False

    def _create_status_bar(self):
        self.status = ttk.Frame(self, relief=tk.SUNKEN)
        self.status.pack(side=tk.BOTTOM, fill=tk.X)

        self.status_left = ttk.Label(self.status, text="Ready", anchor=tk.W)
        self.status_left.pack(side=tk.LEFT, padx=6)

        self.status_pos = ttk.Label(self.status, text="Ln 1, Col 1", width=16, anchor=tk.E)
        self.status_pos.pack(side=tk.RIGHT, padx=4)

        self.status_enc = ttk.Label(self.status, text="UTF-8", width=10, anchor=tk.E)
        self.status_enc.pack(side=tk.RIGHT, padx=4)

        self.status_wrap = ttk.Label(self.status, text="Wrap", width=8, anchor=tk.E)
        self.status_wrap.pack(side=tk.RIGHT, padx=4)

        self.status_theme = ttk.Label(self.status, text="Dark", width=12, anchor=tk.E)
        self.status_theme.pack(side=tk.RIGHT, padx=4)

    # ------------------------------------------------------------------
    # Scrolling / Line numbers sync
    # ------------------------------------------------------------------
    def _on_text_scroll(self, *args):
        self.text.yview(*args)
        self.line_numbers.redraw()

    def _on_text_yscroll(self, first, last):
        self.v_scroll.set(first, last)
        self.line_numbers.redraw()

    # ------------------------------------------------------------------
    # Themes
    # ------------------------------------------------------------------
    def _apply_theme(self, name: str):
        theme = THEMES.get(name, THEMES["Dark"])
        self.current_theme.set(name)

        self.configure(bg=theme["bg"])
        self.text.configure(
            bg=theme["bg"],
            fg=theme["fg"],
            insertbackground=theme["insertbg"],
            selectbackground=theme["selectbg"],
            selectforeground=theme["selectfg"],
        )
        self.line_numbers.configure(bg=theme["linenum_bg"])
        # Store fg for redraw
        self.line_numbers["fg"] = theme["linenum_fg"]

        self.term_output.configure(
            bg=theme["terminal_bg"],
            fg=theme["terminal_fg"],
            insertbackground=theme["terminal_fg"],
        )
        self.text.tag_configure("current_line", background=theme["highlight_current"])

        # Syntax colors
        for tag, color_key in [
            ("keyword", "keyword"),
            ("string", "string"),
            ("comment", "comment"),
            ("number", "number"),
            ("builtin", "builtin"),
        ]:
            self.text.tag_configure(tag, foreground=theme[color_key])

        self.status_theme.config(text=name)
        self.line_numbers.redraw()
        self._rehighlight()

    # ------------------------------------------------------------------
    # File operations
    # ------------------------------------------------------------------
    def new_file(self):
        if not self._confirm_discard():
            return
        self.text.delete("1.0", tk.END)
        self.current_file = None
        self.current_lang = None
        self._update_title()
        self._update_status()
        self.line_numbers.redraw()

    def open_file(self, path: Optional[str] = None):
        if not self._confirm_discard():
            return
        if path is None:
            path = filedialog.askopenfilename(
                title="Open",
                filetypes=[
                    ("All files", "*.*"),
                    ("Text files", "*.txt"),
                    ("Python", "*.py"),
                    ("JSON", "*.json"),
                    ("Markdown", "*.md"),
                    ("HTML", "*.html;*.htm"),
                ],
            )
        if not path:
            return
        try:
            with open(path, "r", encoding=self.encoding, errors="replace") as f:
                content = f.read()
            self.text.delete("1.0", tk.END)
            self.text.insert("1.0", content)
            self.current_file = Path(path)
            self._detect_language()
            self._update_title()
            self._rehighlight()
            self.line_numbers.redraw()
            self._update_status()
            # Also point explorer to the folder
            self._set_explorer_root(str(self.current_file.parent))
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file:\n{e}")

    def save_file(self):
        if self.current_file is None:
            return self.save_as()
        try:
            content = self.text.get("1.0", "end-1c")
            with open(self.current_file, "w", encoding=self.encoding) as f:
                f.write(content)
            self._update_title()
            self.status_left.config(text=f"Saved: {self.current_file.name}")
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Could not save file:\n{e}")
            return False

    def save_as(self):
        path = filedialog.asksaveasfilename(
            title="Save As",
            defaultextension=".txt",
            filetypes=[
                ("Text files", "*.txt"),
                ("Python", "*.py"),
                ("JSON", "*.json"),
                ("Markdown", "*.md"),
                ("All files", "*.*"),
            ],
        )
        if not path:
            return False
        self.current_file = Path(path)
        self._detect_language()
        return self.save_file()

    def _confirm_discard(self) -> bool:
        # Simple check: if modified (we track via edit_modified)
        if self.text.edit_modified():
            answer = messagebox.askyesnocancel(
                "Unsaved Changes",
                "Do you want to save changes before continuing?",
            )
            if answer is None:
                return False
            if answer:
                return self.save_file()
        return True

    def _on_close(self):
        if self._confirm_discard():
            self.destroy()

    def _update_title(self):
        name = self.current_file.name if self.current_file else "Untitled"
        self.title(f"{name} - {APP_NAME}")

    def _detect_language(self):
        self.current_lang = None
        if self.current_file:
            ext = self.current_file.suffix.lower()
            self.current_lang = EXT_TO_LANG.get(ext)

    # ------------------------------------------------------------------
    # File Manager
    # ------------------------------------------------------------------
    def _populate_file_tree(self, root_path: str):
        self.file_tree.delete(*self.file_tree.get_children())
        root_path = os.path.abspath(root_path)
        self.fm_path_var.set(root_path)

        # Root node
        root_id = self.file_tree.insert("", "end", text=os.path.basename(root_path) or root_path,
                                        values=[root_path], open=True)
        self._add_directory_children(root_id, root_path)

    def _add_directory_children(self, parent_id, dir_path):
        try:
            entries = sorted(os.listdir(dir_path), key=lambda x: (not os.path.isdir(os.path.join(dir_path, x)), x.lower()))
            for name in entries:
                if name.startswith("."):
                    continue
                full = os.path.join(dir_path, name)
                is_dir = os.path.isdir(full)
                node = self.file_tree.insert(parent_id, "end", text=name, values=[full])
                if is_dir:
                    # Dummy child so it shows the expand arrow
                    self.file_tree.insert(node, "end", text="...")
        except PermissionError:
            pass

    def _on_tree_expand(self, event):
        item = self.file_tree.focus()
        if not item:
            return
        children = self.file_tree.get_children(item)
        # If only dummy, populate
        if len(children) == 1 and self.file_tree.item(children[0], "text") == "...":
            self.file_tree.delete(children[0])
            path = self.file_tree.item(item, "values")[0]
            self._add_directory_children(item, path)

    def _on_tree_double_click(self, event):
        item = self.file_tree.focus()
        if not item:
            return
        path = self.file_tree.item(item, "values")[0]
        if os.path.isfile(path):
            self.open_file(path)
        elif os.path.isdir(path):
            # Expand / collapse already handled
            pass

    def _set_explorer_root(self, path: str):
        if os.path.isdir(path):
            self._populate_file_tree(path)

    def _refresh_file_tree(self):
        self._populate_file_tree(self.fm_path_var.get())

    def _toggle_file_manager(self):
        if self.show_file_manager.get():
            self.main_paned.insert(0, self.fm_frame, weight=0)
        else:
            self.main_paned.forget(self.fm_frame)

    # ------------------------------------------------------------------
    # Terminal
    # ------------------------------------------------------------------
    def _toggle_terminal(self):
        if self.show_terminal.get():
            if not self._term_visible:
                self.vert_paned.add(self.term_frame, weight=1)
                self._term_visible = True
                self.term_input.focus_set()
        else:
            if self._term_visible:
                self.vert_paned.forget(self.term_frame)
                self._term_visible = False

    def _append_terminal(self, text: str, tag: str = None):
        self.term_output.config(state=tk.NORMAL)
        if tag:
            self.term_output.insert(tk.END, text, tag)
        else:
            self.term_output.insert(tk.END, text)
        self.term_output.see(tk.END)
        self.term_output.config(state=tk.DISABLED)

    def _clear_terminal(self):
        self.term_output.config(state=tk.NORMAL)
        self.term_output.delete("1.0", tk.END)
        self.term_output.config(state=tk.DISABLED)

    def _run_terminal_command(self, event=None):
        cmd = self.term_input.get().strip()
        if not cmd:
            return
        self.term_input.delete(0, tk.END)
        self._append_terminal(f"❯ {cmd}\n")

        def worker():
            try:
                # Use shell for convenience (user's own machine)
                result = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    cwd=self.fm_path_var.get() or os.getcwd(),
                    timeout=30,
                )
                out = result.stdout or ""
                err = result.stderr or ""
                if out:
                    self.after(0, lambda: self._append_terminal(out))
                if err:
                    self.after(0, lambda: self._append_terminal(err))
                if result.returncode != 0 and not err:
                    self.after(0, lambda: self._append_terminal(f"[exit code {result.returncode}]\n"))
            except subprocess.TimeoutExpired:
                self.after(0, lambda: self._append_terminal("[timeout after 30s]\n"))
            except Exception as e:
                self.after(0, lambda: self._append_terminal(f"[error] {e}\n"))

        threading.Thread(target=worker, daemon=True).start()

    # ------------------------------------------------------------------
    # Editing helpers
    # ------------------------------------------------------------------
    def _toggle_wrap(self):
        wrap = tk.WORD if self.word_wrap.get() else tk.NONE
        self.text.config(wrap=wrap)
        self.status_wrap.config(text="Wrap" if self.word_wrap.get() else "No Wrap")
        self.line_numbers.redraw()

    def _toggle_line_numbers(self):
        if self.show_line_numbers.get():
            self.line_numbers.pack(side=tk.LEFT, fill=tk.Y, before=self.text.master)
        else:
            self.line_numbers.pack_forget()

    def choose_font(self):
        # Simple font chooser
        families = sorted(tkfont.families())
        dialog = tk.Toplevel(self)
        dialog.title("Font")
        dialog.geometry("360x280")
        dialog.transient(self)
        dialog.grab_set()

        ttk.Label(dialog, text="Family:").pack(anchor=tk.W, padx=8, pady=4)
        family_var = tk.StringVar(value=self.font_family)
        family_cb = ttk.Combobox(dialog, textvariable=family_var, values=families, state="readonly")
        family_cb.pack(fill=tk.X, padx=8)

        ttk.Label(dialog, text="Size:").pack(anchor=tk.W, padx=8, pady=4)
        size_var = tk.IntVar(value=self.font_size)
        size_spin = ttk.Spinbox(dialog, from_=8, to=48, textvariable=size_var, width=6)
        size_spin.pack(anchor=tk.W, padx=8)

        def apply():
            self.font_family = family_var.get()
            self.font_size = size_var.get()
            self.text.configure(font=(self.font_family, self.font_size))
            self.line_numbers.redraw()
            dialog.destroy()

        ttk.Button(dialog, text="OK", command=apply).pack(pady=12)

    def zoom_in(self):
        self.font_size = min(48, self.font_size + 1)
        self.text.configure(font=(self.font_family, self.font_size))
        self.line_numbers.redraw()

    def zoom_out(self):
        self.font_size = max(8, self.font_size - 1)
        self.text.configure(font=(self.font_family, self.font_size))
        self.line_numbers.redraw()

    def zoom_reset(self):
        self.font_size = 11
        self.text.configure(font=(self.font_family, self.font_size))
        self.line_numbers.redraw()

    def find_dialog(self):
        dialog = tk.Toplevel(self)
        dialog.title("Find")
        dialog.geometry("360x120")
        dialog.transient(self)
        dialog.grab_set()

        ttk.Label(dialog, text="Find what:").pack(anchor=tk.W, padx=8, pady=4)
        entry = ttk.Entry(dialog, width=40)
        entry.pack(padx=8, fill=tk.X)
        entry.focus_set()

        case_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(dialog, text="Match case", variable=case_var).pack(anchor=tk.W, padx=8)

        def do_find():
            needle = entry.get()
            if not needle:
                return
            start = self.text.index(tk.INSERT)
            pos = self.text.search(needle, start, tk.END, nocase=not case_var.get())
            if not pos:
                # wrap around
                pos = self.text.search(needle, "1.0", start, nocase=not case_var.get())
            if pos:
                end = f"{pos}+{len(needle)}c"
                self.text.tag_remove("sel", "1.0", tk.END)
                self.text.tag_add("sel", pos, end)
                self.text.mark_set(tk.INSERT, end)
                self.text.see(pos)
            else:
                messagebox.showinfo("Find", "Cannot find the text.", parent=dialog)

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=8)
        ttk.Button(btn_frame, text="Find Next", command=do_find).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Close", command=dialog.destroy).pack(side=tk.LEFT, padx=4)
        entry.bind("<Return>", lambda e: do_find())

    def replace_dialog(self):
        dialog = tk.Toplevel(self)
        dialog.title("Replace")
        dialog.geometry("380x160")
        dialog.transient(self)
        dialog.grab_set()

        ttk.Label(dialog, text="Find what:").grid(row=0, column=0, sticky=tk.W, padx=8, pady=4)
        find_entry = ttk.Entry(dialog, width=30)
        find_entry.grid(row=0, column=1, padx=8, pady=4)
        find_entry.focus_set()

        ttk.Label(dialog, text="Replace with:").grid(row=1, column=0, sticky=tk.W, padx=8, pady=4)
        repl_entry = ttk.Entry(dialog, width=30)
        repl_entry.grid(row=1, column=1, padx=8, pady=4)

        case_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(dialog, text="Match case", variable=case_var).grid(row=2, column=1, sticky=tk.W, padx=8)

        def find_next():
            needle = find_entry.get()
            if not needle:
                return
            start = self.text.index(tk.INSERT)
            pos = self.text.search(needle, start, tk.END, nocase=not case_var.get())
            if not pos:
                pos = self.text.search(needle, "1.0", start, nocase=not case_var.get())
            if pos:
                end = f"{pos}+{len(needle)}c"
                self.text.tag_remove("sel", "1.0", tk.END)
                self.text.tag_add("sel", pos, end)
                self.text.mark_set(tk.INSERT, end)
                self.text.see(pos)
            else:
                messagebox.showinfo("Replace", "Cannot find the text.", parent=dialog)

        def replace_one():
            if self.text.tag_ranges("sel"):
                self.text.delete("sel.first", "sel.last")
                self.text.insert(tk.INSERT, repl_entry.get())
            find_next()

        def replace_all():
            needle = find_entry.get()
            repl = repl_entry.get()
            if not needle:
                return
            content = self.text.get("1.0", tk.END)
            flags = 0 if case_var.get() else re.IGNORECASE
            new_content, count = re.subn(re.escape(needle), repl, content, flags=flags)
            if count:
                self.text.delete("1.0", tk.END)
                self.text.insert("1.0", new_content.rstrip("\n"))
                messagebox.showinfo("Replace", f"Replaced {count} occurrence(s).", parent=dialog)
            else:
                messagebox.showinfo("Replace", "No matches found.", parent=dialog)

        btn_frame = ttk.Frame(dialog)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="Find Next", command=find_next).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="Replace", command=replace_one).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="Replace All", command=replace_all).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="Close", command=dialog.destroy).pack(side=tk.LEFT, padx=3)

    def goto_line(self):
        line = simpledialog.askinteger("Go to Line", "Line number:", parent=self, minvalue=1)
        if line:
            self.text.mark_set(tk.INSERT, f"{line}.0")
            self.text.see(tk.INSERT)
            self._highlight_current_line()

    # ------------------------------------------------------------------
    # Syntax highlighting
    # ------------------------------------------------------------------
    def _rehighlight(self, event=None):
        # Remove previous syntax tags
        for tag in ("keyword", "string", "comment", "number", "builtin"):
            self.text.tag_remove(tag, "1.0", tk.END)

        if not self.syntax_enabled.get() or not self.current_lang:
            return

        patterns = SYNTAX_PATTERNS.get(self.current_lang)
        if not patterns:
            return

        content = self.text.get("1.0", tk.END)
        for pattern, tag in patterns:
            try:
                for match in re.finditer(pattern, content, re.MULTILINE):
                    start = f"1.0+{match.start()}c"
                    end = f"1.0+{match.end()}c"
                    self.text.tag_add(tag, start, end)
            except re.error:
                continue

    def _highlight_current_line(self, event=None):
        self.text.tag_remove("current_line", "1.0", tk.END)
        self.text.tag_add("current_line", "insert linestart", "insert lineend+1c")

    def _on_key_release(self, event=None):
        self._highlight_current_line()
        self._update_status()
        # Debounced rehighlight for performance
        if hasattr(self, "_hl_after"):
            self.after_cancel(self._hl_after)
        self._hl_after = self.after(300, self._rehighlight)

    def _on_cursor_move(self, event=None):
        self._highlight_current_line()
        self._update_status()

    def _on_text_modified(self, event=None):
        self.text.edit_modified(False)
        self.line_numbers.redraw()

    def _update_status(self, event=None):
        try:
            pos = self.text.index(tk.INSERT)
            line, col = pos.split(".")
            self.status_pos.config(text=f"Ln {line}, Col {int(col)+1}")
        except Exception:
            pass
        self.status_enc.config(text=self.encoding.upper())
        self.status_wrap.config(text="Wrap" if self.word_wrap.get() else "No Wrap")

    # ------------------------------------------------------------------
    # Shortcuts
    # ------------------------------------------------------------------
    def _bind_shortcuts(self):
        self.bind("<Control-n>", lambda e: self.new_file())
        self.bind("<Control-o>", lambda e: self.open_file())
        self.bind("<Control-s>", lambda e: self.save_file())
        self.bind("<Control-Shift-S>", lambda e: self.save_as())
        self.bind("<Control-f>", lambda e: self.find_dialog())
        self.bind("<Control-h>", lambda e: self.replace_dialog())
        self.bind("<Control-g>", lambda e: self.goto_line())
        self.bind("<Control-plus>", lambda e: self.zoom_in())
        self.bind("<Control-equal>", lambda e: self.zoom_in())  # = key
        self.bind("<Control-minus>", lambda e: self.zoom_out())
        self.bind("<Control-0>", lambda e: self.zoom_reset())
        # Also on the text widget
        self.text.bind("<Control-a>", lambda e: self.text.tag_add("sel", "1.0", "end-1c") or "break")

    def show_about(self):
        messagebox.showinfo(
            "About Notepadxx",
            f"{APP_NAME} v{VERSION}\n\n"
            "A full-featured Notepad alternative with IDE extras.\n"
            "Built with pure Python + Tkinter.\n\n"
            "Features: Themes, Line Numbers, Word Wrap,\n"
            "Syntax Highlighting, File Manager, Terminal,\n"
            "Find/Replace, and more.\n\n"
            "https://github.com/BenFreedomWalker/Notepadxx",
        )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main():
    # High-DPI awareness on Windows (best effort)
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    app = Notepadxx()
    app.mainloop()


if __name__ == "__main__":
    main()
