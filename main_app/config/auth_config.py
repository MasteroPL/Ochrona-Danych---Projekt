import os

tmp = os.getenv("PASSWORD_HASH_PEPPER")
if tmp is not None:
    PASSWORD_HASH_PEPPER = tmp
else:
    PASSWORD_HASH_PEPPER = "oZ#hQ"
    print("PASSWORD_HASH_PEPPER not found, setting to default")
