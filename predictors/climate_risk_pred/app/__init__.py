from flask import Flask
from dotenv import load_dotenv
from config.config import Config
from .prediction import helada_bp, plagas_bp
from .extensions import init_extensions
from flask_cors import CORS
from .globals.ApiExceptions import APIException
from flask import jsonify
import logging
import os

load_dotenv()

logger = logging.getLogger(__name__)

def create_app(config_class = Config):
    app = Flask(__name__)

    CORS(app, resources = {r"/*" : {"origins" : "*"}}) # Permite CORS para todas las rutas y origenes

    app.config.from_object(config_class)

    init_extensions(app)

    
    app.register_blueprint(helada_bp)
    app.register_blueprint(plagas_bp)

    @app.errorhandler(APIException)
    def handle_api_exception(e):
        return jsonify({
            'status' : e.status,
            'error' : e.error,
            'message' : e.message,
        }), e.status
    
    @app.errorhandler(Exception)
    def handle_generic_exception(e):
        logger.exception("Unhandled exception")

        return jsonify({
            'success': False,
            'status': 500,
            'message': 'Internal Server Error'
        }), 500

    return app