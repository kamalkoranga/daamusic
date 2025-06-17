import os
import customtkinter as ctk
from tkinter import filedialog
import subprocess
import json
import signal
import time

class MusicPlayerApp:
    def __init__(self):
        # Initialize the main window
        self.root = ctk.CTk()
        self.root.title("DaaMusic")
        self.root.geometry("900x700")
        
        # Set appearance mode and color theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # MPV process holder
        self.mpv_process = None
        self.current_song_index = -1
        self.song_buttons = []
        self.repeat_mode = False

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Configuration file
        self.config_file = "music_player_config.json"
        
        # Create UI
        self.create_widgets()
        
        # Load music folder
        self.load_music_folder()
        
        # Start the main loop
        self.root.mainloop()

    def create_widgets(self):
        """Set up the user interface"""
        # Create main frame
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Title label
        self.title_label = ctk.CTkLabel(
            self.main_frame, 
            text="🎵 daamusic - Music Streaming GUI", 
            font=("Arial", 34, "bold")
        )
        self.title_label.pack(pady=10)
        
        # Music folder frame
        self.folder_frame = ctk.CTkFrame(self.main_frame)
        self.folder_frame.pack(fill="x", padx=10, pady=5)
        
        self.folder_label = ctk.CTkLabel(
            self.folder_frame, 
            text="Music Folder: Not Selected",
            anchor="w"
        )
        self.folder_label.pack(side="left", fill="x", expand=True)
        
        self.change_folder_btn = ctk.CTkButton(
            self.folder_frame, 
            text="Change Folder",
            command=self.change_music_folder,
            width=120
        )
        self.change_folder_btn.pack(side="right")

        # --- Tabs for Offline and Online ---
        self.tabview = ctk.CTkTabview(self.main_frame, height=500)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=5)
        self.tabview.add("Offline")
        self.tabview.add("Online")
        
        # --- OFFLINE TAB CONTENT ---
        offline_tab = self.tabview.tab("Offline")
        # Move your search box, song list, and controls to the offline tab
        self.search_entry = ctk.CTkEntry(
            offline_tab,
            placeholder_text="Search songs..."
        )
        self.search_entry.pack(fill="x", padx=10, pady=5)
        self.search_entry.bind("<KeyRelease>", self.filter_songs)
        
        self.song_listbox = ctk.CTkScrollableFrame(
            offline_tab,
            height=400,
        )
        self.song_listbox.pack(fill="both", expand=True, padx=10, pady=5)

        self.controls_frame = ctk.CTkFrame(offline_tab)
        self.controls_frame.pack(fill="x", padx=10, pady=10)

        self.prev_btn = ctk.CTkButton(self.controls_frame, text="⏮ Prev", width=80, command=self.play_prev)
        self.prev_btn.pack(side="left", padx=5)

        self.play_pause_btn = ctk.CTkButton(self.controls_frame, text="⏸ Pause", width=80, command=self.toggle_play_pause)
        self.play_pause_btn.pack(side="left", padx=5)

        self.next_btn = ctk.CTkButton(self.controls_frame, text="⏭ Next", width=80, command=self.play_next)
        self.next_btn.pack(side="left", padx=5)

        self.repeat_btn = ctk.CTkButton(self.controls_frame, text="🔁 Repeat Off", width=100, command=self.toggle_repeat)
        self.repeat_btn.pack(side="left", padx=5)

        # --- ONLINE TAB CONTENT ---
        online_tab = self.tabview.tab("Online")
        self.online_search_frame = ctk.CTkFrame(online_tab)
        self.online_search_frame.pack(fill="x", padx=10, pady=10)

        self.online_search_entry = ctk.CTkEntry(
            self.online_search_frame,
            placeholder_text="Search online music..."
        )
        self.online_search_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.online_search_btn = ctk.CTkButton(
            self.online_search_frame,
            text="🔍",
            width=40,
            # command=self.search_online_music  # You can define this method later
        )
        self.online_search_btn.pack(side="left")

    
    def load_music_folder(self):
        """Load music folder from config or ask user"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r") as f:
                    config = json.load(f)
                    music_folder = config.get("music_folder", "")
                    if music_folder and os.path.isdir(music_folder):
                        self.music_folder = music_folder
                        self.folder_label.configure(text=f"Music Folder: {self.music_folder}")
                        self.load_songs()
                        return
        except Exception as e:
            print(f"Error loading config: {e}")
        
        # If no valid config, ask user
        self.change_music_folder()
    
    def save_music_folder(self):
        """Save the music folder to config"""
        try:
            config = {"music_folder": self.music_folder}
            with open(self.config_file, "w") as f:
                json.dump(config, f)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def change_music_folder(self):
        """Change the music folder"""
        folder = filedialog.askdirectory(title="Select Music Folder")
        if folder:
            self.music_folder = folder
            self.folder_label.configure(text=f"Music Folder: {self.music_folder}")
            self.save_music_folder()
            self.load_songs()
    
    def load_songs(self):
        """Load songs from the music folder"""
        # Clear existing songs
        for widget in self.song_listbox.winfo_children():
            widget.destroy()
        self.song_buttons = []
        
        # Get all music files
        self.song_files = []
        supported_formats = (".mp3", ".wav", ".ogg", ".flac", ".m4a", ".wma")
        
        for root, _, files in os.walk(self.music_folder):
            for file in files:
                if file.lower().endswith(supported_formats):
                    full_path = os.path.join(root, file)
                    self.song_files.append(full_path)
        
        # Sort alphabetically
        self.song_files.sort()
        
        # Create buttons for each song
        for index, song in enumerate(self.song_files):
            song_name = os.path.basename(song)
            btn = ctk.CTkButton(
                self.song_listbox,
                text=song_name,
                command=lambda s=song, i=index: self.play_song(s, i),
                anchor="w",
                fg_color="transparent",
                hover_color=("#3a7ebf", "#1f538d")
            )
            btn.pack(fill="x", pady=2)
            self.song_buttons.append(btn)
    
    def filter_songs(self, event=None):
        """Filter songs based on search text"""
        search_text = self.search_entry.get().lower()
        for widget in self.song_listbox.winfo_children():
            if isinstance(widget, ctk.CTkButton):
                song_text = widget.cget("text").lower()
                if search_text in song_text:
                    widget.pack(fill="x", pady=2)
                else:
                    widget.pack_forget()

    def toggle_repeat(self):
        """Toggle repeat mode"""
        self.repeat_mode = not self.repeat_mode
        if self.repeat_mode:
            self.repeat_btn.configure(text="🔁 Repeat On")
        else:
            self.repeat_btn.configure(text="🔁 Repeat Off")

    def play_song(self, song_path, index=None):
        """Play a song using MPV"""
        # Stop current song if playing
        if self.mpv_process and self.mpv_process.poll() is None:
            try:
                self.mpv_process.send_signal(signal.SIGCONT)
            except Exception:
                pass
            self.mpv_process.terminate()
            try:
                self.mpv_process.wait(timeout=2)
            except Exception:
                self.mpv_process.kill()
        self._paused = False
        self.play_pause_btn.configure(text="⏸ Pause")
        # Start new song
        mpv_args = ["mpv", "--no-terminal"]
        if self.repeat_mode:
            mpv_args.append("--loop")
        mpv_args.append(song_path)
        self.mpv_process = subprocess.Popen(
            mpv_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        # Update indicator
        if index is not None:
            for i, btn in enumerate(self.song_buttons):
                btn.configure(fg_color="transparent", text=os.path.basename(self.song_files[i]))
            self.song_buttons[index].configure(fg_color="#1f538d", text="▶ " + os.path.basename(song_path))
            self.current_song_index = index
        print(f"Playing song: {song_path} index: {index}")
        self.root.after(1000, self.check_song_end)

    def check_song_end(self):
        """Check if the song has ended and play next if repeat is off"""
        if self.mpv_process and self.mpv_process.poll() is not None:
            if not self.repeat_mode:
                self.play_next()
        else:
            self.root.after(1000, self.check_song_end)
    
    def play_prev(self):
        """Play previous song (wrap to last if at first)"""
        if not self.song_files:
            return
        if self.current_song_index > 0:
            new_index = self.current_song_index - 1
        else:
            new_index = len(self.song_files) - 1  # Wrap to last
        self.play_song(self.song_files[new_index], new_index)

    def play_next(self):
        """Play next song (wrap to first if at last)"""
        if not self.song_files:
            return
        if self.current_song_index < len(self.song_files) - 1:
            new_index = self.current_song_index + 1
        else:
            new_index = 0  # Wrap to first
        self.play_song(self.song_files[new_index], new_index)

    def toggle_play_pause(self):
        """Toggle play/pause using MPV IPC (or SIGSTOP/SIGCONT as fallback)"""
        if self.mpv_process and self.mpv_process.poll() is None:
            if getattr(self, "_paused", False):
                # Resume
                try:
                    self.mpv_process.send_signal(subprocess.signal.SIGCONT)
                except Exception:
                    pass
                self.play_pause_btn.configure(text="⏸ Pause")
                self._paused = False
            else:
                # Pause
                try:
                    self.mpv_process.send_signal(subprocess.signal.SIGSTOP)
                except Exception:
                    pass
                self.play_pause_btn.configure(text="▶ Play")
                self._paused = True
    
    def on_close(self):
        """Handle app close and cleanup"""
        if self.mpv_process and self.mpv_process.poll() is None:
            try:
                self.mpv_process.send_signal(signal.SIGCONT)
            except Exception:
                pass
            self.mpv_process.terminate()
            try:
                self.mpv_process.wait(timeout=2)
            except Exception:
                self.mpv_process.kill()
        self.root.destroy()


if __name__ == "__main__":
    # Check if MPV is installed
    try:
        subprocess.run(["mpv", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        app = MusicPlayerApp()
    except FileNotFoundError:
        print("MPV is not installed. Please install MPV to use this application.")
        print("On Linux: sudo apt install mpv")
        print("On macOS: brew install mpv")
        print("On Windows: Download from https://mpv.io/installation/")
    except Exception as e:
        print(f"Error: {e}")