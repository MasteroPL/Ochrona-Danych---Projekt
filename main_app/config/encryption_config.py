import os

tmp = os.getenv("DEFAULT_ENCODING_PASSWORD")
if tmp is not None:
    DEFAULT_ENCODING_PASSWORD = tmp
else:
    DEFAULT_ENCODING_PASSWORD = b'\x95%\xe9\xeb\x15\xff\xb6\x19\xd1\xe6\xe5?\x07C\xebh\xb9\x82r\xbf\x1c\xed\xaa\x0f'
    print("DEFAULT_ENCODING_PASSWORD not found, setting to default")