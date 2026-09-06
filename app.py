from flask import Flask

import config

app = Flask(__name__)
app.secret_key = config.FLASK_SECRET_KEY
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"


if __name__ == "__main__":
    app.run(debug=True)
