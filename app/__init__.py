from flask import Flask
from dotenv import load_dotenv
from config.config import Config
import os

load_dotenv()

def create_app(config_class = Config):
    app = Flask(__name__)

    app.config.from_object(config_class)

    from .prediction import prediction_bp
    app.register_blueprint(prediction_bp)

    return app