import config as settings
import re
from app_init import mysql, login_manager
from passlib.hash import pbkdf2_sha256
from flask_login import UserMixin

class User(UserMixin):

    def __init__(self, 
        id:int=None, 
        login:str=None
    ):
        self.id = id
        self.login = login

    def to_json(self):
        return {
            "id": self.id,
            "login": self.login
        }

    def get_id(self):
        return str(self.id)

    def validate(self):
        clazz = type(self)
        validation_cycle = [
            {
                "field_name": "login",
                "field_value": self.login,
                "field_validator": clazz.validate_login
            }
        ]

        response = {
            "valid": True,
            "errors": { }
        }
        for validation in validation_cycle:
            tmp_resp = validation["field_validator"](validation["field_value"])

            if not tmp_resp["valid"]:
                response["valid"] = False
                response["errors"][validation["field_name"]] = tmp_resp["error"]
            else:
                setattr(self, validation["field_name"], tmp_resp["value"])

        return response

    @classmethod
    def validate_login(clazz, login:str):
        if len(login) < 3 or len(login) > 20:
            return {
                "valid": False,
                "error": "Login musi zawierać pomiędzy 3 a 20 znaków"
            }

        rex = re.compile("[a-zA-Z0-9]+")
        if not rex.fullmatch(login):
            return {
                "valid": False,
                "error": "Login może zawierać tylko małe litery, wielkie litery i cyfry"
            }

        return {
            "valid": True,
            "value": login
        }

    @classmethod
    def validate_password(clazz, password:str):
        if len(password) < 8 or len(password) > 32:
            return {
                "valid": False,
                "error": "Hasło musi zawierać pomiędzy 8 a 32 znaków"
            }
        
        return {
            "valid": True,
            "value": password
        }

    @classmethod
    def login_exists(clazz, login:str):
        mysql.prepare_connection()
        with mysql.cursor() as cursor:
            cursor.execute("""
                SELECT id FROM user WHERE login=%(login)s
            """, {
                "login": login
            })

            return cursor.rowcount > 0

    @classmethod
    def get_by_id(clazz, id:int):
        mysql.prepare_connection()
        with mysql.cursor() as cursor:
            cursor.execute("""
                SELECT id, login FROM user WHERE id=%(id)s 
            """, {
                "id": id
            })

            if cursor.rowcount == 0:
                raise UserDoesNotExistError()
            
            row = cursor.fetchone()
            return User(
                id=row["id"],
                login=row["login"]
            )

    @classmethod
    def get_by_login(clazz, login:str):
        mysql.prepare_connection()
        with mysql.cursor() as cursor:
            cursor.execute("""
                SELECT id, login FROM user WHERE login=%(login)s 
            """, {
                "login": login
            })

            if cursor.rowcount == 0:
                raise UserDoesNotExistError()
            
            row = cursor.fetchone()
            return User(
                id=row["id"],
                login=row["login"]
            )


    def register(self, password:str):
        clazz = type(self)

        valid_password = clazz.validate_password(password)
        if not valid_password["valid"]:
            raise ValueError("Invalid password value")

        mysql.prepare_connection()
        with mysql.cursor() as cursor:
            if clazz.login_exists(self.login):
                raise UserAlreadyRegisteredError()

            # Hashowanie zawiera z pudełka sól (16 bajtów losowo generowanych przez bibliotekę, taka implementacja jest zalecana)
            # oraz wielokrotne hashowanie (29000 rund domyślnie, można zmienić)
            password_hash = pbkdf2_sha256.hash(password + settings.PASSWORD_HASH_PEPPER)

            cursor.execute("""
                INSERT INTO user (
                    login, password_hash
                ) VALUES (
                    %(login)s, %(password_hash)s
                )
            """, {
                "login": self.login,
                "password_hash": password_hash
            })

            mysql.commit()

            self.id = cursor.lastrowid

    def verify_password(self, password:str):
        if self.id is None:
            raise UserDoesNotExistError()

        mysql.prepare_connection()
        with mysql.cursor() as cursor:
            cursor.execute("""
                SELECT id, password_hash
                FROM user
                WHERE id=%(id)s
            """, {
                "id": self.id
            })

            if cursor.rowcount == 0:
                raise UserDoesNotExistError()

            row = cursor.fetchone()
            pass_hash = row["password_hash"]

            return pbkdf2_sha256.verify(password + settings.PASSWORD_HASH_PEPPER, pass_hash)




class UserError(Exception):
    pass

class UserDoesNotExistError(UserError):
    pass

class UserAlreadyRegisteredError(UserError):
    pass



#
# LOGIN MANAGER INIT
#

@login_manager.user_loader
def load_user(user_id):
    if user_id is None:
        return None

    try:
        return User.get_by_id(user_id)
    except UserDoesNotExistError:
        return None
