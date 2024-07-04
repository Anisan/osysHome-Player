from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired

# Определение класса формы
class SettingsForm(FlaskForm):
    command = StringField('Command')
    propertyMinLevel = StringField('Property min level')
    submit = SubmitField('Submit')