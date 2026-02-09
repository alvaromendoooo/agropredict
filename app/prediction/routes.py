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
    """
    Endpoint para obtener la prediccion de heladas para el dia de hoy

    Parámetros de la query:
    - province: Codigo de la provincia (opcional)
    - estacion: Codigo de la estacion (opcional)
    
    :param tipo: Tipo de dato a solicitar (Hora, Dia, Semana)
    :type tipo: str
    :return: JSON con la predicción de riesgo de helada actual
    """
    try:
        # Datos obtenidos de las querys sobre la petición
        province_code = request.args.get('province')
        estacion_code = request.args.get('estacion')
        incluir_evaluacion = request.args.get('evaluacion', 'false').lower()
        cultivos = request.args.get('cultivos')

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
        
        if not province_code and not estacion_code:
            raise APIException(
                message = "Al menos se debe especificar uno de los dos codigos a solicitar (province, estacion)",
                status = 400,
                error = 'Invalid parameters'
            )

        incluir_cultivos = incluir_evaluacion in ['true', '1', 'yes', 'si']
        cultivo_lista = None
        if cultivos:
            cultivo_lista = [c.strip().lower() for c in cultivos.split(',')]
            cultivos_disponibles = HeladaPredictionService.listar_cultivos_disponibles()
            for c in cultivo_lista:
                if c not in cultivos_disponibles:
                    raise APIException(
                        message = f"Cultivos no reconocidos: {', '.join(c)}",
                        status = 400,
                        error = 'Invalid corp params'
                    )

        # Obtengo la prediccion
        datos_prediccion = HeladaPredictionService.obtener_predicciones_helada_observadas(
            province_code = province_code,
            estacion_code = estacion_code,
            type = tipo.lower(),
            incluir_evaluacion_cultivos = incluir_cultivos,
            cultivos = cultivo_lista
        )

        return dataclass_to_json(datos_prediccion), 200
    
    except APIException as e:
        logger.error(f'API Exception en prediccion_heladas_observadas: {e}')
        return jsonify({
            'message': e.message,
            'status': e.status,
            'error': e.error
        }), e.status
    
    except ValueError as e:
        logger.error(f'ValueError en prediccion_heladas_observadas: {e}')
        return jsonify({
            'message': 'Error al procesar los datos',
            'status': 400,
            'error': str(e)
        }), 400
    
    except Exception as e:
        logger.error(f'Error inesperado en prediccion_heladas_observadas: {e}', exc_info=True)
        return jsonify({
            'message': 'Error interno del servidor',
            'status': 500,
            'error': 'Internal server error'
        }), 500

@helada_bp.route('/heladas/cultivos')
@log('../logs/fichero_salida.json')
def listar_cultivos():
    """
    Endpoint encargado de mostrar al cliente los cultivos disponibles
    """
    try:
        cultivos_disponibles = HeladaPredictionService.listar_cultivos_disponibles()

        return jsonify({
            'total' : len(cultivos_disponibles),
            'cultivos' : cultivos_disponibles,
            'mensaje' : 'Use este nombre en el parametro "cultivos" sobre los demas endpoints para filtrar la evaluacion de riesgo de helada en cultivos especificos'
        }), 200
    
    except Exception as e:
        logger.error(f'Error listando los cultivos disponibles: {e}')
        return jsonify({
            'message' : 'Error al obtener el listado de cultivos disponibles',
            'status' : 500,
            'error' : str(e)
        }), 500


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