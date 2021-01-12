from flask import Flask
import config
from models.mysql import MySQL

app = Flask(__name__, static_url_path="/static/", static_folder="static", template_folder="templates")
app.secret_key = config.APP_SECRET
mysql = MySQL(
    "root",
    "Qwertyui123!",
    "127.0.0.1",
    "fileshare",
    autocommit=False
)