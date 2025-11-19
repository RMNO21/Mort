# Movie Org — Media Manager (Revamp)

A Python Tkinter-based media management tool that scans folders for media files (images, videos, audio), stores metadata in a local SQLite database, generates thumbnails, and provides a simple UI for browsing and organizing your media library.

## Features

- Scan and catalog media files from one or more folders
- Automatic thumbnail generation for images and videos
- Quick search, grouping by Movies or TV Shows, and a list or thumbnail view
- Basic organizing tools to move/copy files into a structured library
- Lightweight SQLite database with a small, local footprint

## Prerequisites

- Python 3.8+ (tested with 3.x)
- Tkinter (typically bundled with Python)
- Pillow (PIL) for image handling
- ttkthemes for improved UI aesthetics
- SQLite (built-in in Python)

## Installation (Linux)

1. Ensure Python 3 and Tkinter are installed:
   - `sudo apt-get update`
   - `sudo apt-get install python3 python3-tk python3-pip`

2. Install Python dependencies:
   - `pip3 install -r requirements.txt`

3. Run the application:
   - `python3 src/movies.py`

Optional: Create a virtual environment to isolate dependencies:
- `python3 -m venv venv`
- `source venv/bin/activate` (or `venv\Scripts\activate` on Windows)
- `pip install -r requirements.txt`

## Installation (Windows)

1. Install Python 3.x from https://www.python.org (ensure "Add Python to PATH" is checked).

2. Open Command Prompt and install dependencies:
   - `pip install -r requirements.txt`

3. Run the application:
   - `python src\movies.py`

Note: Windows users may need to install Tkinter separately if it isn't included with the Python distribution.

## Usage

- Launch the app, then use "Add Folder" to point it at media sources.
- Use "Refresh" to scan and populate the library.
- Filter by Movies or TV Shows, or switch to thumbnail view for a visual library.
- Right-click items to open, reveal, or delete.

## Configuration

- The app stores settings in `mm_settings.json` in the project root.
- Thumbnails are cached under `.thumbs_revamp`.

## Contributing

Contributions are welcome. Please open an issue or pull request with a clear description of the change.

## License

This project is licensed under the GNU General Public License v3.0 or later. See the LICENSE file for details.
