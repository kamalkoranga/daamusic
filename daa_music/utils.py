import os
import shutil
import urllib.request
import zipfile
import asyncio
import platform
from pathlib import Path
from yt_dlp import YoutubeDL
from rich.table import Table
from rich.prompt import Prompt
from rich.console import Console
import heapq
import shlex
from collections import Counter
import threading
import queue
import subprocess

MPV_DOWNLOAD_URL = "https://github.com/kamalkoranga/music_cli/raw/main/mpv/mpv-x86_64-20250330-git-5ba7ee5.zip"
INSTALL_DIR = Path.home() / ".cache" / "daa_music" / "mpv"
MPV_EXE = INSTALL_DIR / "mpv-x86_64-20250330-git-5ba7ee5"
MPV_ZIP = INSTALL_DIR / "mpv-x86_64-20250330-git-5ba7ee5.zip"
CONFIG_PATH = Path.home() / ".cache" / "daa_music" / "music_dir.txt"

# --- DSA: Play history and next-up queue ---
play_history = []  # Stack for played songs
play_counter = Counter()  # Frequency counter for most played
song_queue = queue.Queue()
queue_thread = None
queue_thread_running = False
queue_lock = threading.Lock()
current_song = None
current_process = None


class OfflineSong:
    def __init__(self, title, path, size):
        self.title = title
        self.path = path
        self.size = size  # in bytes

    def __lt__(self, other):
        return self.size < other.size


def get_music_directory(force_prompt=False):
    if CONFIG_PATH.exists() and not force_prompt:
        with open(CONFIG_PATH) as f:
            music_dir = f.read().strip()
        if os.path.isdir(music_dir):
            return music_dir
    # Prompt user for directory
    music_dir = Prompt.ask("Enter path to your music directory")
    while not os.path.isdir(music_dir):
        music_dir = Prompt.ask("Invalid path. Enter path to your music directory")
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        f.write(music_dir)
    return music_dir


def scan_music_folder(folder):
    # DFS traversal to find all music files
    songs = []
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.lower().endswith(('.mp3', '.wav', '.flac', '.aac', '.ogg')):
                path = os.path.join(root, file)
                size = os.path.getsize(path)
                songs.append(OfflineSong(file, path, size))
    return songs


def insertion_sort_by_size(songs):
    for i in range(1, len(songs)):
        key = songs[i]
        j = i - 1
        while j >= 0 and songs[j].size > key.size:
            songs[j + 1] = songs[j]
            j -= 1
        songs[j + 1] = key
    return songs


def linear_search_title(songs, keyword):
    return [song for song in songs if keyword.lower() in song.title.lower()]


def play_offline_song(song_path, song_title=None):
    safe_path = shlex.quote(song_path)
    os.system(f"mpv --no-video {safe_path}")
    if song_title:
        play_history.append(song_title)
        play_counter[song_title] += 1


def show_top_played(console, n=3):
    if not play_counter:
        console.print("[bold yellow]No songs played yet.[/bold yellow]")
        return
    table = Table(title=f"Top {n} Most Played Songs")
    table.add_column("Rank", justify="center", style="cyan")
    table.add_column("Title", style="magenta")
    table.add_column("Plays", style="green")
    for i, (title, count) in enumerate(play_counter.most_common(n), 1):
        table.add_row(str(i), title, str(count))
    console.print(table)

def get_current_song():
    with queue_lock:
        return current_song

def play_song_queue_worker():
    global current_song, current_process
    while True:
        song = song_queue.get()
        if song is None:
            # Drain the queue to remove any remaining songs
            while not song_queue.empty():
                try:
                    song_queue.get_nowait()
                except queue.Empty:
                    break
            break  # Sentinel to stop the thread
        with queue_lock:
            current_song = song
            play_history.append(song.title)
            play_counter[song.title] += 1
            current_process = subprocess.Popen(
                ["mpv", "--no-video", song.path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        # print('current_song: ', getattr(current_song, 'title', str(current_song)))
        # print(f"[QUEUE] Now playing: {song.title}")
        current_process.wait()
        with queue_lock:
            current_song = None
            current_process = None
        song_queue.task_done()


def start_song_queue():
    global queue_thread, queue_thread_running
    if not queue_thread_running:
        queue_thread = threading.Thread(target=play_song_queue_worker, daemon=True)
        queue_thread.start()
        queue_thread_running = True


def add_song_to_queue(song):
    start_song_queue()
    song_queue.put(song)
    print(f"[QUEUE] Added to queue: {song.title}")


def stop_song_queue():
    global current_process, queue_thread_running
    # Terminate current playing song if any
    with queue_lock:
        if current_process and current_process.poll() is None:
            current_process.terminate()
            try:
                current_process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                current_process.kill()
        current_process = None
    # Put sentinel and drain queue
    song_queue.put(None)
    queue_thread_running = False
    if queue_thread:
        queue_thread.join()


def play_offline_music():
    console = Console()
    music_dir = get_music_directory()
    if not os.path.isdir(music_dir):
        console.print("[bold red]Music directory not found![/bold red]")
        return

    # 1. Scan directory (DFS)
    songs = scan_music_folder(music_dir)
    if not songs:
        console.print("[bold red]No music files found in directory![/bold red]")
        return

    # 2. Sort by file size (Insertion Sort)
    songs = insertion_sort_by_size(songs)
    console.print(f"[bold green]Found {len(songs)} songs in '{music_dir}'[/bold green]")

    # 3. Heap: Top 3 largest files
    top3_largest = heapq.nlargest(3, songs, key=lambda s: s.size)

    # 4. Linear search: Find by keyword
    keyword = Prompt.ask("Enter keyword to search in song titles (leave empty to skip)", default="")
    found = songs
    if keyword.strip():
        found = linear_search_title(songs, keyword)
        if not found:
            console.print("[bold red]No songs found with that keyword![/bold red]")
            return
        # If only one song found, play it directly
        if len(found) == 1:
            selected_song = found[0]
            console.print(f"[bold blue]Now Playing:[/bold blue] {selected_song.title}")
            play_offline_song(selected_song.path, selected_song.title)
            return

    while True:
        table = Table(title="Offline Songs (Sorted by Size)")
        table.add_column("Index", justify="center", style="cyan")
        table.add_column("Title", style="magenta")
        table.add_column("Size (MB)", style="green")
        for i, song in enumerate(songs):
            mark = ""
            if song in top3_largest:
                mark = " [Top 3 Largest]"
            table.add_row(str(i + 1), song.title + mark, f"{song.size/1024/1024:.2f}")
        console.print(table)

        choice = Prompt.ask("Enter the index of the song to add to queue (or 'e' to quit)", default="1")
        if choice.lower() == 'e':
            break
        try:
            idx = int(choice) - 1
            if idx < 0 or idx >= len(songs):
                raise ValueError
        except ValueError:
            console.print("[bold red]Invalid choice![/bold red]")
            continue
        selected_song = songs[idx]
        add_song_to_queue(selected_song)
        console.print(f"[bold blue]Added to queue:[/bold blue] {selected_song.title}")
    console.print("[bold green]Queue finished. Exiting.[/bold green]")



def install_mpv():
    system = platform.system()
    if system == "Windows":
        print("Downloading MPV for Windows...")
        INSTALL_DIR.mkdir(parents=True, exist_ok=True)

        # Download the zip file if it's not already downloaded
        if not MPV_ZIP.exists() and MPV_EXE:
            urllib.request.urlretrieve(MPV_DOWNLOAD_URL, MPV_ZIP)
            print("MPV download complete!")

        # Extract the ZIP file if not already extracted
        if not MPV_EXE.exists():
            with zipfile.ZipFile(MPV_ZIP, 'r') as zip_ref:
                zip_ref.extractall(INSTALL_DIR)
            print("MPV extraction complete!")

        # Optional: Remove the zip file after extraction
        MPV_ZIP.unlink()

    elif system == "Darwin":  # macOS
        print("Installing MPV using Homebrew...")
        os.system("brew install mpv")

    elif system == "Linux":
        print("Installing MPV for Linux...")
        os.system("sudo apt update && sudo apt install -y mpv || sudo pacman -S --noconfirm mpv || sudo dnf install -y mpv")
    
    else:
        print("Unsupported OS. Please install MPV manually.")
        exit(1)


def is_mpv_installed():
    if shutil.which("mpv"):
        return True  # MPV is already in the PATH (installed globally)
    if MPV_EXE.exists():
        return True  # MPV is installed locally
    return False


def add_mpv_to_path():
    """Add the MPV installation directory to the PATH environment variable"""
    current_path = os.environ.get("PATH", "")
    mpv_dir = str(INSTALL_DIR / "mpv-x86_64-20250330-git-5ba7ee5")

    # Only add if it's not already in the PATH
    if mpv_dir not in current_path:
        os.environ["PATH"] = mpv_dir + os.pathsep + current_path
        # print(f"Added {mpv_dir} to PATH.")


def check_mpv():
    if not is_mpv_installed():
        print("MPV is not installed ❌")
        install_mpv()

    # Add MPV to the PATH
    add_mpv_to_path()


def play_song(song_url):
    os.system(f"mpv --no-video {song_url}")


async def search_and_play(song_name):
    console = Console()
    console.print(f"[bold green]Searching for:[/bold green] {song_name}")

    ydl_opts = {
        "format": "bestaudio[ext=m4a]/bestaudio",  # Ensure best audio only
        "quiet": True,
        "noplaylist": True,
        "geo_bypass": True,
        "default_search": "ytsearch5",  # Fetch 5 results to speed up search
        "nocheckcertificate": True,  # Skip SSL certificate checks
        "extractor_retries": 0,  # No retries for faster response
        "noprogress": True,  # Disable progress bar to speed up processing
        "ignoreerrors": True,  # Skip errors instead of retrying
        "extract_flat": True,  # Faster metadata extraction
        "skip_download": True,  # Do not process unnecessary metadata
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Referer": "https://www.youtube.com/",
        },
    }

    loop = asyncio.get_event_loop()
    with YoutubeDL(ydl_opts) as ydl:

        results = await loop.run_in_executor(
            None, lambda: ydl.extract_info(f"ytsearch5:{song_name}", download=False)
        )

        if not results or "entries" not in results or not results["entries"]:
            console.print("[bold red]No results found.[/bold red]")
            return

        table = Table(title="Search Results")
        table.add_column("Index", justify="center", style="cyan")
        table.add_column("Title", style="magenta")

        for i, result in enumerate(results["entries"]):
            table.add_row(str(i + 1), result.get("title", "Unknown Title"))

        console.print(table)

        choice = Prompt.ask("Enter the index of the song to play", default="1")

        try:
            choice = int(choice) - 1
            if choice < 0 or choice >= len(results["entries"]):
                raise ValueError
        except ValueError:
            console.print("[bold red]Invalid choice! Playing first song.[/bold red]")
            choice = 0

        selected_song = results["entries"][choice]
        console.print(
            f"[bold blue]Now Playing:[/bold blue] {selected_song.get('title', 'Unknown Title')}"
        )

        song_url = selected_song.get("url")
        if not song_url:
            console.print("[bold red]Error retrieving URL.[/bold red]")
            return

        # os.system(f'start /B mpv --no-video "{url}"')  # run in background
        # os.system(f"mpv --no-video {song_url}")
        play_song(song_url)