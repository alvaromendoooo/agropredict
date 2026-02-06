from .prediction_service import HeladaPredictionService
from . import helada_bp
from ..globals.log_decorator import log
from ..globals.ApiExceptions import APIException
from ..globals.dto2dict import dataclass_to_json
from .prediction_dto import TipoDato
from datetime import date
from typing import Optional
from flask import jsonify
import logging
from flask import request

logger = logging.getLogger(__name__)

@helada_bp.route('/heladas/observadas/<string:tipo>', methods = ['GET'])
@log('../logs/fichero_salida.json')
def prediccion_heladas_observadas(
    tipo : str
):
    try:

        province_code = request.args.get('province')
        estacion_code = request.args.get('estacion')


        # Comprobación de parámetros recibidos
        if not tipo:
            raise APIException(
                message = "Todos los parámetros deben estar definidos",
                status = 400,
                error = 'Invalid parameters'
            )
        
        # Solo se puede indicar uno de los dos, o código de provincia o código de estacion
        if province_code and estacion_code:
            raise APIException(
                message = "Solo se puede indicar el código de provincia o el código de estacion",
                status = 400,
                error = 'Invalid parameters'
            )

        datos_prediccion = HeladaPredictionService.obtener_predicciones_helada_observadas(
            province_code = province_code,
            estacion_code = estacion_code,
            type = tipo
        )

        return dataclass_to_json(datos_prediccion)
    except APIException as e:
        logger.error(f'API Exception: {e}')
        return jsonify(
            {
                'message' : 'Provider error',
                'status' : '502',
                'error' : str(e)
            }
        ), 502
        
@helada_bp.route('/heladas/futuras/<string:zona>/<string:prediccion>', methods = ['GET'])
@log('../logs/fichero_salida.json')
def prediccion_heladas_futuras(
    zona : str,
    prediccion : str
):
    try:
        provinciaId = request.args.get('provinciaId')
        ccaaId = request.args.get('ccaaId')

        if not zona and prediccion:
            raise APIException(
                message = 'Todos los parámetros deben estar definidos',
                status = 400,
                error = 'Invalid parameters'
            )
        
        if provinciaId and ccaaId:
            raise APIException(
                message = 'Solo se puede indicar el id de la provincia o el de la comunidad, no los dos',
                status = 400,
                error = 'Invalid parameters'
            )
    
    except APIException as e:
        logger.error(f'API Exception: {e}')
        return jsonify(
            {
                'message' : 'Provider error',
                'status' : '502',
                'error' : str(e)
            }
        ), 502