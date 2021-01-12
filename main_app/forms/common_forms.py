from flask_wtf import FlaskForm
from wtforms import StringField, FileField, BooleanField, PasswordField
from wtforms.validators import DataRequired


class UploadFileForm(FlaskForm):
    upload_file = FileField(label="Plik", validators=[DataRequired(message="To pole jest wymagane")])
    is_public = BooleanField(label="Publiczny", description="Zaznacz, jeśli chcesz, aby plik był dostępny publicznie. Każdy posiadający do niego link będzie mógł go wyświetlić.")
    password = PasswordField(label="Hasło do pliku", description="Jeśli wypełnisz to pole, plik będzie chroniony hasłem. Nie będzie można odkodować go bez podania poprawnego hasła.")

