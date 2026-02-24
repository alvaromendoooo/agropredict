from .prediction_service import HeladaPredictionService
from . import helada_bp
from ..globals.log_decorator import log
from ..globals.ApiExceptions import APIException
from ..globals.dto2dict import dataclass_to_json
from flask import jsonify
import logging
import json
from ..threading.thread_task import generar_informe_background
from flask import request, current_app

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
        variedades = request.args.get('variedades')

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

        incluir_variedades = incluir_evaluacion in ['true', '1', 'yes', 'si']
        variedades_lista = None
        if variedades:
            variedades_lista = [v.strip().lower() for v in variedades.split(',')]
            variedades_disponibles = HeladaPredictionService.listar_variedades_disponibles()
            for v in variedades_lista:
                if v not in variedades_disponibles:
                    raise APIException(
                        message = f"Variedad de cultivo no reconocidos: {', '.join(v)}",
                        status = 400,
                        error = 'Invalid corp params'
                    )

        # Obtengo la prediccion
        datos_prediccion = HeladaPredictionService.obtener_predicciones_helada_observadas(
            province_code = province_code,
            estacion_code = estacion_code,
            type = tipo.lower(),
            incluir_evaluacion_variedades = incluir_variedades,
            variedades = variedades_lista
        )

        datos_json = dataclass_to_json(datos_prediccion)
        generar_informe_background(current_app._get_current_object(), datos_prediccion = datos_json, acumular = True)
        
        return datos_json, 200
    
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

@helada_bp.route('/heladas/variedades')
@log('../logs/fichero_salida.json')
def listar_variedades():
    """
    Endpoint encargado de mostrar al cliente las variedades de cultivo disponibles
    """
    try:
        variedades_disponibles = HeladaPredictionService.listar_variedades_disponibles()

        return jsonify({
            'total' : len(variedades_disponibles),
            'cultivos' : variedades_disponibles,
            'mensaje' : 'Use este nombre en el parametro "variedades" sobre los demas endpoints para filtrar la evaluacion de riesgo de helada en variedades especificas'
        }), 200
    
    except Exception as e:
        logger.error(f'Error listando las variedades disponibles: {e}')
        return jsonify({
            'message' : 'Error al obtener el listado de variedades disponibles',
            'status' : 500,
            'error' : str(e)
        }), 500


@helada_bp.route('/heladas/futuras/<string:zona>', methods = ['GET'])
@log('../logs/fichero_salida.json')
def prediccion_heladas_futuras(
    zona : str
):
    try:
        # Parametros de query
        provinciaId = request.args.get('provinciaId')
        ccaaId = request.args.get('ccaaId')
        incluir_evaluacion_variedad = request.args.get('evaluacion_var', 'false').lower()
        incluir_evaluacion_localidad = request.args.get('evaluacion_loc', 'false').lower()
        variedades = request.args.get('variedades')
        localidades = request.args.get('localidades')


        if not zona:
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

        incluir_variedades = incluir_evaluacion_variedad in ['true', '1', 'yes', 'si']
        variedades_lista = None
        if variedades:
            variedades_lista = [v.strip().lower() for v in variedades.split(',')]
            variedades_disponibles = HeladaPredictionService.listar_variedades_disponibles()
            for v in variedades_lista:
                if v not in variedades_disponibles:
                    raise APIException(
                        message = f"Variedades de cultivo no reconocidos: {', '.join(v)}",
                        status = 400,
                        error = 'Invalid corp params'
                    )
                
        incluir_localidades = incluir_evaluacion_localidad in ['true', '1', 'yes', 'si']
        localidad_lista = None
        if localidades:
            localidad_lista = [l.strip().lower() for l in localidades.split(',')]
            localidades_disponibles = HeladaPredictionService.listar_localidades_disponibles()
            for l in localidad_lista:
                if l not in localidades_disponibles:
                    raise APIException(
                        message = f"Localidades no reconocidas: {', '.join(l)}",
                        status = 400,
                        error = 'Invalid locality params'
                    )

        datos = HeladaPredictionService.obtener_predicciones_helada_futuras(
            province_code = provinciaId,
            ccaa_code = ccaaId,
            zona = zona,
            incluir_eval_localidad = incluir_localidades,
            incluir_eval_variedades = incluir_variedades,
            localidades_normalizadas = localidad_lista,
            variedades = variedades_lista
        )
        
        datos_response = dataclass_to_json(datos)
        datos_dict = datos_response.get_json()
        generar_informe_background(current_app._get_current_object(), datos_prediccion = datos_dict, acumular = True)

        return datos_response, 200

    except APIException as e:
        logger.error(f'API Exception en prediccion_heladas_futuras: {e}')
        return jsonify({
            'message': e.message,
            'status': e.status,
            'error': e.error
        }), e.status
    
    except ValueError as e:
        logger.error(f'ValueError en prediccion_heladas_futuras: {e}')
        return jsonify({
            'message': 'Error al procesar los datos',
            'status': 400,
            'error': str(e)
        }), 400
    
    except Exception as e:
        logger.error(f'Error inesperado en prediccion_heladas_futuras: {e}', exc_info=True)
        return jsonify({
            'message': 'Error interno del servidor',
            'status': 500,
            'error': 'Internal server error'
        }), 500