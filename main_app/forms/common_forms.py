from flask_wtf import FlaskForm
from wtforms import StringField, FileField
from wtforms.validators import DataRequired


class UploadFileForm(FlaskForm):
    upload_file = FileField(label="Plik", validators=[DataRequired(message="To pole jest wymagane")])
