from app_init import app
from flask import render_template, request, session, jsonify
from config import flask_config as settings
from werkzeug.utils import secure_filename
import os
from models.file import File
from io import BytesIO

from forms import UploadFileForm
@app.route("/files/upload/", methods=["GET", "POST"])
def upload_file():
    form = UploadFileForm()

    if form.validate_on_submit():
        f = form.upload_file.data
        filename = secure_filename(f.filename)

        fbytes = f.stream._file

        ofile = File(file_bytes=fbytes.read(), file_extension="PNG", file_path="out2841289", file_name=filename)

        ofile.encrypt()
        ofile.save_to_files()
        ofile.save_to_database()
        ofile.decrypt()
        ofile.save_to_files("decrypted.png")
        # out_bytes, tag, nonce = File.encrypt(fbytes, "test1")

        # dec_bytes = File.decrypt(BytesIO(out_bytes), "test1", tag, nonce)
        # dec_bytes = File.decrypt(BytesIO(out_bytes), "test1", tag, nonce)
        # print(len(tag))
        # print(len(nonce))
        # with open("out.png", "wb") as outfile:
        #     outfile.write(out_bytes)

        # with open("out2.png", "wb") as outfile:
        #     outfile.write(dec_bytes)

        return jsonify({"msg": "OK"}), 200

    return render_template("common/files__upload.html", form=form)
