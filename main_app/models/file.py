from Crypto.Cipher import AES
from io import BytesIO
import os
from config import encryption_config as enc_settings
from app_init import mysql
import uuid
from werkzeug.utils import secure_filename
from models.user import User

class File:

    def __init__(self, 
        db_id:int = None, 
        file_code:str = None,
        file_bytes:BytesIO=None, 
        file_name:str=None, 
        file_path=None, 
        signature=None, 
        file_type=None, 
        is_public:bool = False, 
        file_manually_encoded:bool = False
    ):
        clazz = type(self)
        self.db_id = None
        self.file_code = file_code
        self.file_path = None
        self.file_bytes = None
        self.file_name = None
        self.signature = signature
        self.file_type = file_type
        self.nonce = None
        self.tag = None
        self.seed = None
        self.is_public = is_public
        self.file_manually_encoded = file_manually_encoded
        self.file_path = file_path
        self.file_bytes = file_bytes
        self.file_name = file_name

        if signature is not None:
            self.tag, self.nonce, self.seed = self.read_signature(signature)

    @classmethod
    def exists(clazz, id:int):
        mysql.prepare_connection()
        with mysql.cursor() as cursor:
            cursor.execute("""
                SELECT
                    id
                FROM user_file
                WHERE id=%(id)s
            """, {
                "id": id
            })

            mysql.commit()

            if cursor.rowcount > 0:
                return True
            else:
                return False

    @classmethod
    def get(clazz, id:int):
        mysql.prepare_connection()
        with mysql.cursor() as cursor:
            cursor.execute("""
                SELECT
                    *
                FROM user_file
                WHERE id=%(id)s
            """, {
                "id": id
            })

            mysql.commit()

            if cursor.rowcount == 0:
                raise ValueError("Requested file does not exist")

            # signature = row.get("file_signature", None)
            # if signature is not None:
            #     signature = signature.encode("utf-8")
            row = cursor.fetchone()

            return clazz.from_sql_row(row)

    @classmethod
    def get_by_file_code(clazz, file_code:str):
        mysql.prepare_connection()
        with mysql.cursor() as cursor:
            cursor.execute("""
                SELECT
                    *
                FROM user_file
                WHERE file_code=%(file_code)s
            """, {
                "file_code": file_code
            })

            if cursor.rowcount == 0:
                raise ValueError("Requested file does not exist")

            row = cursor.fetchone()

            return clazz.from_sql_row(row)

    @classmethod
    def from_sql_row(clazz, sql_row):
        return File(
            db_id=sql_row.get("id", None),
            file_code=sql_row.get("file_code", None),
            file_name=sql_row.get("file_name", None),
            file_path=sql_row.get("file_path", None),
            file_type=sql_row.get("file_type", None),
            is_public=sql_row.get("is_public", False),
            file_manually_encoded=sql_row.get("file_manually_encoded", False),
            signature=sql_row.get("file_signature", None)
        )

    @classmethod
    def read_signature(clazz, signature):
        if len(signature) != 40:
            raise ValueError("Invalid signature")

        tag = signature[0:16]
        nounce = signature[16:32]
        seed = signature[32:40]

        print(len(tag))

        return tag, nounce, seed

    @classmethod
    def read_file(clazz, file_path):
        with open("file_path", "wb") as source_file:
            return source_file.read()

    @classmethod
    def _encrypt(clazz, file_bytes, password_bytes):
        
        if len(password_bytes) > 32:
            raise ValueError("Password length can be at most 32")

        key = password_bytes
        while len(key) < 32:
            key += b'\0'

        cipher = AES.new(key, AES.MODE_EAX)

        cipher_text, tag = cipher.encrypt_and_digest(file_bytes)

        return cipher_text, tag, cipher.nonce

    @classmethod
    def _decrypt(clazz, file_bytes, password_bytes, tag, nonce):

        if len(password_bytes) > 32:
            raise ValueError("Password length can be at most 32")

        key = password_bytes
        while len(key) < 32:
            key += b'\0'

        cipher = AES.new(key, AES.MODE_EAX, nonce)

        decrypted = cipher.decrypt_and_verify(file_bytes, tag)
        
        return decrypted

    def encrypt(self, password:str = None):
        clazz = type(self)

        seed = os.urandom(8)
        if password is None:
            password_bytes = enc_settings.DEFAULT_ENCODING_PASSWORD + seed
        else:
            if len(password) > 24:
                raise ValueError("Maximum password length is 24 bytes")

            password_bytes = password.encode("utf-8")

            while len(password_bytes) < 24:
                password_bytes += b'\0'

            password_bytes += seed

        cipher_text, tag, nonce = clazz._encrypt(self.file_bytes, password_bytes)

        self.tag = tag
        self.nonce = nonce
        self.file_bytes = cipher_text
        self.seed = seed
        self.signature = self.tag + self.nonce + self.seed

    def decrypt(self, password:str = None):
        clazz = type(self)

        if self.file_bytes is None or self.signature is None:
            raise ValueError("File not valid for decryption")

        tag, nonce, seed = clazz.read_signature(self.signature)

        if password is None:
            password_bytes = enc_settings.DEFAULT_ENCODING_PASSWORD + seed
        else:
            if len(password) > 24:
                raise ValueError("Maximum password length is 24 bytes")

            password_bytes = password.encode("utf-8")

            while len(password_bytes) < 24:
                password_bytes += b'\0'

            password_bytes += seed

        self.file_bytes = clazz._decrypt(self.file_bytes, password_bytes, tag, nonce)

    def read_file_from_path(self):
        clazz = type(self)
        if self.file_path is None:
            raise ValueError("File path not assigned")

        self.file_bytes = clazz.read_file(self.file_path)

    def save_to_files(self, file_path:str = None):
        if file_path == None:
            file_path = self.file_path
        else:
            self.file_path = file_path

        if file_path is None:
            raise ValueError("File path not specified")

        with open(file_path, "wb") as out_file:
            out_file.write(self.file_bytes)

    def save_to_database(self, commit=True):
        mysql.prepare_connection()
        with mysql.cursor() as cursor:
            if self.db_id is None:
                cursor.execute("""
                    INSERT INTO user_file (
                        file_path, 
                        file_code,
                        file_name, 
                        is_public, 
                        file_type, 
                        file_manually_encoded, 
                        file_signature
                    ) VALUES (
                        %(file_path)s, %(file_code)s, %(file_name)s, %(is_public)s, %(file_type)s, %(file_manually_encoded)s, %(file_signature)s
                    )
                """, {
                    "file_path": self.file_path,
                    "file_code": self.file_code,
                    "file_name": self.file_name,
                    "is_public": self.is_public,
                    "file_type": self.file_type,
                    "file_manually_encoded": self.file_manually_encoded,
                    "file_signature": self.signature
                })
                if commit:
                    mysql.commit()

                self.db_id = cursor.lastrowid

            else:
                cursor.execute("""
                    UPDATE user_file
                    SET
                        file_path=%(file_path)s,
                        file_code=%(file_code)s,
                        file_name=%(file_name)s,
                        is_public=%(is_public)s,
                        file_type=%(file_type)s,
                        file_manually_encoded=%(file_manually_encoded)s,
                        file_signature=%(file_signature)s
                    WHERE id=%(id)s
                """, {
                    "id": self.db_id,
                    "file_path": self.file_path,
                    "file_code": self.file_code,
                    "file_name": self.file_name,
                    "is_public": self.is_public,
                    "file_type": self.file_type,
                    "file_manually_encoded": self.file_manually_encoded,
                    "file_signature": self.signature
                })
                if commit:
                    mysql.commit()

    def assign_user(self, user:User, access_type, commit=True):
        if access_type != "OWNER" and access_type != "EDITOR" and access_type != "READER":
            raise ValueError("Invalid access_type")

        if user.id is None:
            raise ValueError("Invalid user")

        if FileAssignment.exists(user, self):
            raise ValueError("Assignment already exists")

        raise Exception()

        assignment = FileAssignment(
            access_type=access_type,
            user=user,
            file=self
        )
        assignment.save(commit)

    def reassign_user(self, user:User, access_type):
        if access_type != "OWNER" and access_type != "EDITOR" and access_type != "READER":
            raise ValueError("Invalid access_type")

        assignment = FileAssignment.get_assignment(user, self)
        if assignment is None:
            raise ValueError("Assignment doesn't exist")

        assignment.access_type = access_type
        assignment.save()

    def remove_user(self, user:User):
        assignment = FileAssignment.get_assignment(user, self)
        if assignment is None:
            raise ValueError("Assignment doesn't exist")

        assignment.delete()

    def assignment_exists(self, user:User):
        return FileAssignment.exists(user, self)

    def get_assignment(self, user:User):
        return FileAssignment.get_assignment(user, self)

    def generate_unique_path(self, base_path:str):
        unique_filename = str(uuid.uuid4())
        self.file_code = unique_filename
        path = base_path + unique_filename

        while(os.path.isfile(path)):
            unique_filename = str(uuid.uuid4())
            path = base_path + unique_filename

        self.file_path = path

    @classmethod
    def from_file(clazz, file):
        
        file_name = secure_filename(file.filename)

        if len(file_name) > 60:
            file_name = file_name[0:50] + "___" + file_name[-10:]

        fbytes = file.stream._file.read()
        mime_type = file.mimetype

        if mime_type == "text/plain":
            file_type = "TEXT"
        else:
            file_type = "BLOB"

        return File(
            file_bytes=fbytes,
            file_name=file_name,
            file_type=file_type
        )



class FileAssignment:

    def __init__(self,
        id:int = None,
        access_type:str = None,
        user:User = None,
        file:File = None
    ):
        self.id = id
        self.access_type = access_type
        self.user = user
        self.file = file

    @classmethod
    def exists(clazz, user:User, file:File):
        mysql.prepare_connection()
        with mysql.cursor() as cursor:
            cursor.execute("""
                SELECT id
                FROM user__user_file__assignment
                WHERE user_id=%(user_id)s AND user_file_id=%(user_file_id)s
            """, {
                "user_id": user.id,
                "user_file_id": file.db_id
            })

            return cursor.rowcount > 0

    def save(self, commit=True):
        clazz = type(self)
        mysql.prepare_connection()
        with mysql.cursor() as cursor:
            if self.id is None:
                cursor.execute("""
                    INSERT INTO user__user_file__assignment (
                        user_id,
                        user_file_id,
                        access_type
                    ) VALUES (
                        %(user_id)s, %(user_file_id)s, %(access_type)s
                    )
                """, {
                    "user_id": self.user.id,
                    "user_file_id": self.file.db_id,
                    "access_type": self.access_type
                })

                if commit:
                    mysql.commit()

                self.id = cursor.lastrowid

            else:
                cursor.execute("""
                    UPDATE user__user_file__assignment
                    SET
                        user_id=%(user_id)s,
                        user_file_id=%(user_file_id)s,
                        access_type=%(access_type)s
                    WHERE id=%(id)s
                """, {
                    "id": self.id,
                    "user_id": self.user.id,
                    "user_file_id": self.file.db_id,
                    "access_type": self.access_type
                })

                if commit:
                    mysql.commit()


    @classmethod
    def from_sql_row(clazz, sql_row):
        user = User(
            id=sql_row["user_id"],
            login=sql_row["user_login"]
        )
        file = File(
            db_id=sql_row["file_id"],
            file_code=sql_row["file_code"],
            file_path=sql_row["file_path"],
            file_name=sql_row["file_name"],
            is_public=sql_row["file_is_public"],
            file_type=sql_row["file_type"],
            file_manually_encoded=sql_row["file_manually_encoded"],
            signature=sql_row["file_signature"]
        )

        return FileAssignment(
            id=sql_row["assignment_id"],
            access_type=sql_row["assignment_access_type"],
            user=user,
            file=file
        )

    @classmethod
    def get_assignment(clazz, user:User, file:File):
        mysql.prepare_connection()
        with mysql.cursor() as cursor:
            cursor.execute("""
                SELECT
                    uufa.id AS 'assignment_id',
                    uufa.access_type AS 'assignment_access_type'
                FROM user__user_file__assignment uufa
                WHERE user_id=%(user_id)s AND user_file_id=%(user_file_id)s
            """, {
                "user_id": user.id,
                "user_file_id": file.db_id
            })

            if cursor.rowcount == 0:
                return None

            row = cursor.fetchone()

            return FileAssignment(
                id=row["assignment_id"],
                access_type=row["assignment_access_type"],
                user=user,
                file=file
            )

    @classmethod
    def get_assignment_from_ids(clazz, user_id:int, file_id:int):
        mysql.prepare_connection()
        with mysql.cursor() as cursor:
            cursor.execute("""
                SELECT
                    uufa.id AS 'assignment_id',
                    uufa.access_type AS 'assignment_access_type',

                    u.id AS 'user_id',
                    u.login AS 'user_login',

                    uf.id AS 'file_id',
                    uf.file_code AS 'file_code',
                    uf.file_path AS 'file_path',
                    uf.file_name AS 'file_name',
                    uf.is_public AS 'file_is_public',
                    uf.file_type AS 'file_type',
                    uf.file_manually_encoded AS 'file_manually_encoded',
                    uf.file_signature AS 'file_signature'
                FROM user__user_file__assignment uufa
                JOIN user u ON u.id = uufa.user_id
                JOIN user_file uf ON uf.id = uufa.user_file_id
                WHERE user_id=%(user_id)s AND user_file_id=%(user_file_id)s
            """, {
                "user_id": user.id,
                "user_file_id": file.db_id
            })

            if cursor.rowcount == 0:
                return None

            row = cursor.fetchone()

            return clazz.from_sql_row(row)

    @classmethod
    def get_user_assignments(clazz, user:User):
        mysql.prepare_connection()
        with mysql.cursor() as cursor:
            cursor.execute("""
                SELECT
                    uufa.id AS 'assignment_id',
                    uufa.access_type AS 'assignment_access_type',

                    u.id AS 'user_id',
                    u.login AS 'user_login',

                    uf.id AS 'file_id',
                    uf.file_code AS 'file_code',
                    uf.file_path AS 'file_path',
                    uf.file_name AS 'file_name',
                    uf.is_public AS 'file_is_public',
                    uf.file_type AS 'file_type',
                    uf.file_manually_encoded AS 'file_manually_encoded',
                    uf.file_signature AS 'file_signature'
                FROM user__user_file__assignment uufa
                JOIN user u ON u.id = uufa.user_id
                JOIN user_file uf ON uf.id = uufa.user_file_id
                WHERE user_id=%(user_id)s
            """, {
                "user_id": user.id
            })

            rows = cursor.fetchall()

            result = []
            for row in rows:
                result.append(clazz.from_sql_row(row))

            return result

    @classmethod
    def get_file_assignments(clazz, file:File):
        mysql.prepare_connection()
        with mysql.cursor() as cursor:
            cursor.execute("""
                SELECT
                    uufa.id AS 'assignment_id',
                    uufa.access_type AS 'assignment_access_type',

                    u.id AS 'user_id',
                    u.login AS 'user_login',

                    uf.id AS 'file_id',
                    uf.file_code AS 'file_code',
                    uf.file_path AS 'file_path',
                    uf.file_name AS 'file_name',
                    uf.is_public AS 'file_is_public',
                    uf.file_type AS 'file_type',
                    uf.file_manually_encoded AS 'file_manually_encoded',
                    uf.file_signature AS 'file_signature'
                FROM user__user_file__assignment uufa
                JOIN user u ON u.id = uufa.user_id
                JOIN user_file uf ON uf.id = uufa.user_file_id
                WHERE user_file_id=%(user_file_id)s
            """, {
                "user_file_id": file.db_id
            })

            rows = cursor.fetchall()

            result = []
            for row in rows:
                result.append(clazz.from_sql_row(row))

            return result
            
    def delete(self, commit=True):
        mysql.prepare_connection()
        with mysql.cursor() as cursor:
            cursor.execute("""
                DELETE FROM user__user_file__assignment
                WHERE user__user_file__assignment.id=%(id)s
            """, {
                "id": self.id
            })
            if commit:
                cursor.commit()
            self.id = None

