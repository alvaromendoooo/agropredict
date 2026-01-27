from flask import Blueprint

prediction_bp = Blueprint('predicciones', __name__, template_folder = 'templates')

from . import routes