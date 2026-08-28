from flask import Blueprint

helada_bp = Blueprint('heladas', __name__, template_folder = 'templates')
plagas_bp = Blueprint('plagas', __name__, template_folder = 'templates')

from . import routes