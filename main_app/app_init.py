from flask import Flask
import config

app = Flask(__name__, static_url_path="/static/", static_folder="static", template_folder="templates")
app.secret_key = config.APP_SECRET