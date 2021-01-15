import os

tmp = os.getenv("DATABASE_HOST")
if tmp is not None:
    DATABASE_HOST = tmp
else:
    DATABASE_HOST = "127.0.0.1"
    print("DATABASE_HOST not found, setting to default")

tmp = os.getenv("DATABASE_USER")
if tmp is not None:
    DATABASE_USER = tmp
else:
    DATABASE_USER = "root"
    print("DATABASE_USER not found, setting to default")

tmp = os.getenv("DATABASE_PASSWORD")
if tmp is not None:
    DATABASE_PASSWORD = tmp
else:
    DATABASE_PASSWORD = "Qwertyui123!"
    print("DATABASE_PASSWORD not found, setting to default")

tmp = os.getenv("DATABASE_DB_NAME")
if tmp is not None:
    DATABASE_DB_NAME = tmp
else:
    DATABASE_DB_NAME = "fileshare"
    print("DATABASE_DB_NAME not found, setting to default")