import os
import shutil


locations = []
while True:
    path = input("Enter search location (or 'done'): ").strip()
    if path.lower() == "done":
        break
    if os.path.isdir(path):
        locations.append(path)
    else:
        print("Invalid directory")

files = []

for loc in locations:
    for root, dirs, filenames in os.walk(loc):
        for f in filenames:
            if f.lower().endswith(".mkv"):
                files.append(os.path.join(root, f))

tvshows = {}  
movies = []

for fullpath in files:
    filename = os.path.basename(fullpath)
    name = filename.lower()

    season = episode = None
    show_end = None

    for i in range(len(name)):
        if i + 2 >= len(name):
            continue

        if name[i] == 's' and name[i+1:i+3].isdigit():
            season = int(name[i+1:i+3])
            show_end = i

        if name[i] == 'e' and name[i+1:i+3].isdigit():
            episode = int(name[i+1:i+3])

    if season is not None and episode is not None and show_end is not None:
        show = filename[:show_end].replace('.', ' ').strip().lower()
        tvshows.setdefault(show, {})
        tvshows[show].setdefault(season, [])
        tvshows[show][season].append(fullpath)
    else:
        movies.append(fullpath)

print("\nTV Shows")
for show in sorted(tvshows):
    print(f"|----{show}")

print("\nMovies")
for m in movies:
    print("|----", os.path.basename(m))

dest = input("\nWhere should files be moved? ").strip()
tv_root = os.path.join(dest, "TV Shows")
movie_root = os.path.join(dest, "Movies")

os.makedirs(tv_root, exist_ok=True)
os.makedirs(movie_root, exist_ok=True)


for show, seasons in tvshows.items():
    show_dir = os.path.join(tv_root, show)
    os.makedirs(show_dir, exist_ok=True)

    for season, episodes in seasons.items():
        season_dir = os.path.join(show_dir, f"season {season:02d}")
        os.makedirs(season_dir, exist_ok=True)

        for src in episodes:
            dst = os.path.join(season_dir, os.path.basename(src)) 
            shutil.move(src, dst)

for src in movies:
    dst = os.path.join(movie_root, os.path.basename(src))
    shutil.move(src, dst)

print("\nDone.")
