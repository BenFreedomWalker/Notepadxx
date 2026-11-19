# Notepadxx

A full-featured Notepad-like text editor with IDE extras, built with pure Python and Tkinter.

Looks and feels like classic Windows Notepad, but includes modern power-user and light-IDE features.

## Features

### Classic Notepad core
- New / Open / Save / Save As
- Undo / Redo, Cut / Copy / Paste / Select All
- Find & Replace (with match-case)
- Go to Line
- Word Wrap toggle
- Status bar (line, column, encoding, wrap mode, theme)
- Font selection & zoom (Ctrl + / Ctrl - / Ctrl 0)

### Enhanced editor
- **Themes**: Light, Dark, High Contrast, Classic
- **Line numbers** – synced with scrolling, clickable to jump
- **Syntax highlighting** (basic regex-based) for:
  - Python
  - JSON
  - HTML / XML
  - Markdown
  - C / C++ headers
- Current-line highlight
- Configurable word wrap

### IDE-style panels
- **File Manager / Explorer** (left sidebar)
  - Browse folders
  - Double-click to open files
  - Path bar + refresh
- **Integrated Terminal** (bottom panel)
  - Run shell commands
  - Captures stdout / stderr
  - Working directory follows the explorer root

### Keyboard shortcuts
| Action            | Shortcut          |
|-------------------|-------------------|
| New               | Ctrl+N            |
| Open              | Ctrl+O            |
| Save              | Ctrl+S            |
| Save As           | Ctrl+Shift+S      |
| Find              | Ctrl+F            |
| Replace           | Ctrl+H            |
| Go to Line        | Ctrl+G            |
| Zoom In / Out     | Ctrl+ / Ctrl-     |
| Reset Zoom        | Ctrl+0            |
| Select All        | Ctrl+A            |

## Requirements

- Python 3.8+
- Tkinter (included with most Python installations)

On Debian/Ubuntu:
```bash
sudo apt install python3-tk
```

No third-party packages required.

## Run

```bash
git clone https://github.com/BenFreedomWalker/Notepadxx.git
cd Notepadxx
python main.py
```

Or simply:
```bash
python main.py
```

## Project structure

```
Notepadxx/
├── main.py          # Complete application
├── README.md
└── LICENSE
```

## Screenshots / Notes

- Dark theme is the default (easy on the eyes for coding).
- Toggle File Manager and Terminal from the **View** menu.
- Syntax highlighting activates automatically based on file extension when you open a supported file type.
- The terminal runs commands in a background thread so the UI stays responsive (30 s timeout per command).

## License

See [LICENSE](LICENSE).

---

**Notepadxx** – Notepad, but better.
