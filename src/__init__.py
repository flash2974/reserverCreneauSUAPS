import os
from dotenv import load_dotenv
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager
from src.AutoSUAPS import AutoSUAPS
from src.Notifier import Notifier



load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../config/.env"), override=True)

# === ENV SETUP ===
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
TOKEN = os.getenv("TOKEN")
DEBUG = os.getenv("DEBUG") == "True"
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
DISCORD_ID = os.getenv("DISCORD_ID")

# === FLASK APP SETUP ===
app = Flask(__name__)
app.secret_key = os.urandom(24)

# Cookie de session sécurisé sous HTTPS only + transmission headers sécurisés
if not DEBUG :
    app.config["SESSION_COOKIE_SECURE"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

notifier = Notifier(WEBHOOK_URL, DISCORD_ID)
auto = AutoSUAPS(USERNAME, PASSWORD, notifier)