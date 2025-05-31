import os
import asyncio
from rich.console import Console
from rich.prompt import Prompt
from daa_music.utils import check_mpv, search_and_play, play_offline_music, get_current_song,song_queue, get_music_directory, play_history, show_top_played, stop_song_queue

VERSION = "0.0.4"


def main():
    os.system("cls" if os.name == "nt" else "clear")
    print(f"Version: {VERSION}")
    check_mpv()
    console = Console()

    try:

        while True:
            console.print("\n[bold cyan]1.[/bold cyan] Search & Play Online")
            console.print("[bold cyan]2.[/bold cyan] Play Offline Music")
            console.print("[bold cyan]3.[/bold cyan] Set Offline Music Directory")
            console.print("[bold cyan]4.[/bold cyan] Show Play History")
            console.print("[bold cyan]5.[/bold cyan] Show Top Played Songs")
            console.print("[bold cyan]6.[/bold cyan] Show Queue Status")
            console.print("[bold cyan]7.[/bold cyan] Exit")
            choice = Prompt.ask("Choose an option", choices=["1", "2", "3", "4", "5", "6", "7"], default="1")

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
            elif choice == "6":
                song = get_current_song()
                # Show current playing song and queue
                if song:
                    console.print(f"[bold green]Now Playing:[/bold green] {getattr(song, 'title', str(song))}")
                else:
                    console.print("[bold yellow]No song is currently playing.[/bold yellow]")
                # Show remaining songs in queue
                queue_list = list(song_queue.queue)
                if queue_list:
                    console.print("[bold cyan]Songs in Queue:[/bold cyan]")
                    for idx, song in enumerate(queue_list, 1):
                        # Avoid showing the sentinel None
                        if song is not None:
                            console.print(f"{idx}. {getattr(song, 'title', str(song))}")
                else:
                    console.print("[bold yellow]Queue is empty.[/bold yellow]")

            else:
                stop_song_queue()
                console.print("[bold yellow]Exiting...[/bold yellow]")
                break

    except KeyboardInterrupt:
        console.print("\n[bold yellow]Exiting...[/bold yellow]")

if __name__ == "__main__":
    main()
