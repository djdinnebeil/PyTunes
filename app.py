import tkinter as tk
from tkinter import ttk
import random
import music_tag
from tksheet import Sheet
from music_paths_with_info import *
from pyglet.media.player import Player
from pyglet.media import Source, load, StaticSource
from pynput import keyboard
from pynput.keyboard import Listener, Key, KeyCode
import pyperclip
import pyautogui

pyautogui.FAILSAFE = False

file_path_index = 6
song_name_index = 0
artist_name_index = 1
album_name_index = 2
length_time_index = 3
total_time_index = 4
total_plays_index = 5

numpad_0 = 96
numpad_1 = 97
numpad_2 = 98
numpad_3 = 99
numpad_4 = 100
numpad_5 = 101
numpad_6 = 102
numpad_7 = 103
numpad_8 = 104
numpad_9 = 105
numpad_asterisk = 106
numpad_plus = 107

# Shortcuts
timestamp_shortcut = numpad_3
next_song_shortcut = numpad_6
play_pause_shortcut = numpad_5
prev_song_shortcut = numpad_4
PyTunes_song_shortcut = numpad_9
print_song_shortcut = numpad_plus
exit_program_shortcut = numpad_0
yes_no_shortcut = numpad_7
episode_title_shortcut = numpad_asterisk
choice_shortcut = numpad_8


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title('PyTunes')

        self.columns = ['Name', 'Artist', 'Album', 'Length', 'Total Time', 'Total Plays']
        self.sorting = [True] * 6

        self.time_counter = 0
        self.index = None

        self.song_tree_frame = ttk.Frame(self)
        self.song_tree = None

        self.song_frame = SongFrame(self)
        self.song_frame.grid()


        self.scrollbar = None
        self.create_song_tree()
        self.song_tree_frame.grid()
        self.row_id = None

        self.song_frame.select_next_song()

        self.listener = keyboard.Listener(on_press=self.process_key_events)
        self.listener.start()

    def create_song_tree(self):
        if self.song_tree:
            self.song_tree.destroy()
        if self.scrollbar:
            self.scrollbar.destroy()

        self.song_tree = ttk.Treeview(self.song_tree_frame, columns=self.columns, show='headings')

        for index, col in enumerate(self.columns):
            self.song_tree.heading(col, text=col, command=self.sort_songs_wrapper(index))

        global song_paths_with_info

        for iid, song in enumerate(song_paths_with_info):
            self.song_tree.insert('', 'end', iid=iid, values=song[:-1])

        self.scrollbar = ttk.Scrollbar(self.song_tree_frame)
        self.scrollbar.configure(command=self.song_tree.yview)
        self.song_tree.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.BOTH)

        self.song_tree.pack()
        self.song_tree.bind('<Double-1>', self.get_song_rowid)


    def sort_songs_wrapper(self, index):
        def sort_songs():
            global song_paths_with_info
            if self.sorting[index]:
                song_paths_with_info.sort(key=lambda e: e[index], reverse=True)
                self.sorting[index] = False
            else:
                song_paths_with_info.sort(key=lambda e: e[index], reverse=False)
                self.sorting[index] = True
            self.create_song_tree()
        return sort_songs

    def get_song_rowid(self, event):
        row_id = int(self.song_tree.selection()[0])
        self.song_frame.select_next_song(row_id=row_id)

    def process_key_events(self, event):
        if hasattr(event, 'vk'):
            numpad_key = event.vk
            if numpad_key == next_song_shortcut:
                self.song_frame.select_next_song()
            elif numpad_key == play_pause_shortcut:
                self.song_frame.play_pause_song()
            elif numpad_key == print_song_shortcut:
                song = f'[{self.song_frame.name_string.get()}] [{self.song_frame.artist_string.get()}] [{self.song_frame.album_string.get()}]'
                self._print_to_screen(song)

    def _print_to_screen(self, message):
        print(message)
        message = message + '\n\n'
        pyperclip.copy(message)
        self._paste_from_clipboard()

    def _paste_from_clipboard(self):
        pyautogui.keyDown('ctrlleft')
        pyautogui.press('v')
        pyautogui.keyUp('ctrlleft')


class SongFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self.parent = parent
        self.active_job = None
        self.time_counter = 0
        self.audio_playing = True
        self.active_job = True
        self.audio_player = Player()
        self.audio_player_2 = Player()
        self.number = None

        self.switch_audio_players = True

        self.name_string = tk.StringVar()
        self.artist_string = tk.StringVar()
        self.album_string = tk.StringVar()
        self.comment_string = tk.StringVar()
        self.length_string = tk.StringVar()

        self.name_label = tk.Label(self, textvariable=self.name_string, width=50, font=('Arial', 18))
        self.artist_label = tk.Label(self, textvariable=self.artist_string, font=('Arial', 12))
        self.album_label = tk.Label(self, textvariable=self.album_string, width=50, font=('Arial', 12))
        self.length_label = tk.Label(self, textvariable=self.length_string, width=50, font=('Arial', 15))

        self.name_label.grid()
        self.artist_label.grid()
        self.album_label.grid()
        self.length_label.grid()

        self.play_pause_button = ttk.Button(self, text='Play/Pause', command=self.play_pause_song)
        self.play_pause_button.grid()

        self.next_song_button = ttk.Button(self, text='Next Song', command=self.select_next_song)
        self.next_song_button.grid()



    def select_next_song(self, row_id=None):
        global song_paths_with_info

        if self.audio_playing:
            self.audio_player.pause()
        if self.number is not None:
            song_paths_with_info[self.number][total_time_index] += self.time_counter
        if self.active_job:
            self.after_cancel(self.active_job)
        if row_id is not None:
            self.number = int(row_id)
        else:
            self.number = random.randrange(0, len(song_paths_with_info))
        print(song_paths_with_info[self.number])
        filepath = song_paths_with_info[self.number][file_path_index]
        if self.audio_player:
            self.audio_player.delete()
        self.song_audio = load(filepath)

        self.audio_player = Player()
        self.audio_player.queue(self.song_audio)
        self.time_counter = 0
        if self.audio_playing:
            self.audio_player.play()

        name = song_paths_with_info[self.number][song_name_index]
        artist = song_paths_with_info[self.number][artist_name_index]
        album = song_paths_with_info[self.number][album_name_index]
        # comment = metadata['comment']
        length = int(song_paths_with_info[self.number][length_time_index])

        self.name_string.set(name)
        self.artist_string.set(artist)
        self.album_string.set(album)
        self.length_string.set(length)

        song_paths_with_info[self.number][total_plays_index] += 1
        self.parent.song_tree.focus(self.number)
        self.parent.song_tree.selection_set(self.number)
        self.parent.song_tree.see(self.number)
        with open('music_paths_with_info.py', 'w+', encoding='utf-8') as f:
            f.write('song_paths_with_info = [\n')

            for song_info in song_paths_with_info:
                f.write(f'{song_info},\n')
            f.write(']')

        if self.audio_playing:
            self.decrease_timer()

    def decrease_timer(self):
        current_time = int(self.length_string.get())
        new_time = current_time - 1
        self.length_string.set(new_time)

        self.time_counter += 1
        if new_time < 1:
            self.select_next_song()
        else:
            self.active_job = self.after(1000, self.decrease_timer)

    def play_pause_song(self):
        if self.audio_playing:
            self.audio_player.pause()
            self.audio_playing = False
            if self.active_job:
                self.after_cancel(self.active_job)
        else:
            self.audio_player.play()
            self.decrease_timer()
            self.audio_playing = True
app = App()
app.mainloop()