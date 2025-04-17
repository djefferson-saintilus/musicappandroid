import os
import json
os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'
import random
from kivy.core.audio import SoundLoader
from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.core.window import Window
from kivy.animation import Animation
from kivy.uix.image import Image
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.behaviors import DragBehavior
from kivy.graphics import Color, Rectangle
from kivy.utils import platform

from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.filemanager import MDFileManager
from kivymd.uix.label import MDLabel
from kivymd.uix.slider import MDSlider
from kivymd.uix.list import OneLineListItem, MDList

from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3

class DraggableSidebar(DragBehavior, RelativeLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.drag_timeout = 10000000
        self.drag_distance = 0
        self.md_bg_color = [0.1, 0.1, 0.3, 1]  # Sidebar background color
        self.padding = dp(5)
        self.spacing = dp(5)

        # Add a shadow effect or border to separate the sidebar visually
        with self.canvas.before:
            Color(0, 0, 0, 0.5)  # Shadow color
            self.shadow = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self.update_shadow, pos=self.update_shadow)

    def update_shadow(self, *args):
        self.shadow.size = self.size
        self.shadow.pos = self.pos

class MusicPlayer(MDApp):
    def build(self):
        # Simplify screen resolution logic for compatibility with Pydroid 3
        if platform == "android":
            Window.fullscreen = True  # Use fullscreen mode for Android
        else:
            Window.size = (360, 640)  # Default size for non-Android platforms

        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "BlueGray"  # Changed primary theme color

        self.playlist = []
        self.current_index = 0
        self.current_song = None
        self.sound = None

        self.playlist_file = 'playlist.json'
        self.load_playlist()

        self.file_manager = MDFileManager(
            exit_manager=self.exit_manager,
            select_path=self.select_path,
            ext=['.mp3', '.wav']
        )

        main_layout = FloatLayout()
        main_layout.canvas.before.clear()
        with main_layout.canvas.before:
            Color(0.05, 0.05, 0.2, 1)  # Main background color
            self.bg_rect = Rectangle(size=Window.size, pos=(0, 0))

        self.sidebar = DraggableSidebar(size_hint=(None, 1), width=dp(200), x=-dp(200))
        
        # Add a close button to the sidebar
        close_button = MDIconButton(
            icon="close",
            size_hint=(None, None),
            size=(dp(30), dp(30)),
            pos_hint={"right": 1, "top": 1},
            on_press=self.toggle_sidebar  # Reuse the toggle_sidebar method to close
        )
        self.sidebar.add_widget(close_button)

        self.playlist_layout = MDList(size_hint=(1, 0.9))  # Adjust size_hint to fill the sidebar
        self.sidebar.add_widget(self.playlist_layout)
        self.refresh_playlist_ui()
        main_layout.add_widget(self.sidebar)

        content_layout = MDBoxLayout(orientation='vertical', size_hint=(1, 1), padding=dp(5), spacing=dp(5),
                                     pos_hint={'x': 0, 'y': 0})

        header_layout = MDBoxLayout(orientation='horizontal', size_hint=(1, None), height=dp(40),
                                    padding=dp(5), spacing=dp(5))
        toggle_sidebar_btn = MDIconButton(icon='playlist-music', on_press=self.toggle_sidebar)  # Playlist icon
        header_layout.add_widget(toggle_sidebar_btn)
        content_layout.add_widget(header_layout)

        self.album_art = Image(source='logo.png', size_hint=(1, 0.3))
        content_layout.add_widget(self.album_art)

        song_info_layout = MDBoxLayout(orientation='vertical', size_hint=(1, None), height=dp(60),
                                       padding=dp(5), spacing=dp(5))
        self.song_title = MDLabel(text='Song Title', size_hint=(1, 0.5), halign='center',
                                  theme_text_color='Custom', text_color=[1, 1, 1, 1], font_style='H6')
        self.artist_name = MDLabel(text='Artist', size_hint=(1, 0.5), halign='center',
                                   theme_text_color='Custom', text_color=[1, 1, 1, 1], font_style='Subtitle2')
        song_info_layout.add_widget(self.song_title)
        song_info_layout.add_widget(self.artist_name)
        content_layout.add_widget(song_info_layout)

        progress_layout = MDBoxLayout(orientation='horizontal', size_hint=(1, None), height=dp(25),
                                      padding=dp(5), spacing=dp(5))
        content_layout.add_widget(progress_layout)

        volume_layout = MDBoxLayout(orientation='horizontal', size_hint=(1, None), height=dp(30), spacing=dp(5))
        self.volume_slider = MDSlider(min=0, max=1, value=1, size_hint=(0.8, 1))
        self.volume_slider.bind(value=self.set_volume)
        self.volume_label = MDLabel(text=f'Volume: {self.volume_slider.value:.2f}', size_hint=(0.2, 1),
                                    halign='center', theme_text_color='Custom', text_color=[0.9, 0.9, 0.9, 1],
                                    font_size=sp(12))
        volume_layout.add_widget(self.volume_label)
        volume_layout.add_widget(self.volume_slider)
        content_layout.add_widget(volume_layout)

        controls_layout = MDBoxLayout(orientation='horizontal', size_hint=(1, None), height=dp(60), spacing=dp(10),
                                      padding=dp(10), pos_hint={'center_x': 0.5})
        shuffle_button = MDIconButton(icon='shuffle', size_hint=(None, None), size=(dp(50), dp(50)))
        shuffle_button.md_bg_color = [0.1, 0.6, 0.1, 1]
        shuffle_button.bind(on_press=self.shuffle_playlist)

        prev_button = MDIconButton(icon='skip-previous', size_hint=(None, None), size=(dp(50), dp(50)))
        prev_button.md_bg_color = [0.1, 0.6, 0.1, 1]
        prev_button.bind(on_press=self.play_previous_song)

        self.play_button = MDIconButton(icon='play-circle', size_hint=(None, None), size=(dp(60), dp(60)))
        self.play_button.md_bg_color = [0.1, 0.6, 0.1, 1]
        self.play_button.bind(on_press=self.play_pause_song)

        next_button = MDIconButton(icon='skip-next', size_hint=(None, None), size=(dp(50), dp(50)))
        next_button.md_bg_color = [0.1, 0.6, 0.1, 1]
        next_button.bind(on_press=self.play_next_song)

        repeat_button = MDIconButton(icon='repeat', size_hint=(None, None), size=(dp(50), dp(50)))
        repeat_button.md_bg_color = [0.1, 0.6, 0.1, 1]
        repeat_button.bind(on_press=self.repeat_song)

        controls_layout.add_widget(shuffle_button)
        controls_layout.add_widget(prev_button)
        controls_layout.add_widget(self.play_button)
        controls_layout.add_widget(next_button)
        controls_layout.add_widget(repeat_button)

        content_layout.add_widget(controls_layout)

        select_song_button = MDRaisedButton(
            text="Select Song",
            size_hint=(0.5, None),
            height=dp(40),
            pos_hint={'center_x': 0.5, 'center_y': 0.1},
            md_bg_color=[0.2, 0.6, 0.2, 1],
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1]
        )
        select_song_button.bind(on_press=self.file_manager_open)
        content_layout.add_widget(select_song_button)

        main_layout.add_widget(content_layout)

        return main_layout

    def toggle_sidebar(self, instance):
        target_x = 0 if self.sidebar.x < 0 else -dp(200)
        Animation(x=target_x, duration=0.3).start(self.sidebar)
        if target_x == 0:
            # Bring the sidebar to the front by adjusting its canvas index
            parent = self.sidebar.parent
            if parent:
                parent.remove_widget(self.sidebar)
                parent.add_widget(self.sidebar)

    def file_manager_open(self, *args):
        self.file_manager.show(os.getcwd())

    def select_path(self, path):
        self.exit_manager()
        if path not in self.playlist:
            self.playlist.append(path)
            self.current_index = len(self.playlist) - 1
            self.save_playlist()
            self.refresh_playlist_ui()
        self.current_song = path
        self.play_song()

    def exit_manager(self, *args):
        self.file_manager.close()

    def set_volume(self, instance, value):
        if self.sound:
            self.sound.volume = value
        self.volume_label.text = f'Volume: {value:.2f}'

    def format_duration(self, duration):
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        return f'{minutes}:{seconds:02d}'

    def update_progress(self, dt):
        if self.sound and self.sound.state == 'play':
            current_pos = self.sound.get_pos()
            if current_pos >= self.sound.length:
                self.play_next_song(None)

    def play_song(self):
        if self.sound:
            self.sound.stop()
        if self.current_song:
            self.sound = SoundLoader.load(self.current_song)
            if self.sound:
                self.sound.play()
                self.sound.volume = self.volume_slider.value
                self.update_metadata()
                self.play_button.icon = 'pause-circle'
                Clock.unschedule(self.update_progress)
                Clock.schedule_interval(self.update_progress, 1)
            else:
                self.song_title.text = 'Failed to load song'
                self.artist_name.text = ''
        else:
            self.song_title.text = 'No song selected'
            self.artist_name.text = ''

    def update_metadata(self):
        try:
            if not self.current_song or not os.path.exists(self.current_song):
                raise FileNotFoundError("Current song file does not exist.")
            
            audio = EasyID3(self.current_song)
            self.song_title.text = audio.get('title', ['Unknown Title'])[0]
            self.artist_name.text = audio.get('artist', ['Unknown Artist'])[0]
        except FileNotFoundError as e:
            self.song_title.text = "File Not Found"
            self.artist_name.text = ""
            print(f"Error: {e}")
        except Exception as e:
            self.song_title.text = os.path.basename(self.current_song) if self.current_song else "Unknown Song"
            self.artist_name.text = "Unknown Artist"
            print(f"Error reading metadata: {e}")

    def play_pause_song(self, instance):
        if self.sound:
            if self.sound.state == 'play':
                self.sound.stop()
                instance.icon = 'play-circle'
            else:
                self.sound.play()
                instance.icon = 'pause-circle'
        else:
            self.play_song()

    def play_next_song(self, instance):
        if self.playlist:
            self.current_index = (self.current_index + 1) % len(self.playlist)
            self.current_song = self.playlist[self.current_index]
            self.play_song()

    def play_previous_song(self, instance):
        if self.playlist:
            self.current_index = (self.current_index - 1) % len(self.playlist)
            self.current_song = self.playlist[self.current_index]
            self.play_song()

    def repeat_song(self, instance):
        self.play_song()

    def shuffle_playlist(self, instance):
        if self.playlist:
            random.shuffle(self.playlist)
            self.current_index = 0
            self.save_playlist()
            self.refresh_playlist_ui()

    def refresh_playlist_ui(self):
        self.playlist_layout.clear_widgets()
        for index, song in enumerate(self.playlist):
            is_current = index == self.current_index
            item = OneLineListItem(
                text=os.path.basename(song),
                theme_text_color="Custom",
                text_color=[0.1, 0.6, 0.1, 1] if is_current else [1, 1, 1, 1],  # Highlight current song
                on_press=lambda x, i=index: self.play_song_by_index(i)
            )
            self.playlist_layout.add_widget(item)

    def play_song_by_index(self, index):
        self.current_index = index
        self.current_song = self.playlist[index]
        self.play_song()
        self.refresh_playlist_ui()  # Update the UI to reflect the current song

    def save_playlist(self):
        with open(self.playlist_file, 'w') as f:
            json.dump(self.playlist, f)

    def load_playlist(self):
        if os.path.exists(self.playlist_file):
            with open(self.playlist_file, 'r') as f:
                self.playlist = json.load(f)

if __name__ == '__main__':
    MusicPlayer().run()
