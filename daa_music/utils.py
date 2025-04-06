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


MPV_DOWNLOAD_URL = "https://github.com/kamalkoranga/music_cli/raw/main/mpv/mpv-x86_64-20250330-git-5ba7ee5.zip"
INSTALL_DIR = Path.home() / ".cache" / "daa_music" / "mpv"
MPV_EXE = INSTALL_DIR / "mpv-x86_64-20250330-git-5ba7ee5"
MPV_ZIP = INSTALL_DIR / "mpv-x86_64-20250330-git-5ba7ee5.zip"

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