import os

tmp = os.getenv("USER_FILE_BASE_PATH")
if tmp is not None:
    USER_FILE_BASE_PATH = tmp
else:
    USER_FILE_BASE_PATH = "protected_files/user_files/"
    print("USER_FILE_BASE_PATH not found, setting to default")
