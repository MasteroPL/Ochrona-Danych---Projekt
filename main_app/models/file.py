from Crypto.Cipher import AES
from io import BytesIO
import os
from config import encryption_config as enc_settings
from app_init import mysql

class File:

    def __init__(self, db_id:int = None, file_bytes:BytesIO=None, file_extension:str = None, file_name:str=None, file_path=None, signature=None, file_type=None, is_public:bool = False, file_manually_encoded:bool = False):
        clazz = type(self)
        self.db_id = None
        self.file_path = None
        self.file_bytes = None
        self.file_name = None
        self.signature = signature
        self.file_type = file_type
        self.file_extension = file_extension
        self.nonce = None
        self.tag = None
        self.seed = None
        self.is_public = is_public
        self.file_manually_encoded = file_manually_encoded

        if file_path is not None:
            self.file_path = file_path

        if file_bytes is not None and file_name is not None:
            self.file_bytes = file_bytes
            self.file_name = file_name
        elif self.file_path != None:
            try:
                self.file_bytes = clazz.ReadFile(self.file_path)
            except:
                self.file_bytes = None

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

            row = cursor.fetchone()
            # signature = row.get("file_signature", None)
            # if signature is not None:
            #     signature = signature.encode("utf-8")

            return File(
                db_id=row.get("id", None),
                file_name=row.get("file_name", None),
                file_path=row.get("file_path", None),
                file_type=row.get("file_type", None),
                file_extension=row.get("file_extension", None),
                is_public=row.get("is_public", False),
                file_manually_encoded=row.get("file_manually_encoded", False),
                signature=row.get("file_signature", None)
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

    def save_to_files(self, file_path:str = None):
        if file_path == None:
            file_path = self.file_path
        else:
            self.file_path = file_path

        if file_path is None:
            raise ValueError("File path not specified")

        with open(file_path, "wb") as out_file:
            out_file.write(self.file_bytes)

    def save_to_database(self):
        mysql.prepare_connection()
        with mysql.cursor() as cursor:
            if self.db_id is None:
                cursor.execute("""
                    INSERT INTO user_file (
                        file_path, 
                        file_name, 
                        file_extension, 
                        is_public, 
                        file_type, 
                        file_manually_encoded, 
                        file_signature
                    ) VALUES (
                        %(file_path)s, %(file_name)s, %(file_extension)s, %(is_public)s, %(file_type)s, %(file_manually_encoded)s, %(file_signature)s
                    )
                """, {
                    "file_path": self.file_path,
                    "file_name": self.file_name,
                    "file_extension": self.file_extension,
                    "is_public": self.is_public,
                    "file_type": "TEXT" if self.file_extension == "TXT" else "BLOB",
                    "file_manually_encoded": self.file_manually_encoded,
                    "file_signature": self.signature
                })
                mysql.commit()

            else:
                cursor.execute("""
                    UPDATE user_file
                    SET
                        file_path=%(file_path)s,
                        file_name=%(file_name)s,
                        file_extension=%(file_extension)s,
                        is_public=%(is_public)s,
                        file_type=%(file_type)s,
                        file_manually_encoded=%(file_manually_encoded)s,
                        file_signature=%(file_signature)s
                    WHERE id=%(id)s
                """, {
                    "id": self.db_id,
                    "file_path": self.file_path,
                    "file_name": self.file_name,
                    "file_extension": self.file_extension,
                    "is_public": self.is_public,
                    "file_type": self.file_type,
                    "file_manually_encoded": self.file_manually_encoded,
                    "file_signature": self.signature
                })
                mysql.commit()
