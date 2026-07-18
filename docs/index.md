# Player — audio player with queue and multi-backend support

The `Player` plugin adds audio playback to osysHome: it queues audio files and plays them through any of several backends, with volume control and level-based filtering.

## Quick Start

### Step 1. Configure the playback backend

1. Open the osysHome admin panel and go to the `Player` module (category `App`).
2. In the `Backend` field, select a playback method:
   - `auto` — the plugin auto-selects the best backend for your platform
   - `winmedia` — Windows Media Player (Windows only, requires `pywin32`)
   - `pulseaudio` — PulseAudio `paplay` (Linux only)
   - `gstreamer` — GStreamer `gst-play-1.0` (Linux only)
   - `vlc` — VLC Media Player (`python-vlc`)
   - `ffplay` — FFmpeg `ffplay`
   - `command` — custom command template
3. If you selected `command`, fill in `Command` — a template with `{file}` and `{volume}` placeholders. Example: `"C:\Program Files\mpv\mpv.exe" --volume={volume} "{file}"`
4. Click `Submit`.

**Auto-detection priority order:**
- **Windows:** WinMedia → VLC → FFplay → Command
- **Linux:** GStreamer → PulseAudio → VLC → FFplay → Command

### Step 2. Configure volume and minimum level

The plugin does not store volume internally — it reads it from a system property on each playback:
- **Volume** — select an object and property with values 0–100 (normalized to 0.0–1.0 internally)
- **Min level** — select an object and property for the minimum level threshold

If the `Volume` property value is unavailable, `0.8` (80%) is used as fallback.

### Step 3. Play a sound

```python
callPluginFunction("Player", "playSound", {
    "file_name": "notification.wav",
    "level": 5
})
```

The file is resolved relative to the project's `APP_DIR`. If `level` is below the `Min level` value, the file is not played.

## Queue Behavior

- Each `playSound` call pushes the file into a `queue.Queue`.
- A daemon background worker thread drains the queue sequentially.
- If the worker is already running, new files are simply appended to the queue.

## Backend Details & Installation

### WinMedia (Windows)

- **Library:** `pywin32` (`win32com.client`)
- **Mechanism:** COM dispatch via `WMPlayer.OCX`
- **Volume scale:** `int(volume * 100)` (0–100)
- **Formats:** all formats supported by Windows Media Player

**Installation:**
```powershell
pip install pywin32
```
No additional system packages required — Windows Media Player is bundled with Windows.

### PulseAudio (Linux)

- **Utility:** `paplay`
- **Volume scale:** `int(volume * 65536)` (PulseAudio native scale)
- **Formats:** WAV, FLAC, Ogg Vorbis (depends on `paplay` capabilities)

**Installation:**
```bash
# Debian/Ubuntu
sudo apt install pulseaudio-utils

# Fedora
sudo dnf install pulseaudio-utils

# Arch
sudo pacman -S pulseaudio
```
`paplay` is typically included with any PulseAudio-enabled desktop.

### GStreamer (Linux)

- **Utility:** `gst-play-1.0`
- **Volume scale:** `--volume` argument (GStreamer scale)
- **Formats:** most audio formats (MP3, WAV, FLAC, Ogg, etc.)

**Installation:**
```bash
# Debian/Ubuntu
sudo apt install gstreamer1.0-tools gstreamer1.0-plugins-base gstreamer1.0-plugins-good

# Fedora
sudo dnf install gstreamer1-plugins-base gstreamer1-plugins-good

# Arch
sudo pacman -S gst-plugins-base gst-plugins-good
```
For MP3 playback you may also need `gstreamer1.0-plugins-ugly` or `gstreamer1.0-libav`.

### VLC (cross-platform)

- **Library:** `python-vlc`
- **Mechanism:** `vlc.MediaPlayer` bindings
- **Volume scale:** `int(volume * 100)` (0–100)
- **Formats:** all formats supported by VLC

**Installation:**
```bash
pip install python-vlc
```
The VLC desktop application must also be installed on the system:

- **Windows:** Download from https://www.videolan.org/vlc/ — ensure the installer path is in `PATH` or the VLC plugin directory matches your Python architecture (32 vs 64 bit).
- **Linux:**
  ```bash
  # Debian/Ubuntu
  sudo apt install vlc

  # Fedora
  sudo dnf install vlc

  # Arch
  sudo pacman -S vlc
  ```
- **macOS:** `brew install --cask vlc`

### FFplay (cross-platform)

- **Utility:** `ffplay` from FFmpeg
- **Volume scale:** `-volume` argument (0–100)
- **Formats:** most audio formats via FFmpeg decoders

**Installation:**
```bash
# Windows: download from https://ffmpeg.org/download.html and add to PATH

# Linux
sudo apt install ffmpeg          # Debian/Ubuntu
sudo dnf install ffmpeg          # Fedora
sudo pacman -S ffmpeg            # Arch

# macOS
brew install ffmpeg
```

### Command (cross-platform)

- **Template:** user-defined command with `{file}` (file path) and `{volume}` (float 0.0–1.0) placeholders
- If `{file}` is absent from the template, the file path is appended as the last argument
- On Windows `{volume}` is replaced with `int(volume * 100)`, otherwise with the float value
- Argument parsing uses `shlex.split` with `posix=False` on Windows, `posix=True` elsewhere

**Examples:**

Windows (mpv):
```
"C:\Program Files\mpv\mpv.exe" --volume={volume} "{file}"
```

Linux (mpv):
```
mpv --volume={volume} "{file}"
```

Linux (aplay — no volume support):
```
aplay "{file}"
```

## Implementation Details

- All backend libraries are lazy-imported — the plugin never crashes on missing dependencies.
- If the selected backend is unavailable, the plugin falls back to auto-detection.
- If no backend is available at all, `playSound` returns `False` and logs an error.
- Volume is normalized to `0.0–1.0`, then scaled per-backend.
- File path is resolved as `os.path.join(app.config["APP_DIR"], file_name)`.

## Actions

The module registers the action `playsound`. Any code in osysHome can trigger audio playback by calling the global `playSound` function from `app.core.lib.common`:

```python
from app.core.lib.common import playSound

# Simple call
playSound("door_open.mp3", level=10)
```

The core system finds all plugins with the `playsound` action (including Player) and submits the request to each in a thread pool.

The Player module automatically:
1. Checks that `level >= Min level` (if min level is configured)
2. Pushes the file into the internal playback queue
3. Starts a background thread if not already running
4. Selects the best available backend and plays the file with the current volume

You can also call the plugin directly:

```python
callPluginFunction("Player", "playSound", {
    "file_name": "door_open.mp3",
    "level": 10
})
```

| Action | Description |
|--------|-------------|
| `playsound` | Play an audio file. Attached to the global `playSound()` function. |

### Global function signature

```python
playSound(file_name: str, level: int = 0, args: dict = None)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `file_name` | `str` | Path to the media file (relative to `APP_DIR`) |
| `level` | `int` | Priority level for filtering (default `0`) |
| `args` | `dict` | Optional extra arguments (default `None`) |

## Automation Example

```python
from app.core.lib.common import playSound

# Play a notification sound when a sensor triggers
if getProperty("Sensor.door") == "open":
    playSound("door_open.mp3", level=10)
```

## Version

Current version: **0.2**

## Requirements

- Flask
- osysHome core system

Optional backend-specific dependencies:
- `pywin32` (WinMedia, Windows)
- `python-vlc` (VLC)
- `paplay` from `pulseaudio-utils` (PulseAudio, Linux)
- `gst-play-1.0` from `gstreamer1.0-tools` (GStreamer, Linux)
- `ffplay` from `ffmpeg` (FFplay)
