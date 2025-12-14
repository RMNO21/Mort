

# Mort - TV & Movie Organizer

[![Python](https://img.shields.io/badge/python-3.6%2B-blue)](https://www.python.org/)

`Mort` is a Python script to organize your TV shows and movies. It scans specified directories for `.mkv` files, detects TV shows based on season and episode patterns, and moves files into a structured folder hierarchy while keeping the original filenames intact.

---

## Features

* Detects **TV shows** using `SxxExx` format.
* Detects **movies**.
* Moves TV shows into structured folders: `TV Shows/Show Name/Season XX/`.
* Moves movies into a separate `Movies/` folder.
* Preserves original filenames.
* Case-insensitive show name detection.
* Supports multiple source directories.

---

## Requirements

* Python 3.6 or higher.
* Works on Windows, macOS, and Linux.
* No external dependencies.

---

## Installation

1. Clone the repository:

```bash
git clone https://github.com/RMNO21/Mort.git
```

2. Navigate into the repository:

```bash
cd Mort
```

---

## Usage

1. Run the script:

```bash
python mort.py
```

2. Input source directories one by one, typing `done` when finished.
3. Enter the destination folder to move the files.
4. The script will organize all `.mkv` files into `TV Shows` and `Movies` folders, preserving original filenames.

---

## License

This project is licensed under the **GNU General Public License v3.0**.

---

