import os

tmp = os.getenv("PASSWORD_HASH_SALT")
if tmp is not None:
    PASSWORD_HASH_SALT = tmp
else:
    PASSWORD_HASH_SALT = "oZ#hQ"
    print("PASSWORD_HASH_SALT not found, setting to default")
