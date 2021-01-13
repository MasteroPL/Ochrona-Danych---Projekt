from app_init import app, mysql
from flask import render_template, request, session, jsonify, send_from_directory, abort, Response, redirect
from flask_login import login_required, current_user
import config as settings
from werkzeug.utils import secure_filename
import os
from models.file import File, FileAssignment, FileDoesNotExistError, FileError
from models.user import User
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

        try:
            ofile = File.from_file(f)
        except Exception as e:
            form.upload_file.errors.append("Niepoprawny plik")
            return render_template("common/files__upload.html", form=form)

        if form.password.data == '':
            password = None
        else:
            password = form.password.data

        ofile.is_public = form.is_public.data
        ofile.encrypt(password)
        ofile.generate_unique_path(settings.USER_FILE_BASE_PATH)
        ofile.save_to_files()

        try:
            ofile.save_to_database(commit=False)
            ofile.assign_user(current_user, "OWNER", commit=False)
            mysql.commit()
        
        except Exception as e:
            mysql.rollback()
            ofile.delete()
            return jsonify({"msg": str(e)}), 500
        

        return redirect("/files/")

    return render_template("common/files__upload.html", form=form)

@app.route("/files/", methods=["GET"])
@login_required
def files():
    user = current_user

    assignments = FileAssignment.get_user_assignments(user)

    my_assignments = []
    shared_assignments = []

    for assignment in assignments:
        if assignment.access_type == "OWNER":
            my_assignments.append(assignment.to_json())
        else:
            shared_assignments.append(assignment.to_json())

    return render_template("common/files.html", 
        my_assignments=my_assignments,
        shared_assignments=shared_assignments
    )

from forms import FilePasswordVerificationForm
@app.route("/files/download/<string:file_code>", methods=["GET", "POST"])
def files_download(file_code):
    try:
        file = File.get_by_file_code(file_code)
    except FileDoesNotExistError:
        abort(404)

    # Autoryzacja dostępu do pliku
    if not file.is_public:
        if not current_user.is_authenticated:
            abort(404)
        
        assignment = FileAssignment.get_assignment(current_user, file)
        if assignment is None:
            abort(404)

    if file.file_manually_encoded:
        form = FilePasswordVerificationForm()

        if form.validate_on_submit():
            file.read_file_from_path()
            try:
                file.decrypt(form.password.data)
                return Response(file.file_bytes, mimetype=file.file_mime_type, headers={
                    "Content-Disposition": "attachment;filename=" + file.file_name
                })
            except ValueError:
                form.password.errors.append("Nieprawidłowe hasło")

        return render_template("common/files__download__decrypt.html",
            form=form
        )

    elif request.method == "GET":
        file.read_file_from_path()
        file.decrypt()
        return Response(file.file_bytes, mimetype=file.file_mime_type, headers={
            "Content-Disposition": "attachment;filename=" + file.file_name
        })

    else:
        abort(403)

@app.route("/files/show/<string:file_code>", methods=["GET", "POST"])
def files_show(file_code):
    try:
        file = File.get_by_file_code(file_code)
    except FileDoesNotExistError:
        abort(404)

    if file.file_type != "TEXT":
        abort(404)

    # Autoryzacja dostępu do pliku
    if not file.is_public:
        if not current_user.is_authenticated:
            abort(404)
        
        assignment = FileAssignment.get_assignment(current_user, file)
        if assignment is None:
            abort(404)

    file_size = os.stat(file.file_path).st_size
    if file_size > 1048576:
        return render_template("common/files__show__unavailable.html",
            file_code=file.file_code
        )

    if file.file_manually_encoded:
        form = FilePasswordVerificationForm()

        if form.validate_on_submit():
            file.read_file_from_path()
            try:
                file.decrypt(form.password.data)
                text = file.file_bytes.decode("utf-8")
                lines = text.split("\n")
                return render_template("common/files__show.html",
                    file_name=file.file_name,
                    file_content_lines=lines
                )
            except ValueError:
                form.password.errors.append("Nieprawidłowe hasło")

        return render_template("common/files__show__decrypt.html",
            form=form
        )

    elif request.method == "GET":
        file.read_file_from_path()
        file.decrypt()
        text = file.file_bytes.decode("utf-8")
        lines = text.split("\n")
        return render_template("common/files__show.html",
            file_name=file.file_name,
            file_content_lines=lines
        )

    else:
        abort(403)


from forms import EmptyForm
@app.route("/files/delete/<string:file_code>", methods=["GET", "POST"])
@login_required
def files_delete(file_code):
    try:
        file = File.get_by_file_code(file_code)
    except FileDoesNotExistError:
        abort(404)

    assignment = FileAssignment.get_assignment(current_user, file)
    if assignment is None:
        abort(404)

    if assignment.access_type != "OWNER" and assignment.access_type != "EDITOR":
        abort(404)

    if file.file_manually_encoded and assignment.access_type != "OWNER":
        form = FilePasswordVerificationForm()

        if form.validate_on_submit():
            file.read_file_from_path()
            try:
                file.decrypt(form.password.data)
            except ValueError:
                form.password.errors.append("Nieprawidłowe hasło")
                return render_template("/common/files__delete__decrypt.html", 
                    form=form,
                    file_name=file.file_name
                )

            file.file_bytes = None
            file.delete()
            return redirect("/files/")

        return render_template("/common/files__delete__decrypt.html", 
            form=form,
            file_name=file.file_name
        )

    else:
        form = EmptyForm()

        if form.validate_on_submit():
            file.delete()
            return redirect("/files/")
        
        return render_template("/common/files__delete.html", 
            form=form,
            file_name=file.file_name
        )
        

@app.route("/files/share/<string:file_code>")
@login_required
def file_share(file_code):
    try:
        file = File.get_by_file_code(file_code)
    except FileDoesNotExistError:
        abort(404)

    assignment = FileAssignment.get_assignment(current_user, file)

    if assignment is None or assignment.access_type != "OWNER":
        abort(404)

    

    


@app.route("/debug/", methods=["GET"])
def debug():
    assignment = FileAssignment.get_assignment_from_ids(1, 12)

    file = assignment.file
    file.read_file_from_path()
    file.decrypt()
    file.save_to_files("test.drawio")

    return "OK", 200