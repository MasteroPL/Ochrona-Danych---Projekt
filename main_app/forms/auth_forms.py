from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Length, EqualTo

class LoginForm(FlaskForm):
    login = StringField(label="Nazwa użytkownika", validators=[DataRequired(message="To pole jest wymagane")])
    password = PasswordField(label="Hasło", validators=[DataRequired(message="To pole jest wymagane")])

class RegisterForm(FlaskForm):
    login = StringField(label="Nazwa użytkownika", validators=[DataRequired(message="To pole jest wymagane"), Length(min=3, max=20)])
    password = PasswordField(label="Hasło", validators=[
        DataRequired(message="To pole jest wymagane"), 
        Length(min=8, max=32, message="Hasło musi zawierać pomiędzy 8 a 32 znaków")
    ])
    repeat_password = PasswordField(label="Powtórz hasło", validators=[
        DataRequired(message="To pole jest wymagane"), 
        EqualTo("password", message="Hasła muszą być identyczne")
    ])

    # # Nadpisywanie głównej walidacji
    # def validate(self, extra_validators=None):
    #     success = super().validate(extra_validators=extra_validators)
    #     if not success:
    #         return success

    #     # ... Inne walidacje