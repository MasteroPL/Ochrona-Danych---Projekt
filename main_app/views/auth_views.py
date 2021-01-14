from app_init import app
from flask import render_template, request, session, jsonify, redirect
from flask_login import login_user, logout_user
import config as settings
from models.user import User, UserDoesNotExistError, UserAlreadyRegisteredError
from models.failed_login import FailedLogin
import datetime

from forms import LoginForm
@app.route("/login/", methods=["GET", "POST"])
def login():
    global_message = request.args.get("info", "")

    form = LoginForm()

    if form.validate_on_submit():
        can_log_in, error = FailedLogin.verify_log_in(request.remote_addr, form.login.data)
        if not can_log_in:
            form.password.errors.append(error)

            return render_template("auth/login.html", form=form, global_message=global_message)

        try:
            user = User.get_by_login(form.login.data)

            if user.verify_password(form.password.data):
                login_user(user, duration=datetime.timedelta(hours=1))

                return redirect("/files/")
            else:
                FailedLogin.register_failed_attempt(request.remote_addr, user)
                form.password.errors.append("Błędny login lub hasło")
        except UserDoesNotExistError:
            FailedLogin.register_failed_attempt(request.remote_addr, None)
            form.password.errors.append("Błędny login lub hasło")

    return render_template("auth/login.html", form=form, global_message=global_message)

@app.route("/logout/", methods=["GET"])
def logout():
    logout_user()
    return redirect("/login/")

from forms import RegisterForm
@app.route("/register/", methods=["GET", "POST"])
def register():

    form = RegisterForm()

    if form.validate_on_submit():
        user = User(
            login=form.login.data
        )
        try:
            user.register(form.password.data)

            return redirect("/login/?info=Rejestracja%20zako%C5%84czona%20pomy%C5%9Blnie")
        except UserAlreadyRegisteredError:
            form.login.errors.append("Użytkownik o tej nazwie już istnieje!")

    return render_template("auth/register.html", form=form)