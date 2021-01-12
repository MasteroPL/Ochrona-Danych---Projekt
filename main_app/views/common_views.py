from app_init import app, mysql
from flask import render_template, request, session, jsonify
from flask_login import login_required, current_user
import config as settings
from werkzeug.utils import secure_filename
import os
from models.file import File
from io import BytesIO

@app.route("/home/", methods=["GET"])
@login_required
def home():
    return render_template("common/home.html")

from forms import UploadFileForm
@app.route("/files/upload/", methods=["GET", "POST"])
@login_required
def upload_file():

    # Domyślny limit uploadu - 16MB
    form = UploadFileForm()

    if form.validate_on_submit():
        f = form.upload_file.data
        ofile = File.from_file(f)

        ofile.encrypt()
        ofile.generate_unique_path(settings.USER_FILE_BASE_PATH)
        ofile.save_to_files()
        try:
            ofile.save_to_database(commit=False)
            ofile.assign_user(current_user, "OWNER", commit=False)
            mysql.commit()
        except:
            mysql.rollback()
        

        return jsonify({"msg": "OK"}), 200

    return render_template("common/files__upload.html", form=form)
