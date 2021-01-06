from app_init import app

# Ładowanie widoków
from views import *

if __name__ == "__main__":
    app.run(ssl_context="adhoc", host="0.0.0.0", port=5000, debug=True)