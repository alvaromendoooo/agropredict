from .prediction_service import PredictionService
from .predictor_plagas import PredictorPlagasService
from . import helada_bp, plagas_bp
from ..globals.log_decorator import log
from ..globals.ApiExceptions import APIException
from ..globals.dto2dict import dataclass_to_json
from flask import jsonify, send_file
import logging
import threading
from ..threading.thread_task import( 
    generar_informe_heladas_background, 
    generar_informe_plagas_background
)
from ..globals.verify_file_response import verify_file_response
from ..globals.convertidor_tipo import convertir_tipo
from flask import request, current_app, send_from_directory
from datetime import datetime, date
import queue, os

logger = logging.getLogger(__name__)

@helada_bp.route('/heladas/observadas/<string:tipo>', methods = ['POST'])
@log('../logs/fichero_salida.json')
def prediccion_heladas_observadas(
    tipo : str
):
    """
    Endpoint para obtener la prediccion de heladas para el dia de hoy

    Contenido del cuerpo de la peticion:
    - province: Codigo de la provincia (opcional)
    - estacion: Codigo de la estacion (opcional)
    - evaluacion: Indica si se incluye una evaluación de variedades
    - variedades: Lista de nombres de variedades a evaluar
    
    :param tipo: Tipo de dato a solicitar (Hora, Dia, Semana)
    :type tipo: str
    :return: JSON con la predicción de riesgo de helada actual
    """
    try:
        # Datos obtenidos de las querys sobre la petición
        request_body = request.get_json()
        province_code = request_body.get('province')
        estacion_code = request_body.get('estacion')
        incluir_evaluacion = request_body.get('evaluacion', False)
        variedades = request_body.get('variedades')

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

        variedades_lista = None
        if incluir_evaluacion:
            if variedades:
                variedades_lista = [v.strip().capitalize() for v in variedades]
                variedades_disponibles = PredictionService.listar_variedades_disponibles()
                cultivo_asociado = variedades_disponibles[0]['nombre_cultivo']

                for v in variedades_lista:
                    if v not in [var['nombre'] for var in variedades_disponibles]:
                        raise APIException(
                            message = f"Variedad de cultivo no reconocidos: {v}",
                            status = 400,
                            error = 'Invalid corp params'
                        )

        # Obtengo la prediccion
        datos_prediccion, estaciones = PredictionService.obtener_predicciones_helada_observadas(
            province_code = province_code,
            estacion_code = estacion_code,
            type = tipo.lower(),
            incluir_evaluacion_variedades = incluir_evaluacion,
            variedades = variedades_lista
        )

        datos_response = dataclass_to_json(datos_prediccion)
        datos_json = datos_response.get_json()

        quiere_pdf = request.args.get("format") == "pdf" or \
        "application/pdf" in request.headers.get("Accept", "")

        pdf_queue = None
        if quiere_pdf:
            pdf_queue = queue.Queue()

        generar_informe_heladas_background(
            current_app._get_current_object(), 
            datos_prediccion = datos_json, 
            acumular = False, 
            is_cultivo = incluir_evaluacion,
            zona = "provincial",
            provincia = province_code,
            tipo = "observado",
            pdf_queue = pdf_queue,
            estaciones = estaciones,
            cultivo = cultivo_asociado if incluir_evaluacion else None,
            variedades = variedades_lista if incluir_evaluacion else None,
            localidades =  None,
        )

        if quiere_pdf:
            try:
                ruta_pdf = pdf_queue.get(timeout = 30)
                return send_file(
                    ruta_pdf,
                    mimetype = "application/pdf",
                    as_attachment = True,
                    download_name = os.path.basename(ruta_pdf)
                )
            except queue.Empty:
                return dataclass_to_json(datos_response), 200
        
        return datos_response, 200
    
    except ValueError as e:
        logger.error(f'ValueError en prediccion_heladas_observadas: {e}')
        return jsonify({
            'message': 'Error al procesar los datos',
            'status': 400,
            'error': str(e)
        }), 400

@helada_bp.route('/heladas/futuras/<string:zona>', methods = ['POST'])
@log('../logs/fichero_salida.json')
def prediccion_heladas_futuras(
    zona : str
):
    try:
        # Contenido del cuerpo de la peticion
        request_body = request.get_json()
        provinciaId = request_body.get('provinciaId')
        ccaaId = request_body.get('ccaaId')
        incluir_evaluacion_variedad = request_body.get('evaluacion_var', False)
        incluir_evaluacion_localidad = request_body.get('evaluacion_loc', False)
        variedades = request_body.get('variedades') # Lista de variedades
        localidades = request_body.get('localidades') # Lista de localidades


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

        variedades_lista = None
        if incluir_evaluacion_variedad:
            if variedades:
                variedades_lista = [v.strip().lower() for v in variedades]
                variedades_disponibles = PredictionService.listar_variedades_disponibles()

                nombres_disponibles = [v['nombre'].lower() for v in variedades_disponibles]
                cultivo_asociado = variedades_disponibles[0]['nombre_cultivo']

                for v in variedades_lista:
                    if v not in nombres_disponibles:
                        raise APIException(
                            message = f"Variedades de cultivo no reconocidos: {', '.join(variedades_lista)}",
                            status = 400,
                            error = 'Invalid corp params'
                        )
                    
        localidad_lista = None
        if incluir_evaluacion_localidad:        
            if localidades:
                localidad_lista = [l.strip().lower() for l in localidades]
                localidades_disponibles = PredictionService.listar_localidades_disponibles()
                for l in localidad_lista:
                    if l not in localidades_disponibles:
                        raise APIException(
                            message = f"Localidades no reconocidas: {', '.join(l)}",
                            status = 400,
                            error = 'Invalid locality params'
                        )

        datos = PredictionService.obtener_predicciones_helada_futuras(
            province_code = provinciaId,
            ccaa_code = ccaaId,
            zona = zona,
            incluir_eval_localidad = incluir_evaluacion_localidad,
            incluir_eval_variedades = incluir_evaluacion_variedad,
            localidades_normalizadas = localidad_lista,
            variedades = variedades_lista
        )
        
        predicciones_obj, estaciones_utilizadas = datos
        datos_response = dataclass_to_json(predicciones_obj)
        datos_dict = datos_response.get_json()

        quiere_pdf = request.args.get("format") == "pdf" or \
        "application/pdf" in request.headers.get("Accept", "")

        pdf_queue = None
        if quiere_pdf:
            pdf_queue = queue.Queue()

        print(variedades_lista)
        generar_informe_heladas_background(
            current_app._get_current_object(), 
            datos_prediccion = datos_dict, 
            pdf_queue = pdf_queue,
            acumular = True, 
            is_cultivo = incluir_evaluacion_variedad,
            zona = zona,
            tipo = "futuros",
            provincia = provinciaId if provinciaId else None,
            cultivo = cultivo_asociado if incluir_evaluacion_variedad else None,
            variedades = variedades_lista if incluir_evaluacion_variedad else None,
            localidades = localidad_lista if incluir_evaluacion_localidad else None,
            estaciones = estaciones_utilizadas,
        )

        if quiere_pdf:
            try:
                ruta_pdf = pdf_queue.get(timeout = 30)
                return send_file(
                    ruta_pdf,
                    mimetype = "application/pdf",
                    as_attachment = True,
                    download_name = os.path.basename(ruta_pdf)
                )
            except queue.Empty:
                return dataclass_to_json(datos_response), 200

        return datos_response, 200
    
    except ValueError as e:
        logger.error(f'ValueError en prediccion_heladas_futuras: {e}')
        return jsonify({
            'message': 'Error al procesar los datos',
            'status': 400,
            'error': str(e)
        }), 400
    
@plagas_bp.route('/plagas/calculadas', methods = ['POST'])
@log('../logs/fichero_salida.json')
def prediccion_plagas_calculadas():

    cultivo = request.args.get('cultivo')

    if not cultivo:
        raise APIException(
            message = 'Invalid parameters',
            status = 400,
            error = 'Se debe indicar el valor de un query param : cultivo'
        )
    
    datos = PredictorPlagasService.obtener_prediccion_plagas_calculadas(
        cultivos = cultivo
    )

    if not datos:
        raise APIException(
            message = 'Data Not Found',
            status = 404,
            error = f'No se han encontrado datos para hacer la predicción de riesgos de plagas frente al cultivo : {cultivo}'
        )
    
    
    datos_response = dataclass_to_json(datos)
    datos_dict = datos_response.get_json()

    quiere_pdf = request.args.get("format") == "pdf" or \
        "application/pdf" in request.headers.get("Accept", "")

    pdf_queue = None
    if quiere_pdf:
        pdf_queue = queue.Queue()

    generar_informe_plagas_background(
        current_app._get_current_object(),
        pdf_queue = pdf_queue,
        plagas = [datos_dict],
        datos_estimados= None,
        tipo_informe = "calculado",
        sensores = None,
        parcelas = None
    )

    if quiere_pdf:
        try:
            ruta_pdf = pdf_queue.get(timeout = 30)
            #return verify_file_response("plagas")
            return send_file(
                ruta_pdf,
                mimetype = "application/pdf",
                as_attachment = True,
                download_name = os.path.basename(ruta_pdf)
            )
        except queue.Empty:
            return dataclass_to_json(datos_response), 200
        #return verify_file_response("plagas")

    return datos_response

@plagas_bp.route('/plagas/estimadas', methods = ['POST'])
@log('../logs/fichero_salida.json')
def predecir_riesgo_plagas_estimadas():
    datos_peticion = request.get_json()

    # Extraemos los datos de la petición
    cultivo = datos_peticion.get('cultivo')
    fecha_inicio_str = datos_peticion.get('fecha_inicio')
    fecha_fin_str = datos_peticion.get('fecha_fin')
    datos_sensores = datos_peticion.get('datos_sensores')
    parcela_id = datos_peticion.get('parcela', None)

    # Parseo de fechas
    fecha_inicio = datetime.fromisoformat(fecha_inicio_str.replace('Z', '+00:00')).date()
    fecha_fin = datetime.fromisoformat(fecha_fin_str.replace('Z', '+00:00')).date()

    resultado = PredictorPlagasService.obtener_prediccion_plagas_estimadas(
        cultivo = cultivo,
        datos_sensores = datos_sensores,
        fecha_inicio = fecha_inicio,
        fecha_fin = fecha_fin
    )

    resultado_response = dataclass_to_json(resultado)
    resultado_dict = resultado_response.get_json()

    # Obtengo las parcelas asociadas al cultivo para dar contexto de cálculo
    parcelas_asociadas_cultivo = PredictorPlagasService._obtener_parcelas_asociadas_cultivo(
        cultivo,
        parcela_id = parcela_id
    )

    quiere_pdf = request.args.get("format") == "pdf" or \
        "application/pdf" in request.headers.get("Accept", "")

    pdf_queue = None
    if quiere_pdf:
        pdf_queue = queue.Queue()

    generar_informe_plagas_background(
        current_app._get_current_object(),
        plagas = None,
        pdf_queue = pdf_queue,
        datos_estimados= resultado_dict,
        tipo_informe = "estimado",
        parcelas = parcelas_asociadas_cultivo if parcelas_asociadas_cultivo else None,
        sensores = datos_sensores if datos_sensores else None
    )

    if quiere_pdf:
        try:
            ruta_pdf = pdf_queue.get(timeout = 30)
            print(ruta_pdf)
            return send_file(
                ruta_pdf,
                mimetype = "application/pdf",
                as_attachment = True,
                download_name = os.path.basename(ruta_pdf)
            )
        except queue.Empty:
            return dataclass_to_json(resultado), 200
        
    return dataclass_to_json(resultado), 200