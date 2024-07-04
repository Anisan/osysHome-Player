import os
import vlc
import subprocess
from flask import render_template
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

    def initialization(self):
        self.queue = queue.Queue()
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
    
    def playSound(self, file_name:str, level:int=0):
        propertyMinLevel = self.config.get('propertyMinLevel','')
        minLevel = 0
        if propertyMinLevel:
            value = getProperty(propertyMinLevel)
            if value:
                minLevel = int(value)
        if level < minLevel:
            return 
        self.queue.put(file_name)
        cmnd = self.config.get('command','')
        if not self.is_playing:
            if cmnd:
                self.play_audio_cmd(cmnd)
            else:
                self.play_audio_vlc(volume=0.95)

    # TODO перенести в цикл для обработки очереди проигрывания
    # TODO приоритетную очередь
    def play_audio_vlc(self, volume=1.0):
        self.is_playing = True

        app_dir = self._app.config["APP_DIR"]
        file_path = self.queue.get()
        full_path=os.path.join(app_dir,file_path)
        self.logger.debug("Start play "+full_path)
        
        # media object
        media = vlc.Media(full_path)
 
        # setting media to the media player
        self.player.set_media(media)
 
        # Установка громкости
        self.player.audio_set_volume(int(volume * 100))

        # Проигрывание аудио
        self.player.play()

        # Ждем завершения проигрывания
        while self.player.is_playing():
            continue
        
        self.logger.debug("Stop play "+full_path)

        if not self.queue.empty():
            self.play_audio_vlc(volume)
        
        # Освобождение ресурсов плеера
        #player.release()
        self.is_playing = False

    def play_audio_cmd(self, cmnd):
        try:
            self.is_playing = True
            app_dir = self._app.config["APP_DIR"]
            filePath = self.queue.get()
            filePath=os.path.join(app_dir,filePath)
            self.logger.debug("Start play %s", filePath)
            cmd = cmnd.split()
            cmd.append(filePath)
            subprocess.run(cmd, check=True)
            self.logger.debug("End play %s", filePath)
        except Exception as e:
            self.logger.exception(e)

        if not self.queue.empty():
            self.play_audio_cmd(cmnd)
        
        self.is_playing = False



        