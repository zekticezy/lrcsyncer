import tkinter as tk
from tkinter import filedialog, Toplevel, Listbox, Scrollbar, Button
import pygame
import webbrowser
import os

class LRCSyncer:
    def __init__(self, root):
        self.root = root
        self.root.title("LRC Syncer")
        self.root.iconbitmap("content/icon.ico")
        pygame.mixer.init()
        self.audio_path = ""
        self.create_widgets()
        self.create_menu()
        self.lyrics = []
        self.timestamps = []
        self.lyrics_lines = []
        self.current_line_index = -1
        self.current_time = 0

    def create_widgets(self):
        self.import_button = tk.Button(self.root, text="Import Audio File", command=self.import_audio)
        self.import_button.pack(pady=10)
        self.file_name_label = tk.Label(self.root, text="No file imported")
        self.file_name_label.pack(pady=5)
        self.lyrics_text = tk.Text(self.root, height=10, width=50)
        self.lyrics_text.pack(pady=10)
        self.sync_button = tk.Button(self.root, text="Start Syncing", command=self.start_syncing)
        self.sync_button.pack(pady=10)
        self.root.bind("<Up>", self.sync_up)
        self.root.bind("<Down>", self.sync_down)
        self.root.bind("<Return>", self.add_line)

    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        help_menu.add_command(label="Help", command=lambda: self.open_file("html/help.html"))
        help_menu.add_command(label="Contribute", command=lambda: webbrowser.open("https://github.com/zekticezy/lrcsyncer"))
        help_menu.add_command(label="Credits", command=lambda: self.open_file("html/credits.html"))
        help_menu.add_command(label="License", command=lambda: self.open_file("html/license.html"))

    def import_audio(self):
        self.audio_path = filedialog.askopenfilename(filetypes=[("Audio Files", "*.mp3 *.wav")])
        if self.audio_path:
            pygame.mixer.music.load(self.audio_path)
            self.file_name_label.config(text=f"File: {self.audio_path.split('/')[-1]}")
            self.sync_button.config(state=tk.NORMAL)
            print("Audio file imported.")

    def start_syncing(self):
        if not self.audio_path:
            print("No audio file imported.")
            return
        pygame.mixer.music.play()
        self.current_time = pygame.mixer.music.get_pos() / 1000
        print("Syncing started. Use arrow keys to sync.")
        self.show_lyrics_window()

    def sync_up(self, event):
        if self.timestamps:
            if self.current_line_index >= 0:
                self.timestamps.pop(self.current_line_index)
                self.lyrics.pop(self.current_line_index)
                self.current_line_index -= 1
                if self.current_line_index >= 0:
                    last_timestamp = self.timestamps[self.current_line_index]
                    pygame.mixer.music.set_pos(int(last_timestamp * 1000))
                else:
                    pygame.mixer.music.unpause()
                print("Undo last timestamp.")
                self.update_lyrics_window()
            else:
                print("No timestamps to undo.")

    def sync_down(self, event):
        timestamp = pygame.mixer.music.get_pos() / 1000
        if self.lyrics_lines:
            line = self.lyrics_lines.pop(0)
            self.lyrics.append(line)
            self.timestamps.append(timestamp)
            print(f"Timestamp {timestamp} added: {line}")
            self.update_lyrics_window()

    def add_line(self, event):
        lines = self.lyrics_text.get("1.0", tk.END).strip().split('\n')
        if lines:
            self.lyrics_lines.extend(lines)
            self.lyrics_text.delete("1.0", tk.END)
            print("Lines added.")
            self.update_lyrics_window()

    def show_lyrics_window(self):
        self.lyrics_window = Toplevel(self.root)
        self.lyrics_window.title("Lyrics Syncer")
        self.lyrics_window.iconbitmap("content/icon.ico")
        
        self.lyrics_listbox = Listbox(self.lyrics_window, width=80, height=16)
        self.lyrics_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = Scrollbar(self.lyrics_window)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.lyrics_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.lyrics_listbox.yview)
        
        self.update_lyrics_window()

        prev_button = Button(self.lyrics_window, text="Previous", command=self.prev_lyric)
        prev_button.pack(side=tk.LEFT, padx=10, pady=10)
        
        next_button = Button(self.lyrics_window, text="Next", command=self.next_lyric)
        next_button.pack(side=tk.RIGHT, padx=10, pady=10)

    def update_lyrics_window(self):
        self.lyrics_listbox.delete(0, tk.END)
        for i, lyric in enumerate(self.lyrics):
            if self.timestamps[i] is not None:
                self.lyrics_listbox.insert(tk.END, f"[{int(self.timestamps[i] // 60):02}:{int(self.timestamps[i] % 60):02}.{int((self.timestamps[i] % 1) * 1000):03}] {lyric}")
            else:
                self.lyrics_listbox.insert(tk.END, lyric)
                self.lyrics_listbox.itemconfig(tk.END, {'bg':'lightblue'})
            if self.timestamps[i] is None:
                self.lyrics_listbox.itemconfig(tk.END, {'fg':'black'})
            else:
                self.lyrics_listbox.itemconfig(tk.END, {'fg':'blue'})

    def prev_lyric(self):
        if self.current_line_index > 0:
            self.current_line_index -= 1
            self.update_sync_position()

    def next_lyric(self):
        if self.current_line_index < len(self.lyrics) - 1:
            self.current_line_index += 1
            self.update_sync_position()

    def update_sync_position(self):
        if 0 <= self.current_line_index < len(self.lyrics):
            timestamp = self.timestamps[self.current_line_index]
            pygame.mixer.music.set_pos(int(timestamp * 1000))
            print(f"Jumped to timestamp: {timestamp}")

    def save_lrc(self, filename="output.lrc"):
        with open(filename, "w") as f:
            for i in range(len(self.lyrics)):
                if self.timestamps[i] is not None:
                    minute = int(self.timestamps[i] // 60)
                    second = int(self.timestamps[i] % 60)
                    millisecond = int((self.timestamps[i] % 1) * 1000)
                    f.write(f"[{minute:02}:{second:02}.{millisecond:03}] {self.lyrics[i]}\n")
        print(f"LRC file saved as {filename}.")

    def open_file(self, filename):
        path = os.path.join(os.path.dirname(__file__), filename)
        try:
            webbrowser.open(f"file://{path}")
        except Exception as e:
            print(f"Failed to open file: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = LRCSyncer(root)
    root.mainloop()
    app.save_lrc()
