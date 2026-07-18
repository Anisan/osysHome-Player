import os
import threading
from app.core.main.BasePlugin import BasePlugin
import queue
from plugins.Player.forms.SettingForms import SettingsForm
from plugins.Player.backends import get_backend
from app.core.lib.object import getProperty


class Player(BasePlugin):

    def __init__(self,app):
        super().__init__(app,__name__)
        self.title = "Player"
        self.description = """This is a plugin play sound"""
        self.category = "App"
        self.version = "0.2"
        self.actions = ["playsound"]
        self.is_playing = False
        self.queue = queue.Queue()
        self._backend = None

    def initialization(self):
        self._backend = None

    def admin(self, request):
        settings = SettingsForm()
        if request.method == 'GET':
            settings.backend.data = self.config.get('backend', 'auto')
            settings.command.data = self.config.get('command','')
            settings.minlevel_object.data = self.config.get('minlevel_object','')
            settings.minlevel_property.data = self.config.get('minlevel_property','')
            settings.volume_object.data = self.config.get('volume_object','')
            settings.volume_property.data = self.config.get('volume_property','')
        else:
            if settings.validate_on_submit():
                self.config["backend"] = settings.backend.data
                self.config["command"] = settings.command.data
                self.config["minlevel_object"] = settings.minlevel_object.data
                self.config["minlevel_property"] = settings.minlevel_property.data
                self.config["volume_object"] = settings.volume_object.data
                self.config["volume_property"] = settings.volume_property.data
                self._backend = None
                self.saveConfig()
        content = {
            "form": settings,
        }
        return self.render('main_player.html', content)

    def _get_volume(self):
        obj = self.config.get('volume_object', '')
        prop = self.config.get('volume_property', '')
        if not obj or not prop:
            return 0.8
        try:
            value = getProperty(f"{obj}.{prop}")
            if value:
                return max(0.0, min(1.0, float(value) / 100.0))
        except Exception:
            pass
        return 0.8

    def _get_minlevel(self):
        obj = self.config.get('minlevel_object', '')
        prop = self.config.get('minlevel_property', '')
        if not obj or not prop:
            return 0
        try:
            value = getProperty(f"{obj}.{prop}")
            if value:
                return int(value)
        except Exception:
            pass
        return 0

    def playSound(self, file_name:str, level:int=0, args=None):
        minLevel = self._get_minlevel()
        if level < minLevel:
            return
        self.queue.put(file_name)

        if not hasattr(self, '_playback_thread') or not self._playback_thread.is_alive():
            self.logger.debug("Create thread playback")
            self._playback_thread = threading.Thread(
                target=self._playback_worker,
                daemon=True
            )
            self._playback_thread.start()

    def _playback_worker(self):
        self.is_playing = True

        if self._backend is None:
            self._backend = get_backend(self.config)

        if self._backend is None:
            self.logger.error("No audio backend available, skipping playback")
            self.is_playing = False
            return

        self.logger.info("Using backend: %s", self._backend.name)

        while not self.queue.empty():
            file_path = self.queue.get()
            app_dir = self._app.config["APP_DIR"]
            file_path = os.path.join(app_dir, file_path)
            self.logger.debug("Start play " + file_path)

            volume = self._get_volume()
            self._backend.play(file_path, volume)

            self.logger.debug("End play %s", file_path)
            self.queue.task_done()

        self.logger.debug("Empty queue sounds")
        self.is_playing = False
