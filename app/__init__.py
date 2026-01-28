from flask import Flask
from dotenv import load_dotenv
from config.config import Config
from .prediction import helada_bp
import os

load_dotenv()

def create_app(config_class = Config):
    app = Flask(__name__)

    app.config.from_object(config_class)

    
    app.register_blueprint(helada_bp)
    
    return app