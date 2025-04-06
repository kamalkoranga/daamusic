import os
import asyncio
from rich.console import Console
from rich.prompt import Prompt
from daa_music.utils import check_mpv
from .utils import search_and_play

VERSION = "0.0.3"


def main():
    os.system("cls" if os.name == "nt" else "clear")
    print(f"Version: {VERSION}")
    check_mpv()
    console = Console()
    song = Prompt.ask("Enter song name")
    try:
        asyncio.run(search_and_play(song))
        pass
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Exiting...[/bold yellow]")


if __name__ == "__main__":
    main()