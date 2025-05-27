import os
import asyncio
from rich.console import Console
from rich.prompt import Prompt
from daa_music.utils import check_mpv
from .utils import search_and_play, play_offline_music, get_music_directory, play_history, show_top_played

VERSION = "0.0.3"


def main():
    os.system("cls" if os.name == "nt" else "clear")
    print(f"Version: {VERSION}")
    check_mpv()
    console = Console()

    while True:
        console.print("\n[bold cyan]1.[/bold cyan] Search & Play Online")
        console.print("[bold cyan]2.[/bold cyan] Play Offline Music")
        console.print("[bold cyan]3.[/bold cyan] Set Offline Music Directory")
        console.print("[bold cyan]4.[/bold cyan] Show Play History")
        console.print("[bold cyan]5.[/bold cyan] Show Top Played Songs")
        console.print("[bold cyan]6.[/bold cyan] Exit")
        choice = Prompt.ask("Choose an option", choices=["1", "2", "3", "4", "5", "6"], default="1")

        if choice == "1":
            song = Prompt.ask("Enter song name")
            try:
                asyncio.run(search_and_play(song))
            except KeyboardInterrupt:
                console.print("\n[bold yellow]Exiting...[/bold yellow]")
        elif choice == "2":
            play_offline_music()
        elif choice == "3":
            get_music_directory(force_prompt=True)
        elif choice == "4":
            if play_history:
                console.print("[bold yellow]Play History:[/bold yellow]")
                for idx, title in enumerate(reversed(play_history), 1):
                    console.print(f"{idx}. {title}")
            else:
                console.print("[bold yellow]No play history yet.[/bold yellow]")
        elif choice == "5":
            show_top_played(console)
        else:
            break

if __name__ == "__main__":
    main()