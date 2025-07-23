import os
import vlc
import subprocess
import time
import threading
from app.core.main.BasePlugin import BasePlugin
import queue
from plugins.Player.forms.SettingForms import SettingsForm
from app.core.lib.object import getProperty

class Player(BasePlugin):

    def __init__(self,app):
        super().__init__(app,__name__)
        self.title = "Player"
        self.description = """This is a plugin play sound"""
        self.category = "App"
        self.version = "0.1a"
        self.actions = ["playsound"]
        self.is_playing = False
        self.queue = queue.Queue()

    def initialization(self):
        # Инициализация плеера VLC
        self.player = vlc.MediaPlayer()

    def admin(self, request):
        settings = SettingsForm()
        if request.method == 'GET':
            settings.command.data = self.config.get('command','')
            settings.propertyMinLevel.data = self.config.get('propertyMinLevel','')
        else:
            if settings.validate_on_submit():
                self.config["command"] = settings.command.data
                self.config["propertyMinLevel"] = settings.propertyMinLevel.data
                self.saveConfig()
        content = {
            "form": settings,
        }
        return self.render('main_player.html', content)

    def playSound(self, file_name:str, level:int=0, args=None):
        propertyMinLevel = self.config.get('propertyMinLevel','')
        minLevel = 0
        if propertyMinLevel:
            value = getProperty(propertyMinLevel)
            if value:
                minLevel = int(value)
        if level < minLevel:
            return

        # Добавление звука в очередь
        self.logger.debug("Add sound to queue " + file_name)
        self.queue.put(file_name)
        
        # Запуск потока проигрывания, если он не запущен
        if not hasattr(self, '_playback_thread') or not self._playback_thread.is_alive():
            self.logger.debug("Create thread playback")
            self._playback_thread = threading.Thread(
                target=self._playback_worker,
                daemon=True
            )
            self._playback_thread.start()

    def _playback_worker(self):
        """Рабочая функция потока для проигрывания звуков из очереди."""
        self.is_playing = True
        while not self.queue.empty():
            file_path = self.queue.get()
            app_dir = self._app.config["APP_DIR"]
            file_path = os.path.join(app_dir,file_path)
            self.logger.debug("Start play " + file_path)
            cmnd = self.config.get('command', '')
            if cmnd:
                self.play_audio_cmd(file_path, cmnd)
            else:
                self.play_audio_vlc(file_path, volume=0.95)
            self.logger.debug("End play %s", file_path)
            self.queue.task_done()
        self.logger.debug("Empty queue sounds")
        # Сбрасываем флаг is_playing, когда очередь пуста
        self.is_playing = False

    def play_audio_vlc(self, file_path, volume=1.0):
        try:
            # media object
            media = vlc.Media(file_path)
            media.parse()
            duration = media.get_duration()
            if duration <= 0:
                duration = 1000
            self.logger.debug("Duration " + str(duration))
            # setting media to the media player
            self.player.set_media(media)
            # Установка громкости
            self.player.audio_set_volume(int(volume * 100))
            # Проигрывание аудио
            self.player.play()
            time.sleep(duration / 1000 + 0.5)
            self.logger.debug("Stop on duration " + file_path)
            # Ждем завершения проигрывания
            while self.player.is_playing():
                continue

        except Exception as e:
            self.logger.exception(e)

        # Освобождение ресурсов плеера
        # player.release()

    def play_audio_cmd(self, file_path, cmnd):
        try:
            cmd = cmnd.split()
            cmd.append(file_path)
            subprocess.run(cmd, check=True)
        except Exception as e:
            self.logger.exception(e)
