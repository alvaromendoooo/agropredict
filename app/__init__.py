from flask import Flask
from dotenv import load_dotenv
from config.config import Config
import os

load_dotenv()

def create_app(config_class = Config):
    app = Flask(__name__)

    app.config.from_object(config_class)

    return app