from flask import Flask
from flask_login import LoginManager as FlaskLoginManager
import config
from models.mysql import MySQL

app = Flask(__name__, static_url_path="/static/", static_folder="static", template_folder="templates")
app.secret_key = config.APP_SECRET
mysql = MySQL(
    config.DATABASE_USER,
    config.DATABASE_PASSWORD,
    config.DATABASE_HOST,
    config.DATABASE_DB_NAME,
    autocommit=False
)
login_manager = FlaskLoginManager()
login_manager.init_app(app)
