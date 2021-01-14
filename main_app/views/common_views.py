from app_init import app, mysql
from flask import render_template, request, session, jsonify, send_from_directory, abort, Response, redirect
from flask_login import login_required, current_user
import config as settings
from werkzeug.utils import secure_filename
import os
from models.file import File, FileAssignment, FileDoesNotExistError, FileError, UserAlreadyAssignedError, FileAssignmentDoesNotExistError
from models.user import User, UserDoesNotExistError
from io import BytesIO
import jwt
import datetime
from Crypto.Cipher import AES

@app.route("/", methods=["GET"])
def index():
    if current_user.is_authenticated:
        return redirect("/files/")
    return redirect("/login/")

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

        if form.password.data == '' or form.password.data == None:
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
            return render_template("common/files__new_note.html",
                form = form,
                global_info = "Wystąpił błąd serwera"
            )
        

        return redirect("/files/")

    return render_template("common/files__upload.html", form=form)

from forms import NewNoteForm
@app.route("/files/new-note/", methods=["GET", "POST"])
@login_required
def files_new_note():
    form = NewNoteForm()

    if form.validate_on_submit():
        password = form.password.data
        if password == '':
            password = None

        ofile = File(
            file_bytes=form.note.data.encode("utf-8"),
            file_name=form.title.data,
            file_type="TEXT",
            file_mime_type="text/plain",
            is_public=form.is_public.data
        )
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
            return render_template("common/files__new_note.html",
                form = form,
                global_info = "Wystąpił błąd serwera"
            )

        return redirect("/files/")


    return render_template("common/files__new_note.html",
        form = form
    )

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
            form=form,
            is_authenticated=current_user.is_authenticated
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
            file_code=file.file_code,
            is_authenticated=current_user.is_authenticated
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
                    file_content_lines=lines,
                    is_authenticated=current_user.is_authenticated
                )
            except ValueError:
                form.password.errors.append("Nieprawidłowe hasło")

        return render_template("common/files__show__decrypt.html",
            form=form,
            is_authenticated=current_user.is_authenticated
        )

    elif request.method == "GET":
        file.read_file_from_path()
        file.decrypt()
        text = file.file_bytes.decode("utf-8")
        lines = text.split("\n")
        return render_template("common/files__show.html",
            file_name=file.file_name,
            file_content_lines=lines,
            is_authenticated=current_user.is_authenticated
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

    if assignment.access_type != "OWNER":
        abort(404)

    form = EmptyForm()

    if form.validate_on_submit():
        file.delete()
        return redirect("/files/")
    
    return render_template("/common/files__delete.html", 
        form=form,
        file_name=file.file_name
    )
        

from forms import FileShareForm
from forms import FileUnshareForm
@app.route("/files/share/<string:file_code>", methods=["GET", "POST"])
@login_required
def file_share(file_code):
    try:
        file = File.get_by_file_code(file_code)
    except FileDoesNotExistError:
        abort(404)

    assignment = FileAssignment.get_assignment(current_user, file)

    if assignment is None or assignment.access_type != "OWNER":
        abort(404)

    form = FileShareForm()
    if form.validate_on_submit():
        try:
            user = User.get_by_login(form.username.data)

            file.assign_user(user, form.access_type.data)
        except UserDoesNotExistError:
            form.username.errors.append("Nieprawidłowa nazwa użytkownika")

        except UserAlreadyAssignedError:
            form.username.errors.append("Ten użytkownik ma już udostępniony ten plik")

    shares = FileAssignment.get_file_assignments(file)

    shares_json = []
    for share in shares:
        if share.access_type != "OWNER":
            shares_json.append(share.to_json())

    form_unshare = FileUnshareForm()
    form_change_status = FileChangePublicStatusForm()
    return render_template("common/files__share.html",
        shares=shares_json,
        form=form,
        file_name=file.file_name,
        file_code=file_code,
        form_unshare=form_unshare,
        file_is_public=file.is_public,
        form_change_status=form_change_status
    )

@app.route("/files/unshare/<string:file_code>", methods=["POST"])
@login_required
def file_unshare(file_code):
    try:
        file = File.get_by_file_code(file_code)
    except FileDoesNotExistError:
        abort(404)

    assignment = FileAssignment.get_assignment(current_user, file)

    if assignment is None or assignment.access_type != "OWNER":
        abort(404)

    form = FileUnshareForm()
    if form.validate_on_submit():
        try:
            user = User.get_by_id(form.user_id.data)

            file.remove_user(user)

            return redirect("/files/share/" + file_code)
        except UserDoesNotExistError:
            form.user_id.errors.append("Użytkownik nie istnieje")

        except FileAssignmentDoesNotExistError:
            form.user_id.errors.append("Użytkownik nieprzypisany do tego pliku")

    return redirect("/files/share/" + file_code + "?info=Wyst%C4%85pi%C5%82%20b%C5%82%C4%85d%20przy%20pr%C3%B3bie%20usuni%C4%99cia%20udost%C4%99pnienia")

from forms import FileChangePublicStatusForm
@app.route("/files/change-public-status/<string:file_code>", methods=["POST"])
@login_required
def file_change_public_status(file_code):
    try:
        file = File.get_by_file_code(file_code)
    except FileDoesNotExistError:
        abort(404)

    assignment = FileAssignment.get_assignment(current_user, file)

    if assignment is None or assignment.access_type != "OWNER":
        abort(404)

    form = FileChangePublicStatusForm()
    if form.validate_on_submit():
        file.is_public = form.is_public.data
        file.save_to_database()
        return redirect("/files/share/" + file_code)

    abort(404)

@app.route("/files/remove-my-assignment/<string:file_code>", methods=["GET", "POST"])
@login_required
def file_remove_my_assignment(file_code):
    try:
        file = File.get_by_file_code(file_code)
    except FileDoesNotExistError:
        abort(404)

    assignment = FileAssignment.get_assignment(current_user, file)

    if assignment is None:
        abort(404)
    
    if assignment.access_type == "OWNER":
        abort(403)

    form = EmptyForm()
    if form.validate_on_submit():
        try:
            file.remove_user(current_user)

            return redirect("/files/")
        except FileAssignmentDoesNotExistError:
            abort(404)

    return render_template("common/files__remove_my_assignment.html", form=form)


from forms import FileRenameForm
@app.route("/files/rename/<string:file_code>", methods=["GET", "POST"])
@login_required
def file_rename(file_code):
    try:
        file = File.get_by_file_code(file_code)
    except FileDoesNotExistError:
        abort(404)
        
    assignment = FileAssignment.get_assignment(current_user, file)
    if assignment is None or (assignment.access_type != "OWNER" and assignment.access_type != "EDITOR"):
        abort(404)

    form = FileRenameForm()
    if form.validate_on_submit():
        assignment.file.file_name = form.new_name.data
        assignment.file.save_to_database()

        return redirect("/files/")

    elif request.method == "GET":
            form.new_name.data = file.file_name

    return render_template("common/files__rename.html", form=form, file_name=assignment.file.file_name)
    

from forms import TextFileEditForm
@app.route("/files/edit/<string:file_code>", methods=["GET", "POST"])
@login_required
def file_edit(file_code):
    try:
        file = File.get_by_file_code(file_code)
    except FileDoesNotExistError:
        abort(404)

    assignment = FileAssignment.get_assignment(current_user, file)
    if assignment is None or (assignment.access_type != "OWNER" and assignment.access_type != "EDITOR"):
        abort(404)

    file_size = os.stat(file.file_path).st_size
    if file_size > 1048576:
        return render_template("common/files__edit__unavailable.html",
            file_name=file.file_name
        )

    if file.file_manually_encoded:
        form = FilePasswordVerificationForm()
        if form.validate_on_submit():
            file.read_file_from_path()
            try:
                file.decrypt(form.password.data)
                text = file.file_bytes.decode("utf-8")

                edit_form = TextFileEditDecryptedForm()
                edit_form.content.data = text

                cipher = AES.new(settings.DECRYPTION_TOKEN_PASSWORD_ENCODING_KEY, AES.MODE_EAX)
                cipher_text, tag = cipher.encrypt_and_digest(form.password.data.encode("utf-8"))
                bytes_arr = tag + cipher.nonce
                bytes_hex = bytes_arr.hex()

                exp_at = datetime.datetime.utcnow() + datetime.timedelta(seconds=settings.DECRYPTION_TOKEN_JWT_DURATION)
                token = jwt.encode({
                    "type": "DECRYPTION",
                    "file_code": file.file_code,
                    "password": cipher_text.hex(),
                    "signature": bytes_hex,
                    "exp": exp_at
                }, key=settings.DECRYPTION_TOKEN_JWT_SECRET, algorithm="HS256")
                edit_form.decrypt_token.data = token

                return render_template("common/files__edit__decrypted.html",
                    file_name=file.file_name,
                    file_code=file.file_code,
                    form=edit_form
                )
            except ValueError:
                form.password.errors.append("Nieprawidłowe hasło")

        return render_template("common/files__edit__decrypt.html",
            form=form,
            file_name=file.file_name
        )

    else:
        file.read_file_from_path()
        file.decrypt()
        text = file.file_bytes.decode("utf-8")
        edit_form = TextFileEditForm()

        if edit_form.validate_on_submit():
            file.file_bytes = edit_form.content.data.encode("utf-8")
            file.encrypt()
            file.save_to_files()
            file.save_to_database()

            return redirect("/files/")
    
        elif request.method == "GET":
            edit_form.content.data = text


        return render_template("common/files__edit.html",
            file_name=file.file_name,
            file_code=file.file_code,
            form=edit_form,
        )

from forms import TextFileEditDecryptedForm
@app.route("/files/edit-decrypted/<string:file_code>", methods=["POST"])
@login_required
def files_save_edit(file_code):
    try:
        file = File.get_by_file_code(file_code)
    except FileDoesNotExistError:
        abort(404)

    assignment = FileAssignment.get_assignment(current_user, file)
    if assignment is None or (assignment.access_type != "OWNER" and assignment.access_type != "EDITOR"):
        abort(404)

    password = None

    if not file.file_manually_encoded:
        abort(404)

    form = TextFileEditDecryptedForm()
    form_valid = form.validate_on_submit()

    auth_full = form.decrypt_token.data
    if auth_full is None:
        abort(404)
    
    try:
        decoded = jwt.decode(auth_full, key=settings.DECRYPTION_TOKEN_JWT_SECRET, algorithms="HS256")
    except jwt.ExpiredSignatureError:
        return render_template("/files/files__edit__signature_expired.html")
    except jwt.InvalidTokenError as e:
        raise e
        abort(404)

    if decoded["type"] is None or decoded["file_code"] is None or decoded["signature"] is None or decoded["password"] is None:
        abort(404)

    if decoded["type"] != "DECRYPTION" or decoded["file_code"] != file.file_code:
        abort(404)

    try:
        signature = decoded["signature"]
        sign_bytes = bytes.fromhex(signature)
        tag = sign_bytes[0:16]
        nonce = sign_bytes[16:32]

        cipher = AES.new(settings.DECRYPTION_TOKEN_PASSWORD_ENCODING_KEY, AES.MODE_EAX, nonce)
        password_bytes = cipher.decrypt_and_verify(bytes.fromhex(decoded["password"]), tag)
        password = password_bytes.decode("utf-8")

        file.read_file_from_path()
        file.decrypt(password)
    except Exception as e:
        raise e
        abort(404)

    if form_valid:
        file.file_bytes = form.content.data.encode("utf-8")
        file.encrypt(password)
        file.save_to_files()
        file.save_to_database()

        return redirect("/files/")

    exp_at = datetime.datetime.utcnow() + datetime.timedelta(seconds=settings.DECRYPTION_TOKEN_JWT_DURATION)
    token = jwt.encode({
        "type": "DECRYPTION",
        "file_code": file.file_code,
        "password": decoded["password"],
        "signature": decoded["signature"],
        "exp": exp_at
    }, key=settings.DECRYPTION_TOKEN_JWT_SECRET, algorithm="HS256")
    form.decrypt_token.data = token

    return render_template("common/files__edit__decrypted.html",
        form=form,
        file_code=file.file_code,
        file_name=file.file_name
    )

        


@app.route("/debug/", methods=["GET"])
def debug():
    assignment = FileAssignment.get_assignment_from_ids(1, 12)

    file = assignment.file
    file.read_file_from_path()
    file.decrypt()
    file.save_to_files("test.drawio")

    return "OK", 200