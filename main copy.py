import os
os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'

from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.label import MDLabel
from kivymd.uix.filemanager import MDFileManager
from kivy.core.audio import SoundLoader
from kivymd.uix.slider import MDSlider
from kivy.clock import Clock
from kivymd.uix.list import OneLineListItem, MDList
from kivy.uix.image import Image

class MusicPlayer(MDApp):
    def build(self):
        self.playlist = []
        self.current_song = None
        self.sound = None

        # Main layout with reduced padding and spacing
        main_layout = MDBoxLayout(orientation='vertical', padding=5, spacing=5)
        
        # Add logo at the top with reduced size
        logo = Image(source='logo.png', size_hint=(1, 0.1))
        main_layout.add_widget(logo, index=0)

        # Label displaying the current song
        self.label = MDLabel(text='No song playing', size_hint=(1, 0.05))
        main_layout.add_widget(self.label)
        
        # File manager for selecting songs
        self.file_manager = MDFileManager(
            exit_manager=self.exit_manager,
            select_path=self.select_path,
            ext=['.mp3', '.wav']
        )
        
        # Button to open file manager
        open_file_manager_button = MDRaisedButton(
            text='Open File Manager',
            size_hint=(1, 0.05),
            pos_hint={'center_x': 0.5}
        )
        open_file_manager_button.bind(on_press=self.file_manager_open)
        main_layout.add_widget(open_file_manager_button)
        
        # Control buttons (Play/Pause, Stop, Add to Playlist)
        controls_layout = MDGridLayout(cols=3, size_hint=(1, 0.05), spacing=5)
        
        play_button = MDRaisedButton(text='Play/Pause', size_hint=(None, None), size=(80, 40))
        play_button.bind(on_press=self.play_pause_song)
        play_button.icon = 'play-circle'  # Play icon
        play_button.md_bg_color = [0.1, 0.6, 0.1, 1]  # Green background for play
        controls_layout.add_widget(play_button)
        
        stop_button = MDRaisedButton(text='Stop', size_hint=(None, None), size=(80, 40))
        stop_button.bind(on_press=self.stop_song)
        stop_button.icon = 'stop-circle'  # Stop icon
        stop_button.md_bg_color = [0.9, 0.2, 0.2, 1]  # Red background for stop
        controls_layout.add_widget(stop_button)
        
        add_button = MDRaisedButton(text='Add to Playlist', size_hint=(None, None), size=(80, 40))
        add_button.bind(on_press=self.add_to_playlist)
        add_button.icon = 'playlist-plus'  # Add to playlist icon
        controls_layout.add_widget(add_button)
        
        main_layout.add_widget(controls_layout)
        
        # Volume layout with label and slider
        volume_layout = MDBoxLayout(orientation='horizontal', size_hint=(1, 0.05), spacing=5)
        self.volume_slider = MDSlider(min=0, max=1, value=1, size_hint=(0.8, 1))
        self.volume_slider.bind(value=self.set_volume)
        self.volume_label = MDLabel(text=f'Volume: {self.volume_slider.value:.2f}', size_hint=(0.2, 1))
        volume_layout.add_widget(self.volume_label)
        volume_layout.add_widget(self.volume_slider)
        main_layout.add_widget(volume_layout)
        
        # Duration label showing song duration
        self.duration_label = MDLabel(text='Duration: 0:00', size_hint=(1, 0.05))
        main_layout.add_widget(self.duration_label)

        # Playlist list layout
        self.playlist_layout = MDList(size_hint=(1, 0.3))
        main_layout.add_widget(self.playlist_layout)

        return main_layout

    def file_manager_open(self, *args):
        # Open file manager at user's home directory
        self.file_manager.show(os.path.expanduser('~')) 

    def select_path(self, path):
        self.exit_manager()
        self.current_song = path
        self.play_song()

    def exit_manager(self, *args):
        self.file_manager.close()

    def play_pause_song(self, instance):
        if self.sound:
            if self.sound.state == 'play':
                self.sound.stop()
                instance.icon = 'play-circle'  # Change icon to play when stopped
            else:
                self.sound.play()
                instance.icon = 'pause-circle'  # Change icon to pause when playing
        else:
            self.play_song()

    def stop_song(self, instance):
        if self.sound:
            self.sound.stop()
            self.sound = None
            self.label.text = 'No song playing'
            self.duration_label.text = 'Duration: 0:00'
            Clock.unschedule(self.update_progress)

    def play_song(self):
        if self.sound:
            self.sound.stop()
        if self.current_song:
            self.sound = SoundLoader.load(self.current_song)
            if self.sound:
                self.sound.play()
                self.sound.volume = self.volume_slider.value
                self.label.text = f'Playing: {os.path.basename(self.current_song)}'
                self.duration_label.text = f'Duration: {self.format_duration(self.sound.length)}'
                Clock.schedule_interval(self.update_progress, 1)
            else:
                self.label.text = 'Failed to load song'
        else:
            self.label.text = 'No song selected'
            self.duration_label.text = 'Duration: 0:00'

    def add_to_playlist(self, instance):
        if self.current_song:
            self.playlist.append(self.current_song)
            self.label.text = f'Added to playlist: {os.path.basename(self.current_song)}'
            item = OneLineListItem(text=os.path.basename(self.current_song))
            self.playlist_layout.add_widget(item)

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
            current_time = self.format_duration(current_pos)
            self.duration_label.text = f'Current Time: {current_time} / Duration: {self.format_duration(self.sound.length)}'
            if current_pos >= self.sound.length:
                self.stop_song(None)
                Clock.unschedule(self.update_progress)

if __name__ == '__main__':
    MusicPlayer().run()
