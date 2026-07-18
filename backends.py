import sys
import shlex
import subprocess
import time
import shutil
from app.logging_config import getLogger

logger = getLogger('Player.backends')


class AudioBackend:
    name = "abstract"

    def play(self, file_path: str, volume: float) -> bool:
        raise NotImplementedError


class WinMediaBackend(AudioBackend):
    name = "winmedia"

    @staticmethod
    def is_available() -> bool:
        if sys.platform != 'win32':
            return False
        try:
            import win32com.client
            return True
        except ImportError:
            return False

    def __init__(self):
        import win32com.client
        self._player = win32com.client.Dispatch("WMPlayer.OCX")

    def play(self, file_path: str, volume: float) -> bool:
        try:
            self._player.settings.volume = int(max(0, min(100, volume * 100)))
            media = self._player.newMedia(file_path)
            self._player.currentPlaylist.clear()
            self._player.currentPlaylist.append(media)
            self._player.controls.play()
            while self._player.playState == 3:
                time.sleep(0.1)
            return True
        except Exception as e:
            logger.exception("WinMediaBackend error: %s", e)
            return False


class PulseAudioBackend(AudioBackend):
    name = "pulseaudio"

    @staticmethod
    def is_available() -> bool:
        return sys.platform == 'linux' and shutil.which('paplay') is not None

    def play(self, file_path: str, volume: float) -> bool:
        try:
            vol = int(volume * 65536)
            subprocess.run(['paplay', f'--volume={vol}', file_path], check=True)
            return True
        except Exception as e:
            logger.exception("PulseAudioBackend error: %s", e)
            return False


class GStreamerBackend(AudioBackend):
    name = "gstreamer"

    @staticmethod
    def is_available() -> bool:
        return shutil.which('gst-play-1.0') is not None

    def play(self, file_path: str, volume: float) -> bool:
        try:
            subprocess.run(['gst-play-1.0', f'--volume={volume}', file_path], check=True)
            return True
        except Exception as e:
            logger.exception("GStreamerBackend error: %s", e)
            return False


class VLCBackend(AudioBackend):
    name = "vlc"

    @staticmethod
    def is_available() -> bool:
        try:
            import vlc
            return True
        except ImportError:
            return False

    def __init__(self):
        import vlc
        self._player = vlc.MediaPlayer()

    def play(self, file_path: str, volume: float) -> bool:
        try:
            import vlc
            media = vlc.Media(file_path)
            media.parse()
            duration = media.get_duration()
            if duration <= 0:
                duration = 1000
            self._player.set_media(media)
            self._player.audio_set_volume(int(volume * 100))
            self._player.play()
            time.sleep(duration / 1000 + 0.5)
            while self._player.is_playing():
                time.sleep(0.1)
            return True
        except Exception as e:
            logger.exception("VLCBackend error: %s", e)
            return False


class FFplayBackend(AudioBackend):
    name = "ffplay"

    @staticmethod
    def is_available() -> bool:
        return shutil.which('ffplay') is not None

    def play(self, file_path: str, volume: float) -> bool:
        try:
            vol = int(volume * 100)
            subprocess.run(['ffplay', '-volume', str(vol), '-nodisp', '-autoexit', file_path], check=True)
            return True
        except Exception as e:
            logger.exception("FFplayBackend error: %s", e)
            return False


class CmdBackend(AudioBackend):
    name = "command"

    def __init__(self, command_template: str):
        self.command_template = command_template

    def play(self, file_path: str, volume: float) -> bool:
        try:
            cmd_str = self.command_template
            cmd_str = cmd_str.replace('{volume}', str(int(volume * 100)))

            if '{file}' in cmd_str:
                cmd_str = cmd_str.replace('{file}', file_path)
                cmd = shlex.split(cmd_str, posix=(sys.platform != 'win32'))
            else:
                cmd = shlex.split(cmd_str, posix=(sys.platform != 'win32'))
                cmd.append(file_path)

            subprocess.run(cmd, check=True)
            return True
        except Exception as e:
            logger.exception("CmdBackend error: %s", e)
            return False


_BACKENDS = {
    'winmedia': WinMediaBackend,
    'pulseaudio': PulseAudioBackend,
    'gstreamer': GStreamerBackend,
    'vlc': VLCBackend,
    'ffplay': FFplayBackend,
}


def get_backend(config: dict):
    choice = config.get('backend', 'auto')

    if choice == 'command':
        cmd_template = config.get('command', '')
        if cmd_template:
            return CmdBackend(cmd_template)
        logger.warning("Command backend selected but no command configured")
        choice = 'auto'

    if choice != 'auto':
        cls = _BACKENDS.get(choice)
        if cls and cls.is_available():
            return cls()
        logger.warning("Backend '%s' not available, falling back to auto", choice)

    return _auto_detect(config)


def _auto_detect(config: dict):
    if sys.platform == 'win32' and WinMediaBackend.is_available():
        logger.info("Auto-selected: WinMediaPlayer")
        return WinMediaBackend()

    if sys.platform == 'linux':
        if GStreamerBackend.is_available():
            logger.info("Auto-selected: GStreamer")
            return GStreamerBackend()
        if PulseAudioBackend.is_available():
            logger.info("Auto-selected: PulseAudio")
            return PulseAudioBackend()

    if VLCBackend.is_available():
        logger.info("Auto-selected: VLC")
        return VLCBackend()

    if FFplayBackend.is_available():
        logger.info("Auto-selected: FFplay")
        return FFplayBackend()

    cmd_template = config.get('command', '')
    if cmd_template:
        logger.info("Auto-selected: Command")
        return CmdBackend(cmd_template)

    logger.error("No audio backend available!")
    return None
