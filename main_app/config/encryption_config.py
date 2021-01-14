import os

tmp = os.getenv("DEFAULT_ENCODING_PASSWORD")
if tmp is not None:
    DEFAULT_ENCODING_PASSWORD = tmp
else:
    DEFAULT_ENCODING_PASSWORD = b'\x95%\xe9\xeb\x15\xff\xb6\x19\xd1\xe6\xe5?\x07C\xebh\xb9\x82r\xbf\x1c\xed\xaa\x0f'
    print("DEFAULT_ENCODING_PASSWORD not found, setting to default")

tmp = os.getenv("DECRYPTION_TOKEN_JWT_SECRET")
if tmp is not None:
    DECRYPTION_TOKEN_JWT_SECRET = tmp
else:
    DECRYPTION_TOKEN_JWT_SECRET = b'\x13G\xc8\xdb\x13\x16\xbdFXz\xa7\x13\x8f>\x8c\xd0\x97o \x13(\xd0/`'
    print("DECRYPTION_TOKEN_JWT_SECRET not found, setting to default")

tmp = os.getenv("DECRYPTION_TOKEN_JWT_DURATION")
if tmp is not None:
    DECRYPTION_TOKEN_JWT_DURATION = int(tmp)
else:
    DECRYPTION_TOKEN_JWT_DURATION = 600
    print("DECRYPTION_TOKEN_JWT_DURATION not found, setting to default")

tmp = os.getenv("DECRYPTION_TOKEN_PASSWORD_ENCODING_KEY")
if tmp is not None:
    DECRYPTION_TOKEN_PASSWORD_ENCODING_KEY = tmp
else:
    DECRYPTION_TOKEN_PASSWORD_ENCODING_KEY = b'\xd1\x9d~\xd7\x9a\xba\x87%\xfb\xfb_B%\x17\xe2\x87\x8b\xb1\tk\xe0\xa7\xba\x8b$>6kJ]k\xda'