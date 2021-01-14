from flask_wtf import FlaskForm
from wtforms import StringField, FileField, BooleanField, PasswordField, HiddenField, IntegerField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Length


class UploadFileForm(FlaskForm):
    upload_file = FileField(label="Plik", validators=[DataRequired(message="To pole jest wymagane")])
    is_public = BooleanField(label="Publiczny", description="Zaznacz, jeśli chcesz, aby plik był dostępny publicznie. Każdy posiadający do niego link będzie mógł go wyświetlić.")
    password = PasswordField(label="Hasło do pliku", description="Jeśli wypełnisz to pole, plik będzie chroniony hasłem. Nie będzie można odkodować go bez podania poprawnego hasła.")


class FilePasswordVerificationForm(FlaskForm):
    password = PasswordField(label="Hasło do pliku", validators=[DataRequired(message="To pole jest wymgane"), Length(min=1, max=24)])
    
class EmptyForm(FlaskForm):
    pass

class FileShareForm(FlaskForm):
    username = StringField(label="Użytkownik", validators=[DataRequired(message="To pole jest wymgane"), Length(min=3, max=20)])
    access_type = SelectField(label="Typ dostępu", choices=[
        ("READER", "Odczyt"),
        ("EDITOR", "Edytor")
    ], validators=[DataRequired(message="To pole jest wymgane")])

class FileUnshareForm(FlaskForm):
    user_id = HiddenField(label="Użytkownik", validators=[DataRequired()])


class TextFileEditForm(FlaskForm):
    content = TextAreaField(label="Treść", validators=[DataRequired(message="To pole jest wymagane"), Length(min=0, max=1048576, message="Maksymalna dopuszczalna długość pliku to 1048576 znaków")])

class TextFileEditDecryptedForm(FlaskForm):
    content = TextAreaField(label="Treść", validators=[DataRequired(message="To pole jest wymagane"), Length(min=0, max=1048576, message="Maksymalna dopuszczalna długość pliku to 1048576 znaków")])
    decrypt_token = HiddenField(default=None)

class FileRenameForm(FlaskForm):
    new_name = StringField(label="Nowa nazwa pliku", validators=[DataRequired(message="To pole jest wymagane"), Length(min=1, max=43, message="Nazwa pliku nie może być dłuższa niż 43 znaki")])