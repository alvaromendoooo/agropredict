from config.config import Config
from .prediction_dto import *
from typing import Optional
from datetime import date, timedelta
from math import erf, sqrt
from flask import current_app
from typing import Dict, Any

class HeladaPredictionService():
    _cliente = None

    @classmethod
    def _get_cliente(cls):
        """
        Lazy initialization: crea el cliente solo cuando es necesario
        """
        if cls._cliente is None:
            from ..clients.data_service_client import DataServiceClient 
            _cliente = DataServiceClient(app = current_app)
        return _cliente
    
    @staticmethod
    def dia_juliano(fecha : date) -> int:
        """
        Convierte una fecha en un dia entero indicando el día del año
        que representa [1-366]
        
        :param fecha: Fecha que se obtiene de data_service
        :type fecha: date
        :return: Fecha pasada a entero
        :rtype: int
        """
        # Indicamos que el inicio de año agrícola es el 1 de octubre
        # Cultivo de secano
        inicio_anio_agricola = date(fecha.year, 10, 1)

        if fecha < inicio_anio_agricola:
            inicio_anio_agricola = date(fecha.year - 1, 10, 1)
        
        return (fecha - inicio_anio_agricola).days + 1
    
    @staticmethod
    def prob_helada_posterior(dia, media, desviacion) -> float:
        """
        Calcula la probabilidad de que ocurra una helada después del día dado
        
        :param dia: Dia juliano
        :param media: Media de la última helada histórica
        :param desviacion: Desviación estándar
        :return: Probabilidad (0-1)
        """
        z = (dia - media) / desviacion
        # P (X > z)
        # Probabilidad de que la helada ocurra después del día dado
        return 0.5*(1 - erf(z / sqrt(2)))

    @staticmethod
    def _datos_historicos_calculados_temp(
        datos
    ) -> Dict[str, Any]:
        """
        Analiza datos históricos para obtener información de temperaturas minimas
        y dias asociados a ellas en caso de ser temperaturas bajo cero
        
        :param datos: Datos historicos
        :return: Diccionario con información calculada de temperatura minima
        :rtype: Dict[str, Any]
        """
        dias_totales = 0
        dias_bajo_cero = 0
        temp_min_abs = float("inf")
        timestamp_temp_min = None
        timestamps_bajo_cero = [] 

        for dato in datos.get('datos', []):
            dias_totales += 1             
            temperatura_minima = dato.get('tempMin')
            if temperatura_minima <= 1.6:
                dias_bajo_cero += 1
                timestamp_temp_min = dato.get('horMinTempMin', {})
                if timestamp_temp_min and timestamp_temp_min.get('timestamp'):
                    timestamps_bajo_cero.append(
                        datetime.strptime(timestamp_temp_min.get('timestamp'), "%Y-%m-%dT%H:%M:%S").date()
                    )

            temp_min_abs = min(temp_min_abs, temperatura_minima)
            if timestamp_temp_min:
                timestamp_temp_min_abs = datetime.strptime(timestamp_temp_min.get('timestamp'), "%Y-%m-%dT%H:%M:%S").date()
        
        return {
            "dias" : dias_totales,
            "dias_bajo_cero" : dias_bajo_cero,
            "timestamps_bajo_cero" : timestamps_bajo_cero,
            "temperatura_minima_absoluta" : temp_min_abs,
            "fecha_temp_min_abs" : timestamp_temp_min_abs if timestamp_temp_min_abs else None
        }
    
    @staticmethod
    def _riesgo_tipo_helada(
        datos
    ) -> tuple:
        """
        Identifica si los datos historicos contienen indicios de riesgos por
        heladas blancas (con humedad) o heladas negras (sin humedad)
        
        :param datos: Datos historicos
        :return: Tupla con listas de riesgo (helada_blanca, helada_negra)
        """
        riesgo_helada_blanca = []
        riesgo_helada_negra = []
        
        for dato in datos.get('datos', []):
            
            temp_min = dato.get('tempMin')
            humedad_media = dato.get('humedadMedia')

            if temp_min or humedad_media is None:
                continue

            # Riesgo de helada blanca cuando hay mucho frio y humedad
            if temp_min <= 1.6:
                registro = {
                    "humedad" : humedad_media,
                    "temperatura" : temp_min,
                    "timestamp" : datetime.strptime(dato.get('horMinTempMin').get('timestamp'), "%Y-%m-%dT%H:%M:%S").date()
                }
            
            # Riesgo helada blanca: alta humedad(>= 60%)
            if humedad_media >= 60:
                riesgo_helada_blanca.append(registro)
            # Riesgo de helada negra: baja humedad(< 60%) 
            elif humedad_media < 60:
                riesgo_helada_negra.append(registro)
        
        return riesgo_helada_blanca, riesgo_helada_negra
    
    @staticmethod
    def _determinar_nivel_riesgo(
        datos
    ) -> Dict[str, Any]:
        """
        Determinar el nivel de riesgo general basado en los datos más recientes
        
        :param datos: Datos historicos
        :return: Diccionario con nivel de riesgo y alerta
        :rtype: Dict[str, Any]
        """

        dias_recientes = []
        # Analizo los últimos 7 días para determinar el riesgo actual
        for dato in reversed(datos.get('datos', [])[-7:]):
            dias_recientes.append(dato)

        if not dias_recientes:
            return {
                "nivel" : NivelHelada.SIN_RIESGO.value,
                "alertas" : []
            }

        # Analizo de entre los días mas recientes, el que tiene características
        # mas importantes
        temp_min_reciente = float("inf")
        humedad_min_reciente = None
        precipitacion_reciente = 0

        for dia in dias_recientes:
            temp_min = dia.get('tempMin')
            if temp_min is not None and temp_min < temp_min_reciente:
                temp_min_reciente = temp_min
                humedad_min_reciente = dato.get('humedadMin')
                precipitacion_reciente = dato.get('precipitacion', 0)

        # Evaluacion de condiciones
        # 1. Precipitaciones recientes reducen riesgo de heladas
        if precipitacion_reciente >= 10 and humedad_min_reciente and humedad_min_reciente >= 70:
            return {
                "nivel" : NivelHelada.SIN_RIESGO.value,
                "alertas" : [
                    AlertaDTO(
                        mensaje = "Precipitaciones recientes reducen el riesgo de heladas",
                        recomendacion = "Mantener vigilancia de las recomendaciones meteorológicas futuras",
                        nivel = TipoAlerta.INFORMATIVA.value
                    )
                ]
            }

        # 2. Evaluación por temperatura
        if temp_min <= 0:
            return {
                "nivel" : NivelHelada.FUERTE.value,
                "alertas" : [
                    AlertaDTO(
                        mensaje = f"Temperaturas minimas de {temp_min}C detectado. Riesgo fuerte de riesgo de heladas",
                        recomendacion = "Proteger cultivos sensibles con cobertura térmica, activar sistema de riego para generar una capa de agua que proteja a los brotes",
                        nivel = TipoAlerta.CRITICA.value
                    )
                ]
            }
        elif temp_min <= 1.6:
            return {
                "nivel" : NivelHelada.MODERADA.value,
                "alertas" : [
                    AlertaDTO(
                        mensaje = f"Temperaturas minimas de {temp_min}C detectado. Riesgo moderado de heladas",
                        recomendacion = "Revisa sistemas de protección, previniendo a toda costa los brotes nuevos o jóvenes",
                        nivel = TipoAlerta.PREVENTIVA.value
                    )
                ]
            }
        elif temp_min <= 3.0:
            return {
                "nivel" : NivelHelada.DEBIL.value,
                "alertas" : [
                    AlertaDTO(
                        mensaje = f"Temperaturas minimas de {temp_min}C detectado. Riesgo debil de heladas",
                        recomendacion = "Mantener vigiladas las condiciones meteorológicas, especialmente durante las horas nocturnas",
                        nivel = TipoAlerta.INFORMATIVA.value
                    )
                ]
            }

    @staticmethod
    def _build_predictions(
        data,
        fecha_inicio : date,
        fecha_fin : date            
    ) -> RiesgoHeladaObservadaDTO:
        """
        Construye los DTOs de predicciones de heladas sobre datos observados
        
        :param data: Datos historicos observados
        :param fecha_inicio: Fecha de inicio del periodo analizado
        :param fecha_fin: Fecha de finalización del periodo analizado
        :return: DTO cargado
        :rtype: RiesgoHeladaDTO
        """

        # 1. Obtención de datos calculados sobre temperaturas minimas
        stats_temp = HeladaPredictionService._datos_historicos_calculados_temp(
            datos = data
        )

        registro_temp_min = RegistroTempMinDTO(
            dias_bajo_cero = stats_temp['dias_bajo_cero'],
            temperatura_minima_registrada = stats_temp['temperatura_minima_absoluta'],
            fecha_temp_bajo_cero = stats_temp['timestamps_bajo_cero']
        )

        # 2. Identificación sobre tipo de heladas
        heladas_blancas_list, heladas_negras_list = HeladaPredictionService._riesgo_tipo_helada(
            datos = data
        )

        riesgos_heladas_blancas = []
        # Almaceno todas las heladas blancas en sus DTO para devolverlo
        if heladas_blancas_list:
            for helada_blanca in heladas_blancas_list:
                riesgos_heladas_blancas.append(
                    RiesgoHeladaTipoDTO(
                        **helada_blanca
                    )
                )

        riesgos_heladas_negras = []
        # Almaceno todas las heladas negras en sus DTO para devolverlo
        if heladas_negras_list:
            for helada_negra in heladas_negras_list:
                riesgos_heladas_negras.append(
                    RiesgoHeladaTipoDTO(
                        **helada_negra
                    )
                )

        # 3. Calculo el nivel de riesgo y alerta sobre todos los datos historicos
        riesgos_generales = HeladaPredictionService._determinar_nivel_riesgo(
            datos = data
        )

        # 4. Calculo probabilidad estadística de heladas tardías
        if stats_temp['fecha_temp_min_abs']:
            dia_juliano_temp_min = HeladaPredictionService.dia_juliano(
                fecha = stats_temp['fecha_temp_min_abs']
            )
            prob_helada = HeladaPredictionService.prob_helada_posterior(
                dia = dia_juliano_temp_min,
                media = Config.MEDIA_ULTIMA_HELADA,
                desviacion = Config.DESVIACION_HELADA 
            ) * 100 # Obtengo el porcentaje

        # 5. Generación del contexto
        comentarios = (
            f"Analisis basado en {stats_temp['dias']} dias de datos históricos "
            f"desde {fecha_inicio.strftime('%d/%m/%Y')} hasta {fecha_fin.strftime('%d/%m/%Y')}.\n"
        )

        if stats_temp['temperatura_minima_absoluta'] is not None:
            comentarios += f"Temperatura minima registrada: {stats_temp['temperatura_minima_absoluta']:.1f}C.\n"
        
        if prob_helada > 0:
            comentarios += f"Probabilidad estadistica de helada tardia: {prob_helada}.\n"
        
        comentarios += (
            f"Se detectaron {stats_temp['dias_bajo_cero']} dias con temperaturas bajo cero de los {stats_temp['dias']} dias analizados\n"
            f"Nivel actual de riesgo: {riesgos_generales['nivel']}"
        )

        # Contexto de cálculo
        contexto_calculo = ContextoCalculoDTO(
            tipos_datos = [TipoDato.HISTORICOS],
            prediccion_o_estimacion = TipoResultado.ESTIMACION,
            fuente = ['SiAR'],
            fecha_generacion = datetime.now()
        )

        # 6. Construcción de DTO final
        return RiesgoHeladaObservadaDTO(
            nivel = riesgos_generales['nivel'],
            comentarios = comentarios,
            alertas = riesgos_generales['alertas'],
            contexto = contexto_calculo,
            tipo_prediccion = TipoPrediccion.CURRENT,
            fecha_comiezo_registros = fecha_inicio,
            fecha_fin_registros = fecha_fin,
            registro_temperatura_minima = registro_temp_min,
            riesgos_heladas_blancas = riesgos_heladas_blancas,
            riesgos_heladas_negras = riesgos_heladas_negras
        )

    @classmethod
    def obtener_predicciones_helada_observadas(
        cls,
        province_code : Optional[str],
        estacion_code : Optional[str],
        type : str
    ):
        """
        Obtiene predicciones de heladas basada en datos observados historicos
        
        :param province_code: Codigo de la provincia solicitada
        :type province_code: Optional[str]
        :param estacion_code: Codigo de la estacion solicitada
        :type estacion_code: Optional[str]
        :param type: Tipo de dato a solicitar (Hora, Dia, Semana)
        :type type: str
        """
        # Almaceno la fecha de hoy
        hoy = date.today()
        # Registro la fecha de inicio de las observaciones - últimos 6 meses
        fecha_inicio = hoy - timedelta(days=182)

        client = cls._get_cliente()
        datos = client.get_historic_data(
            province_code = province_code,
            estacion_code = estacion_code,
            type = type,
            start_date = fecha_inicio,
            end_date = hoy
        )

        if not datos:
            raise ValueError("No se pudieron obtener datos historicos sobre dataservice")
        else:
            predicciones = HeladaPredictionService._build_predictions(
                data = datos,
                fecha_inicio = fecha_inicio,
                fecha_fin = hoy
            )

        return predicciones
    
    @classmethod
    def obtener_predicciones_helada_futuras(
        cls,
        province_code : Optional[str],
        ccaa_code : Optional[str],
        zona : str,
        prediccion : str
    ):
        client = cls._get_cliente()
        datos = client.get_future_data(
            province_code = province_code,
            ccaa_code = ccaa_code,
            zona = zona,
            prediccion = prediccion
        )

        if datos:
            pass