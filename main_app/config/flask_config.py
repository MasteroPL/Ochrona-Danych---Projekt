import os

tmp = os.getenv("APP_SECRET")
if tmp is not None:
    APP_SECRET = tmp
else:
    APP_SECRET = b'\x03pF)\xff6T\xb0\xb07\xb3\xe8\x81=Y\xfd\xdd*\x0fe\xf7\xe5C\xe2'
    print("APP_SECRET not found, setting to default")

