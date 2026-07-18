# Player — аудиоплеер с очередью и поддержкой множества бэкендов

Плагин `Player` добавляет в osysHome воспроизведение звуковых файлов: он позволяет ставить аудиофайлы в очередь и проигрывать их через один из доступных аудиобэкендов с поддержкой громкости и фильтрации по уровню.

## Быстрый старт (для новичка)

### Шаг 1. Настройте бэкенд воспроизведения

1. Откройте админку osysHome и перейдите в модуль `Player` (категория `App`).
2. В поле `Backend` выберите способ воспроизведения:
   - `auto` — плагин сам выберет подходящий бэкенд под вашу платформу
   - `winmedia` — Windows Media Player (только Windows, требуется `pywin32`)
   - `pulseaudio` — PulseAudio `paplay` (только Linux)
   - `gstreamer` — GStreamer `gst-play-1.0` (только Linux)
   - `vlc` — VLC Media Player (`python-vlc`)
   - `ffplay` — FFmpeg `ffplay`
   - `command` — произвольная командная строка
3. Если выбран `command`, заполните `Command` — шаблон команды с плейсхолдерами `{file}` и `{volume}`. Пример: `"C:\Program Files\mpv\mpv.exe" --volume={volume} "{file}"`
4. Нажмите `Submit`.

При автоопределении порядок выбора:
- **Windows:** WinMedia → VLC → FFplay → Command
- **Linux:** GStreamer → PulseAudio → VLC → FFplay → Command

### Шаг 2. Настройте громкость и минимальный уровень

Плагин не хранит громкость внутри — он читает её из системного свойства osysHome при каждом воспроизведении:
- **Volume** — выберите объект и свойство, значения 0–100 (будут нормализованы в 0.0–1.0)
- **Min level** — выберите объект и свойство для порога минимального уровня

Если значение из `Volume` недоступно, используется `0.8` (80%).

### Шаг 3. Воспроизведите звук

```python
callPluginFunction("Player", "playSound", {
    "file_name": "notification.wav",
    "level": 5
})
```

Файл ищется относительно `APP_DIR` проекта. Если `level` ниже значения из `Min level`, файл не воспроизводится.

## Работа с очередью

- Каждый вызов `playSound` кладёт файл в очередь (`queue.Queue`).
- Фоновый поток-демон последовательно достаёт файлы из очереди и проигрывает их.
- Если поток уже запущен, новые файлы просто добавляются в очередь.

## Поддерживаемые бэкенды

### WinMedia (Windows)
- **Библиотека:** `pywin32` (win32com.client)
- **Механизм:** COM-объект `WMPlayer.OCX`
- **Громкость:** `int(volume * 100)`, шкала 0–100
- **Форматы:** все, что поддерживает WMP

**Установка:**
```powershell
pip install pywin32
```
Дополнительных системных пакетов не требуется — Windows Media Player встроен в Windows.

### PulseAudio (Linux)
- **Утилита:** `paplay`
- **Громкость:** `int(volume * 65536)`, шкала PA
- **Форматы:** WAV, FLAC, Ogg Vorbis (зависит от paplay)

**Установка:**
```bash
# Debian/Ubuntu
sudo apt install pulseaudio-utils

# Fedora
sudo dnf install pulseaudio-utils

# Arch
sudo pacman -S pulseaudio
```
`paplay` обычно уже установлен в любом дистрибутиве с PulseAudio.

### GStreamer (Linux)
- **Утилита:** `gst-play-1.0`
- **Громкость:** аргумент `--volume` (GStreamer scale)
- **Форматы:** большинство аудиоформатов (MP3, WAV, FLAC, Ogg и др.)

**Установка:**
```bash
# Debian/Ubuntu
sudo apt install gstreamer1.0-tools gstreamer1.0-plugins-base gstreamer1.0-plugins-good

# Fedora
sudo dnf install gstreamer1-plugins-base gstreamer1-plugins-good

# Arch
sudo pacman -S gst-plugins-base gst-plugins-good
```
Для MP3 могут понадобиться `gstreamer1.0-plugins-ugly` или `gstreamer1.0-libav`.

### VLC (кроссплатформенный)
- **Библиотека:** `python-vlc`
- **Механизм:** `vlc.MediaPlayer`
- **Громкость:** `int(volume * 100)`
- **Форматы:** все, что поддерживает VLC

**Установка:**
```bash
pip install python-vlc
```
Само приложение VLC также должно быть установлено в системе:

- **Windows:** Скачайте с https://www.videolan.org/vlc/ — убедитесь, что путь установки есть в `PATH` или разрядность VLC совпадает с разрядностью Python (32 vs 64 бит).
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

### FFplay (кроссплатформенный)
- **Утилита:** `ffplay` из FFmpeg
- **Громкость:** аргумент `-volume` (0–100)
- **Форматы:** большинство аудиоформатов через декодеры FFmpeg

**Установка:**
```bash
# Windows: скачайте с https://ffmpeg.org/download.html и добавьте в PATH

# Linux
sudo apt install ffmpeg          # Debian/Ubuntu
sudo dnf install ffmpeg          # Fedora
sudo pacman -S ffmpeg            # Arch

# macOS
brew install ffmpeg
```

### Command (кроссплатформенный)
- **Шаблон:** команда с `{file}` (путь к файлу) и `{volume}` (число 0.0–1.0)
- Если в шаблоне нет `{file}`, путь добавляется в конец аргументов
- На Windows `{volume}` заменяется на int(volume * 100), иначе на float
- Разбор аргументов: `shlex.split` с `posix=False` на Windows

**Примеры:**

Windows (mpv):
```
"C:\Program Files\mpv\mpv.exe" --volume={volume} "{file}"
```

Linux (mpv):
```
mpv --volume={volume} "{file}"
```

Linux (aplay — без громкости):
```
aplay "{file}"
```

## Детали реализации

- Все библиотеки импортируются лениво (при первом использовании) — плагин не падает, если что-то не установлено.
- Если выбранный бэкенд недоступен, плагин пробует автоопределение.
- Если ни один бэкенд не сработал, возвращается `False`, ошибка логируется.
- Громкость нормализуется в 0.0–1.0, затем масштабируется под конкретный бэкенд.
- Путь к файлу вычисляется как `os.path.join(app.config["APP_DIR"], file_name)`.

## Действия

Модуль регистрирует действие `playsound`. Любой код в osysHome может запустить воспроизведение через глобальную функцию `playSound` из `app.core.lib.common`:

```python
from app.core.lib.common import playSound

# Простой вызов
playSound("door_open.mp3", level=10)
```

Ядро системы находит все плагины с действием `playsound` (включая Player) и отправляет запрос каждому в пул потоков.

Модуль Player автоматически:
1. Проверяет, что `level >= Min level` (если настроен минимальный уровень)
2. Помещает файл во внутреннюю очередь воспроизведения
3. Запускает фоновый поток, если он ещё не активен
4. Выбирает лучший доступный бэкенд и воспроизводит файл с текущей громкостью

Также можно вызвать плагин напрямую:

```python
callPluginFunction("Player", "playSound", {
    "file_name": "door_open.mp3",
    "level": 10
})
```

| Действие | Описание |
|----------|----------|
| `playsound` | Воспроизвести аудиофайл. Привязана к глобальной функции `playSound()`. |

### Сигнатура глобальной функции

```python
playSound(file_name: str, level: int = 0, args: dict = None)
```

| Параметр | Тип | Описание |
|----------|-----|----------|
| `file_name` | `str` | Путь к медиафайлу (относительно `APP_DIR`) |
| `level` | `int` | Уровень приоритета для фильтрации (по умолчанию `0`) |
| `args` | `dict` | Опциональные дополнительные аргументы (по умолчанию `None`) |

## Пример автоматизации

```python
from app.core.lib.common import playSound

# Проиграть звук уведомления при срабатывании датчика
if getProperty("Sensor.door") == "open":
    playSound("door_open.mp3", level=10)
```

## Версия

Текущая версия: **0.2**

## Требования

- Flask
- Основная система osysHome

Опционально:
- `pywin32` (WinMedia, Windows)
- `python-vlc` (VLC)
- `paplay` (PulseAudio, Linux)
- `gst-play-1.0` (GStreamer, Linux)
- `ffplay` (FFplay)
