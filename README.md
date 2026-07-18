# Player - Audio Player Module

![Player Icon](static/Player.png)

Audio playback system for playing sound files and notifications with volume control and queue management.

## Description

The `Player` module provides audio playback capabilities for the osysHome platform. It enables playing sound files, managing playback queue, and controlling volume levels. Supports multiple backends for different platforms.

## Main Features

- ✅ **Audio Playback**: Play audio files via multiple backends
- ✅ **Queue Management**: Queue multiple audio files
- ✅ **Volume Control**: Volume read from system property in real-time
- ✅ **Level Filtering**: Filter playback by minimum level threshold
- ✅ **Multi-Backend**: WinMedia (Windows), PulseAudio/GStreamer (Linux), VLC, FFplay, custom command
- ✅ **Auto-Detection**: Automatic backend selection based on platform
- ✅ **No Transcoding**: Plays any format the native backend supports
- ✅ **Threading**: Background daemon thread for playback

## Admin Panel

The module provides an admin interface for:

- **Backend Selection**: Choose audio backend (auto, winmedia, pulseaudio, gstreamer, vlc, ffplay, command)
- **Volume Source**: Select linked object + property for volume control (0-100 scale)
- **Min Level Source**: Select linked object + property for minimum level filtering
- **Custom Command**: Configure command template with `{file}` and `{volume}` placeholders

### Available Backends

| Backend | Platform | Description |
|---------|----------|-------------|
| WinMedia | Windows | Windows Media Player COM interface |
| PulseAudio | Linux | PulseAudio `paplay` utility |
| GStreamer | Linux | GStreamer `gst-play-1.0` utility |
| VLC | Cross-platform | VLC Media Player (python-vlc) |
| FFplay | Cross-platform | FFmpeg `ffplay` utility |
| Command | Cross-platform | User-defined command template |

**Auto-detection priority:** Windows: WinMedia → VLC → FFplay → Command; Linux: GStreamer → PulseAudio → VLC → FFplay → Command.

## Usage

### Playing Sound

Use the `playsound` action:
```python
callPluginFunction("Player", "playSound", {
    "file_name": "path/to/sound.mp3",
    "level": 5
})
```

### Volume Control

Volume is read from a linked system property (0–100, normalized to 0.0–1.0 internally). Backend-specific scaling is applied automatically.

### Level Filtering

Set a minimum level threshold via a linked property. Playback is suppressed when `level` parameter is below the threshold.

## Technical Details

- **Backends**: Lazy imports — no crashes on missing libraries
- **Volume**: Live read from property each playback
- **Queue**: Thread-safe `queue.Queue` for audio files
- **Threading**: Daemon background playback thread
- **Format Support**: All formats supported by the selected backend

## Version

Current version: **0.2**

## Category

App

## Actions

The module provides the following actions:
- `playsound` - Play audio file with optional level

## Requirements

- Flask
- osysHome core system

Optional per backend:
- WinMedia: `pywin32` (Windows)
- PulseAudio: `paplay` (Linux)
- GStreamer: `gst-play-1.0` (Linux)
- VLC: `python-vlc`
- FFplay: `ffplay` from FFmpeg

## Author

osysHome Team

## License

See the main osysHome project license
