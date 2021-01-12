import pymysql

class MySQL:

    def __init__(self, user:str, password: str, host:str, database:str, autocommit:bool = False):
        self.config = {
            "user": user,
            "password": password,
            "host": host,
            "db": database,
            "charset": "utf8mb4",
            "cursorclass": pymysql.cursors.DictCursor,
            "autocommit": autocommit
        }

        self.connection = pymysql.connect(**self.config)

    def connection_is_open(self):
        return self.connection.open

    def prepare_connection(self):
        if not self.connection_is_open():
            self.connection = mysql.connect(**self.config)

    # Te 3 funkcje przepisane jako udogodnienie, ponieważ są najczęściej używane
    def cursor(self):
        return self.connection.cursor()

    def commit(self):
        self.connection.commit()

    def rollback(self):
        self.connection.rollback()