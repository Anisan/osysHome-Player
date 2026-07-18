from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField

BACKEND_CHOICES = [
    ('auto', 'Auto'),
    ('winmedia', 'WinMediaPlayer (Windows)'),
    ('pulseaudio', 'PulseAudio (Linux)'),
    ('gstreamer', 'GStreamer (Linux)'),
    ('vlc', 'VLC'),
    ('ffplay', 'FFplay'),
    ('command', 'Command'),
]

class SettingsForm(FlaskForm):
    backend = SelectField('Method', choices=BACKEND_CHOICES)
    command = StringField('Command')
    minlevel_object = StringField('Min level object')
    minlevel_property = StringField('Min level property')
    volume_object = StringField('Volume object')
    volume_property = StringField('Volume property')
    submit = SubmitField('Submit')