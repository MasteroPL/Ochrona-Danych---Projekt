from app_init import app

# Ładowanie widoków
from views import *



if __name__ == "__main__":
    app.run(ssl_context=("cert/certificate.crt", "cert/privateKey.key"), host="0.0.0.0", port=8880, debug=True)