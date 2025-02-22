import os
import shutil
import platform
import asyncio
import yt_dlp
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table


def install_mpv():
    system = platform.system()
    if system == "Windows":
        print("Downloading MPV for Windows...")
        mpv_installer = "mpv-setup.exe"
        os.system(f'curl -Lo {mpv_installer} https://sourceforge.net/projects/mpv-player-windows/files/latest/download')
        os.system(f'start /wait {mpv_installer} /S')  # Silent install
        os.remove(mpv_installer)
    
    elif system == "Darwin":  # macOS
        print("Installing MPV using Homebrew...")
        os.system("brew install mpv")
    
    elif system == "Linux":
        print("Installing MPV for Linux...")
        os.system("sudo apt update && sudo apt install -y mpv || sudo pacman -S --noconfirm mpv || sudo dnf install -y mpv")
    
    else:
        print("Unsupported OS. Please install MPV manually.")
        exit(1)

def check_mpv():
    if not shutil.which("mpv"):
        print("MPV is not installed. Installing now...")
        install_mpv()
    else:
        print("MPV is already installed.")

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
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:

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


def main():
    os.system("cls" if os.name == "nt" else "clear")
    check_mpv()
    console = Console()
    song = Prompt.ask("Enter song name")
    try:
        asyncio.run(search_and_play(song))
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Exiting...[/bold yellow]")


if __name__ == "__main__":
    main()
