import json
import os
import re
import shutil
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "mort_config.json")

SKIP_DIRS = {
    "$Recycle.Bin", "Windows", "Program Files", "Program Files (x86)",
    "OneDrive", "CrossDevice", "AppData", "node_modules", ".git",
}

QUALITY_TAGS = re.compile(
    r'\b(720p|1080p|1080i|2160p|4k|uhd|hd|sd|'
    r'x264|x265|h264|h265|hevc|avc|mpeg[24]?|'
    r'aac|ac3|dts|flac|mp3|ogg|'
    r'bluray|blu-ray|bdrip|brrip|webrip|web-dl|webdl|hdtv|dvdrip|hdrip|cam|ts|hdcam|'
    r'remastered|unrated|directors?.cut|extended|proper|repack|'
    r'resampled|dual.?audio|multi|'
    r'hdr|hdr10|dv|dolby.?vision|atmos|'
    r'\bcd\s*\d+|part\s*\d+)\b',
    re.IGNORECASE,
)


def clean_show_name(raw):
    name = raw.replace('.', ' ').replace('_', ' ').replace('-', ' ')
    name = QUALITY_TAGS.sub(' ', name)
    name = re.sub(r'\s+', ' ', name).strip()
    if name.lower().startswith('the '):
        name = name[4:]
    return name.strip()


def parse_episodes(filename):
    base = os.path.splitext(filename)[0]
    season_match = re.search(r'[sS](\d{1,2})', base)
    if not season_match:
        return None
    season = int(season_match.group(1))
    after_season = base[season_match.end():]
    ep_tokens = re.findall(r'[eE](\d{1,3})', after_season, re.IGNORECASE)
    range_match = re.search(r'[-\s]+[eE]?(\d{1,3})', after_season)
    if range_match and ep_tokens:
        range_end = int(range_match.group(1))
        first_ep = int(ep_tokens[0])
        for ep in range(first_ep, range_end + 1):
            if ep not in [int(e) for e in ep_tokens]:
                ep_tokens.append(str(ep))
    if not ep_tokens:
        return None
    episodes = sorted(set(int(e) for e in ep_tokens))
    show_part = base[:season_match.start()]
    show_name = clean_show_name(show_part)
    if not show_name:
        show_name = "Unknown Show"
    return show_name, season, episodes


def show_key(name):
    return name.lower().strip()[:4]


def scan_directories(directories, extensions):
    files = []
    for loc in directories:
        if not os.path.isdir(loc):
            continue
        for root, dirs, filenames in os.walk(loc):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for f in filenames:
                ext = os.path.splitext(f)[1].lower()
                if ext in extensions:
                    files.append((os.path.join(root, f), f))
    return files


def classify_files(files):
    tv_shows = {}
    movies = []
    for fullpath, filename in files:
        result = parse_episodes(filename)
        if result:
            show_name, season, episodes = result
            key = show_key(show_name)
            if key not in tv_shows:
                tv_shows[key] = {'name': show_name, 'seasons': {}}
            tv_shows[key]['seasons'].setdefault(season, set())
            for ep in episodes:
                tv_shows[key]['seasons'][season].add(ep)
            if '_files' not in tv_shows[key]:
                tv_shows[key]['_files'] = []
            tv_shows[key]['_files'].append((fullpath, season, episodes))
        else:
            movies.append(fullpath)
    return tv_shows, movies


# ─── Theme ─────────────────────────────────────────────────────

BG      = "#111111"
SURFACE = "#1a1a1a"
CARD    = "#222222"
BORDER  = "#2a2a2a"
TEXT    = "#e0e0e0"
MUTED   = "#777777"
WHITE   = "#ffffff"
ACCENT  = "#4a9eff"


class MediaOrganizer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Mort")
        self.geometry("820x680")
        self.minsize(700, 540)
        self.configure(bg=BG)

        self.source_dirs = []
        self.detected_tv = {}
        self.detected_movies = []
        self.file_checks = {}

        self._setup_styles()
        self._build_ui()
        self._load_config()

    def _load_config(self):
        if not os.path.exists(CONFIG_PATH):
            return
        try:
            with open(CONFIG_PATH, "r") as f:
                cfg = json.load(f)
            for d in cfg.get("sources", []):
                if os.path.isdir(d) and d not in self.source_dirs:
                    self.source_dirs.append(d)
                    self.dir_listbox.insert(tk.END, d)
            if cfg.get("destination"):
                self.dest_var.set(cfg["destination"])
            for ext, val in cfg.get("extensions", {}).items():
                if ext in self.ext_vars:
                    self.ext_vars[ext].set(val)
            self._update_action()
        except Exception:
            pass

    def _save_config(self):
        cfg = {
            "sources": self.source_dirs,
            "destination": self.dest_var.get(),
            "extensions": {e: v.get() for e, v in self.ext_vars.items()},
        }
        try:
            with open(CONFIG_PATH, "w") as f:
                json.dump(cfg, f, indent=2)
        except Exception:
            pass

    def _setup_styles(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure(".", background=BG, foreground=TEXT, font=("Segoe UI", 10))
        s.configure("Card.TFrame", background=CARD)
        s.configure("TLabel", background=BG, foreground=TEXT)
        s.configure("Muted.TLabel", background=BG, foreground=MUTED)
        s.configure("CardLabel.TLabel", background=CARD, foreground=TEXT)
        s.configure("CardMuted.TLabel", background=CARD, foreground=MUTED)
        s.configure("Section.TLabel", background=BG, foreground=MUTED,
                     font=("Segoe UI", 9, "bold"))
        s.configure("TEntry", fieldbackground=SURFACE, foreground=TEXT,
                     insertcolor=TEXT, borderwidth=0)
        s.configure("TCheckbutton", background=CARD, foreground=TEXT)
        s.map("TCheckbutton", background=[("active", CARD)])
        s.configure("Treeview", background=SURFACE, foreground=TEXT,
                     fieldbackground=SURFACE, rowheight=28, borderwidth=0,
                     font=("Segoe UI", 10))
        s.configure("Treeview.Heading", background=CARD, foreground=MUTED,
                     font=("Segoe UI", 9, "bold"), borderwidth=0)
        s.map("Treeview", background=[("selected", "#2a2a2a")])
        s.configure("Dark.Horizontal.TProgressbar",
                     background=TEXT, troughcolor=SURFACE, borderwidth=0,
                     lightcolor=TEXT, darkcolor=TEXT)

    def _build_ui(self):
        outer = tk.Frame(self, bg=BG)
        outer.pack(fill=tk.BOTH, expand=True, padx=24, pady=20)

        # Header
        hdr = tk.Frame(outer, bg=BG)
        hdr.pack(fill=tk.X, pady=(0, 16))
        tk.Label(hdr, text="Mort", bg=BG, fg=WHITE,
                 font=("Segoe UI", 20, "bold")).pack(side=tk.LEFT)
        tk.Label(hdr, text="Media Organizer", bg=BG, fg=MUTED,
                 font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=(10, 0),
                                              pady=(4, 0))

        self._build_sources(outer)
        self._sep(outer)
        self._build_dest(outer)
        self._sep(outer)
        self._build_advanced(outer)
        self._sep(outer)
        self._build_action(outer)
        self._build_results(outer)
        self._build_progress(outer)

    def _sep(self, parent):
        tk.Frame(parent, bg=BORDER, height=1).pack(fill=tk.X, pady=10)

    # ── Sources ──

    def _build_sources(self, parent):
        card = tk.Frame(parent, bg=CARD, highlightthickness=1,
                         highlightbackground=BORDER)
        card.pack(fill=tk.X, ipady=4)
        inner = tk.Frame(card, bg=CARD)
        inner.pack(fill=tk.X, padx=14, pady=12)

        ttk.Label(inner, text="SOURCE DIRECTORIES",
                   style="Section.TLabel").pack(anchor=tk.W)

        self.dir_listbox = tk.Listbox(inner, height=4, bg=SURFACE,
                                       fg=TEXT, selectbackground="#2a2a2a",
                                       selectforeground=TEXT,
                                       font=("Consolas", 10), bd=0,
                                       highlightthickness=1,
                                       highlightbackground=BORDER,
                                       activestyle="none")
        self.dir_listbox.pack(fill=tk.X, pady=(8, 0))

        btns = tk.Frame(inner, bg=CARD)
        btns.pack(fill=tk.X, pady=(8, 0))
        self._make_btn(btns, "+ Add", self._add_dir, accent=True).pack(
            side=tk.LEFT, padx=(0, 6))
        self._make_btn(btns, "- Remove", self._remove_dir).pack(side=tk.LEFT)

    def _add_dir(self):
        d = filedialog.askdirectory(mustexist=True)
        if d and d not in self.source_dirs:
            self.source_dirs.append(d)
            self.dir_listbox.insert(tk.END, d)
            self._update_action()
            self._save_config()

    def _remove_dir(self):
        for i in reversed(self.dir_listbox.curselection()):
            self.dir_listbox.delete(i)
            del self.source_dirs[i]
        self._update_action()
        self._save_config()

    # ── Destination ──

    def _build_dest(self, parent):
        card = tk.Frame(parent, bg=CARD, highlightthickness=1,
                         highlightbackground=BORDER)
        card.pack(fill=tk.X)
        inner = tk.Frame(card, bg=CARD)
        inner.pack(fill=tk.X, padx=14, pady=12)

        ttk.Label(inner, text="DESTINATION",
                   style="Section.TLabel").pack(anchor=tk.W)

        row = tk.Frame(inner, bg=CARD)
        row.pack(fill=tk.X, pady=(8, 0))

        self.dest_var = tk.StringVar()
        e = tk.Entry(row, textvariable=self.dest_var, bg=SURFACE, fg=TEXT,
                      insertbackground=TEXT, font=("Consolas", 10), bd=0,
                      highlightthickness=1, highlightbackground=BORDER,
                      state="readonly")
        e.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        self._make_btn(row, "Browse", self._browse_dest).pack(side=tk.RIGHT)

    def _browse_dest(self):
        d = filedialog.askdirectory(mustexist=False)
        if d:
            self.dest_var.set(d)
            self._update_action()
            self._save_config()

    # ── Advanced ──

    def _build_advanced(self, parent):
        self._adv_open = False

        self.adv_btn = tk.Button(parent, text="Advanced Settings  \u25bc",
                                  bg=BG, fg=MUTED, activebackground=BG,
                                  activeforeground=TEXT, font=("Segoe UI", 9),
                                  bd=0, relief="flat", cursor="hand2",
                                  command=self._toggle_adv)
        self.adv_btn.pack(anchor=tk.W)

        self.adv_frame = tk.Frame(parent, bg=CARD, highlightthickness=1,
                                    highlightbackground=BORDER)

        inner = tk.Frame(self.adv_frame, bg=CARD)
        inner.pack(fill=tk.X, padx=14, pady=12)

        ttk.Label(inner, text="FILE TYPES",
                   style="Section.TLabel").pack(anchor=tk.W)

        row = tk.Frame(inner, bg=CARD)
        row.pack(anchor=tk.W, pady=(8, 0))

        self.ext_vars = {}
        for ext in [".mkv", ".mp4", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v"]:
            var = tk.BooleanVar(value=(ext == ".mkv"))
            self.ext_vars[ext] = var
            tk.Checkbutton(row, text=ext.upper(), variable=var,
                            bg=CARD, fg=TEXT, activebackground=CARD,
                            activeforeground=TEXT, selectcolor=SURFACE,
                            font=("Consolas", 10), bd=0,
                            command=self._save_config).pack(
                side=tk.LEFT, padx=(0, 14))

    def _toggle_adv(self):
        self._adv_open = not self._adv_open
        if self._adv_open:
            self.adv_frame.pack(fill=tk.X, after=self.adv_btn, pady=(4, 0))
            self.adv_btn.configure(text="Advanced Settings  \u25b2")
        else:
            self.adv_frame.pack_forget()
            self.adv_btn.configure(text="Advanced Settings  \u25bc")

    # ── Action ──

    def _build_action(self, parent):
        f = tk.Frame(parent, bg=BG)
        f.pack(fill=tk.X, pady=(12, 0))

        self.org_btn = tk.Button(f, text="Scan", command=self._do_scan,
                                  bg=WHITE, fg=BG, activebackground="#cccccc",
                                  activeforeground=BG, font=("Segoe UI", 11, "bold"),
                                  bd=0, padx=28, pady=6, cursor="hand2",
                                  state="disabled")
        self.org_btn.pack(side=tk.LEFT)

        self.status_lbl = tk.Label(f, text="", bg=BG, fg=MUTED,
                                    font=("Segoe UI", 9))
        self.status_lbl.pack(side=tk.LEFT, padx=(12, 0))

    def _update_action(self):
        if self.source_dirs and self.dest_var.get():
            self.org_btn.configure(state="normal")
            n = len(self.source_dirs)
            self.status_lbl.configure(
                text=f"{n} source{'s' if n != 1 else ''}")
        else:
            self.org_btn.configure(state="disabled")
            self.status_lbl.configure(text="")

    # ── Results ──

    def _build_results(self, parent):
        self.results_frame = tk.Frame(parent, bg=BG)

        hdr = tk.Frame(self.results_frame, bg=BG)
        hdr.pack(fill=tk.X, pady=(0, 6))
        ttk.Label(hdr, text="DETECTED MEDIA",
                   style="Section.TLabel").pack(side=tk.LEFT)
        self._make_btn(hdr, "All", self._select_all, small=True).pack(
            side=tk.RIGHT, padx=(4, 0))
        self._make_btn(hdr, "None", self._deselect_all, small=True).pack(
            side=tk.RIGHT)

        tree_frame = tk.Frame(self.results_frame, bg=SURFACE, bd=0,
                               highlightthickness=1, highlightbackground=BORDER)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        cols = ("sel", "type", "name", "info")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings",
                                  selectmode="none", height=10,
                                  style="Treeview")
        self.tree.heading("sel", text="\u2610", anchor=tk.W)
        self.tree.heading("type", text="TYPE", anchor=tk.W)
        self.tree.heading("name", text="NAME", anchor=tk.W)
        self.tree.heading("info", text="INFO", anchor=tk.W)
        self.tree.column("sel", width=32, minwidth=32, stretch=False)
        self.tree.column("type", width=56, minwidth=56, stretch=False)
        self.tree.column("name", width=400, minwidth=150)
        self.tree.column("info", width=180, minwidth=80)

        sb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.bind("<Button-1>", self._tree_click)

        footer = tk.Frame(self.results_frame, bg=BG)
        footer.pack(fill=tk.X, pady=(8, 0))
        self.count_lbl = tk.Label(footer, text="", bg=BG, fg=MUTED,
                                   font=("Segoe UI", 9))
        self.count_lbl.pack(side=tk.LEFT)
        self.move_btn = tk.Button(footer, text="Move Files", command=self._do_move,
                                   bg=ACCENT, fg=WHITE, activebackground="#6ab0ff",
                                   activeforeground=WHITE, font=("Segoe UI", 10, "bold"),
                                   bd=0, padx=20, pady=5, cursor="hand2",
                                   state="disabled")
        self.move_btn.pack(side=tk.RIGHT)

    def _populate(self, tv, movies):
        for i in self.tree.get_children():
            self.tree.delete(i)
        self.file_checks.clear()
        self.detected_tv = tv
        self.detected_movies = movies

        tv_n = mv_n = 0

        if tv:
            self.tree.insert("", tk.END, values=("", "", "TV Shows", ""),
                              tags=("sec",))
            for key in sorted(tv):
                d = tv[key]
                fc = len(d.get('_files', []))
                eps = sum(len(e) for e in d['seasons'].values())
                seas = len(d['seasons'])
                info = f"{fc} files, {seas} season{'s' if seas!=1 else ''}, {eps} episodes"
                v = tk.BooleanVar(value=True)
                iid = self.tree.insert("", tk.END,
                                        values=("\u2611", "Show", d['name'], info),
                                        tags=("item",))
                self.file_checks[iid] = v
                tv_n += 1

        if movies:
            self.tree.insert("", tk.END, values=("", "", "Movies", ""),
                              tags=("sec",))
            for p in sorted(movies, key=lambda x: os.path.basename(x).lower()):
                v = tk.BooleanVar(value=True)
                iid = self.tree.insert("", tk.END,
                                        values=("\u2611", "Movie",
                                                 os.path.basename(p), ""),
                                        tags=("item",))
                self.file_checks[iid] = v
                mv_n += 1

        self.tree.tag_configure("sec", foreground=MUTED,
                                 font=("Segoe UI", 9, "bold"))
        self.tree.tag_configure("item", foreground=TEXT)

        total = tv_n + mv_n
        self.count_lbl.configure(
            text=f"{total} item{'s' if total!=1 else ''}")
        self.move_btn.configure(state="normal" if total else "disabled")
        self.results_frame.pack(fill=tk.BOTH, expand=True, pady=(12, 0))

    def _tree_click(self, event):
        if self.tree.identify_region(event.x, event.y) != "cell":
            return
        if self.tree.identify_column(event.x) != "#1":
            return
        iid = self.tree.identify_row(event.y)
        if iid not in self.file_checks:
            return
        v = self.file_checks[iid]
        v.set(not v.get())
        self.tree.set(iid, "sel", "\u2611" if v.get() else "\u2610")

    def _select_all(self):
        for iid, v in self.file_checks.items():
            v.set(True)
            self.tree.set(iid, "sel", "\u2611")

    def _deselect_all(self):
        for iid, v in self.file_checks.items():
            v.set(False)
            self.tree.set(iid, "sel", "\u2610")

    # ── Progress ──

    def _build_progress(self, parent):
        self.prog_frame = tk.Frame(parent, bg=CARD, highlightthickness=1,
                                     highlightbackground=BORDER)
        inner = tk.Frame(self.prog_frame, bg=CARD)
        inner.pack(fill=tk.X, padx=14, pady=12)
        self.prog_label = tk.Label(inner, text="", bg=CARD, fg=TEXT,
                                    font=("Segoe UI", 10, "bold"))
        self.prog_label.pack(anchor=tk.W)
        self.prog_bar = ttk.Progressbar(inner, mode="determinate",
                                         style="Dark.Horizontal.TProgressbar")
        self.prog_bar.pack(fill=tk.X, pady=(6, 0))
        self.prog_detail = tk.Label(inner, text="", bg=CARD, fg=MUTED,
                                     font=("Segoe UI", 9))
        self.prog_detail.pack(anchor=tk.W, pady=(4, 0))

    # ── Helpers ──

    def _make_btn(self, parent, text, cmd, accent=False, small=False):
        bg = ACCENT if accent else SURFACE
        fg = WHITE if accent else TEXT
        fs = 9 if small else 10
        bd = "bold" if accent or small else "normal"
        b = tk.Button(parent, text=text, command=cmd, bg=bg, fg=fg,
                       activebackground=bg, activeforeground=fg,
                       font=("Segoe UI", fs, bd), bd=0, relief="flat",
                       padx=12 if small else 14, pady=3, cursor="hand2")
        return b

    # ── Scan ──

    def _do_scan(self):
        self.org_btn.configure(state="disabled")
        self.move_btn.configure(state="disabled")
        self.prog_frame.pack(fill=tk.X, pady=(12, 0))
        self.prog_label.configure(text="Scanning...")
        self.prog_bar["value"] = 0
        self.prog_detail.configure(text="")
        threading.Thread(target=self._scan_thread, daemon=True).start()

    def _scan_thread(self):
        exts = {e for e, v in self.ext_vars.items() if v.get()}
        if not exts:
            self.after(0, lambda: messagebox.showwarning(
                "No File Types", "Select at least one file type."))
            self.after(0, lambda: self.org_btn.configure(state="normal"))
            return
        files = scan_directories(self.source_dirs, exts)
        tv, mv = classify_files(files)
        self.after(0, lambda: self._on_scan(tv, mv))

    def _on_scan(self, tv, mv):
        self.prog_frame.pack_forget()
        self.org_btn.configure(state="normal")
        total = sum(len(d.get('_files', [])) for d in tv.values()) + len(mv)
        if total == 0:
            messagebox.showinfo("Empty", "No matching files found.")
            return
        self._populate(tv, mv)

    # ── Move ──

    def _do_move(self):
        shows, movies = [], []
        for iid, v in self.file_checks.items():
            if not v.get():
                continue
            tags = self.tree.item(iid, "tags")
            name = self.tree.set(iid, "name")
            if "item" in tags:
                if self.tree.set(iid, "type") == "Show":
                    for k, d in self.detected_tv.items():
                        if d['name'] == name:
                            shows.append((k, d))
                            break
                else:
                    for p in self.detected_movies:
                        if os.path.basename(p) == name:
                            movies.append(p)
                            break

        if not shows and not movies:
            messagebox.showinfo("Nothing Selected", "Select items to move.")
            return

        self.move_btn.configure(state="disabled")
        self.org_btn.configure(state="disabled")
        self.prog_frame.pack(fill=tk.X, pady=(12, 0))
        self.prog_bar["value"] = 0
        threading.Thread(target=self._move_thread,
                          args=(shows, movies), daemon=True).start()

    def _move_thread(self, shows, movies):
        dest = self.dest_var.get()
        tv_root = os.path.join(dest, "TV Shows")
        mv_root = os.path.join(dest, "Movies")
        os.makedirs(tv_root, exist_ok=True)
        os.makedirs(mv_root, exist_ok=True)

        tasks = []
        for _, d in shows:
            sd = os.path.join(tv_root, d['name'])
            for fp, s, _ in d.get('_files', []):
                tasks.append((fp, os.path.join(sd, f"season {s:02d}",
                                                os.path.basename(fp))))
        for p in movies:
            tasks.append((p, os.path.join(mv_root, os.path.basename(p))))

        total = len(tasks)
        moved = failed = 0

        for i, (src, dst) in enumerate(tasks):
            fn = os.path.basename(src)
            self.after(0, lambda v=i, f=fn: (
                self.prog_bar.configure(value=(v / total) * 100 if total else 0),
                self.prog_label.configure(text=f"{v+1} / {total}"),
                self.prog_detail.configure(text=f"Moving: {f}")))

            if os.path.exists(dst):
                continue
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            try:
                shutil.copy2(src, dst)
                try:
                    os.unlink(src)
                except OSError:
                    pass
                moved += 1
            except Exception as e:
                failed += 1

        self.after(0, lambda: (
            self.prog_bar.configure(value=100),
            self.prog_label.configure(text="Done"),
            self.prog_detail.configure(
                text=f"Moved: {moved}  |  Failed: {failed}"),
            self.org_btn.configure(state="normal"),
            self.move_btn.configure(state="disabled"),
            messagebox.showinfo("Done",
                                f"Moved {moved} file{'s' if moved!=1 else ''}."
                                + (f"\n{failed} failed." if failed else ""))))


if __name__ == "__main__":
    app = MediaOrganizer()
    app.mainloop()
