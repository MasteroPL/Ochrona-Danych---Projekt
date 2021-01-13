from flask_wtf import FlaskForm
from wtforms import StringField, FileField, BooleanField, PasswordField, HiddenField
from wtforms.validators import DataRequired, Length


class UploadFileForm(FlaskForm):
    upload_file = FileField(label="Plik", validators=[DataRequired(message="To pole jest wymagane")])
    is_public = BooleanField(label="Publiczny", description="Zaznacz, jeśli chcesz, aby plik był dostępny publicznie. Każdy posiadający do niego link będzie mógł go wyświetlić.")
    password = PasswordField(label="Hasło do pliku", description="Jeśli wypełnisz to pole, plik będzie chroniony hasłem. Nie będzie można odkodować go bez podania poprawnego hasła.")


class EditTextFileForm(FlaskForm):
    note_title = StringField(label="Tytuł", validators=[DataRequired(message="To pole jest wymgane"), Length(min=1, max=43)])
    note_content = StringField(label="Treść", validators=[DataRequired(message="To pole jest wymagane"), Length(min=1, max=1048576)])

    is_public = BooleanField(label="Plik publiczny", description="Zaznacz, jeśli chcesz, aby plik był dostępny publicznie. Każdy posiadający do niego link będzie mógł go wyświetlić.")

    password = HiddenField(label="Hasło do pliku")

class EditBlobFileForm(FlaskForm):
    file_title = StringField(label="Tytuł", validators=[DataRequired(message="To pole jest wymgane"), Length(min=1, max=43)])

    is_public = BooleanField(label="Plik publiczny", description="Zaznacz, jeśli chcesz, aby plik był dostępny publicznie. Każdy posiadający do niego link będzie mógł go wyświetlić.")

    password = HiddenField(label="Hasło do pliku")


class FilePasswordVerificationForm(FlaskForm):
    password = PasswordField(label="Hasło do pliku", validators=[DataRequired(), Length(min=1, max=24)])
    
class EmptyForm(FlaskForm):
    pass