from config.config import Config
from .prediction_dto import *
from ..crops.crops_threshold import evaluar_riesgo_varios_cultivos, listar_cultivo
from typing import Optional, Union
from datetime import date, timedelta
from math import erf, sqrt
from flask import current_app
from typing import Dict, Any
import re

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
    def _recuento_riesgos() -> Dict:
        """
        Devuelve un registro de riesgos que sirve como contador 
        
        :return: Diccionario con el mapa de registros reseteado
        :rtype: Dict
        """

        return {
            "critico" : 0,
            "alto" : 0,
            "moderado" : 0,
            "debil" : 0,
            "sin_riesgo" : 0
        }

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
    def _temperatura_minima_futuros_calculada(
        temperaturas_localidades : list[Dict]
    ) -> float:
        """
        Dado las temperaturas por localidades que arroja la predicción de 
        dataservice, obtenemos la temperatura mínima registrada para la 
        provincia de cáceres.
        
        :param temperaturas_localidades: Localidades de AEMET con sus temperaturas
        :type temperaturas_localidades: list[Dict]
        :return: Temperatura minima registrada para la provincia en base a las localidades
        :rtype: float
        """

        temp_min_absoluta = 10000
        
        for temp_loc in temperaturas_localidades:
            temperatura_minima_localidad = temp_loc['temperatura_minima']
            if temperatura_minima_localidad < temp_min_absoluta:
                temp_min_absoluta = temperatura_minima_localidad

        return temp_min_absoluta

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
        registro = {}
        estaciones_humedad = []
        
        for dato in datos.get('datos', []):
            temp_min = dato.get('tempMin')
            humedad_media = dato.get('humedadMedia')
            if (temp_min or humedad_media) is None:
                continue

            # Riesgo de helada blanca cuando hay mucho frio y humedad
            if temp_min <= 1.6:
                estaciones_humedad = [
                    dato.get('horMinHumMin').get('estacion_id'), 
                    dato.get('horMinHumMax').get('estacion_id')
                ]
                registro = {
                    "humedad" : humedad_media,
                    "temperatura" : temp_min,
                    "timestamp" : datetime.strptime(dato.get('fecha'), "%Y-%m-%d").date(),
                    "estacion_id_temp" : dato.get('horMinTempMin').get('estacion_id'),
                    "estacion_id_hum" : estaciones_humedad
                }
                # Riesgo helada blanca: alta humedad(>= 60%)
                if humedad_media >= 60:
                    riesgo_helada_blanca.append(registro)
                # Riesgo de helada negra: baja humedad(< 60%) 
                elif humedad_media < 60:
                    riesgo_helada_negra.append(registro)
                
                # Reset de datos almacenados
                estaciones_humedad = []
        
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
    def _generate_alerta_cultivo(
        evaluacion_cultivos : Dict
    ) -> List[AlertaDTO]:
        """
        Genera alertas especificas por cultivo en base a sus evaluaciones
        
        :param evaluacion_cultivos: Datos de evaluacion sobre los cultivos solicitados
        :type evaluacion_cultivos: Dict
        :return: Lista de alertas sobre cada cultivo solicitado
        :rtype: List[AlertaDTO]
        """

        nivel_riesgo = evaluacion_cultivos.get('nivel_riesgo')
        cultivo = evaluacion_cultivos.get('cultivo')
        etapa = evaluacion_cultivos.get('etapa_fenologica')
        temperatura = evaluacion_cultivos.get('temperatura')
        
        alerta = None

        # Recomendaciones especificas para cultivos y nivel de riesgo
        recomendaciones = {
            "fuerte" : {
                "almendro" : "CRITICO : Portejer brotes de almendro con mantas términas",
                "cerezo" : "CRITICO : Utilizar Red Protectora para Arboles Frutales",
                "melocotonero" : "CRITICO: Utilizar malla o velo anti-heladas"
            },
            "moderada" : {
                "almendro" : "ALERTA : Rociamiento de CODIFROST con un mojante NO IONICO en los brotes",
                "cerezo" : "ALERTA : Monitoreo de temperatura, aplicar sistema de aspersión para envolver al brote con capa de agua",
                "melocotonero" : "ALERTA : Rociamiento de CODIFROST con un mojante NO IONICO en los brotes"
            },
            "debil" : {
                "default" : "VIGILANCIA de las temperaturas minimas nocturnas por los agentes meteorologicos"
            }
        }

        if nivel_riesgo in ["fuerte", "moderada", "debil"]:
            categoria_recomendacion = recomendaciones.get(nivel_riesgo, {})

            # Caso general para todo tipo de cultivo analizado
            if nivel_riesgo == "debil":
                recomendacion_cultivo = categoria_recomendacion['default']
            else:
                recomendacion_cultivo = categoria_recomendacion.get(cultivo.lower(), {})

            tipo_alerta = {
                "fuerte" : TipoAlerta.CRITICA,
                "moderada" : TipoAlerta.PREVENTIVA,
                "debil" : TipoAlerta.INFORMATIVA
            }.get(nivel_riesgo, TipoAlerta.INFORMATIVA)

            alerta = AlertaDTO(
                mensaje = f"Cultivo {cultivo} en etapa de {etapa}: riesgo {nivel_riesgo} a temperatura {temperatura:.1}C",
                recomendacion = recomendacion_cultivo,
                nivel = tipo_alerta
            )
            
        return alerta

    

    @staticmethod
    def _evaular_riesgo_cultivos(
        temperatura_minima : float,
        mes : int,
        cultivos : Optional[list[str]] = None
    ) -> ResumenCultivoDTO:
        """
        Evaula el riesgo de helada en cada uno de los cultivos pasados
        
        :param temperatura_minima: Temperatura minima a evaluar en cada cultivo
        :type temperatura_minima: float
        :param mes: Mes del año (1-12)
        :type mes: int
        :param cultivos: Lista con el nombre de los cultivos a analizar
        :type cultivos: Optional[list[str]]
        :return: DTO con el resumen de los cultivos analizados
        :rtype: ResumenCultivoDTO
        """

        # 1. Obtengo los datos evaluados que devuelve crops_threshold
        evaluacion = evaluar_riesgo_varios_cultivos(
            temperatura = temperatura_minima,
            mes = mes,
            cultivos = cultivos
        )

        # Convertir los datos evaluados obtenidos a DTO resultante
        analisis_cultivos = []
        riesgos = HeladaPredictionService._recuento_riesgos()

        alertas = []
        for ev in evaluacion:
            alerta_evaluacion = HeladaPredictionService._generate_alerta_cultivo(
                evaluacion_cultivos = ev
            )
            alertas.append(alerta_evaluacion)

            # Incremento los contadores
            nivel = ev.get('nivel_riesgo')
            if nivel == "fuerte":
                riesgos['critico'] += 1
            elif nivel == "moderadas":
                riesgos['moderado'] += 1
            elif nivel == "debil":
                riesgos['debil'] += 1
            else:
                riesgos['sin_riesgo'] += 1

            # Creacion del DTO AnalisisCultivo
            analisis_cultivos.append(
                AnalisisCultivoDTO(
                    cultivo = ev['cultivo'],
                    nombre_cientifico = ev['nombre_cientifico'],
                    etapa_fenologica = ev['etapa_fenologica'],
                    temperatura_evaluada = ev['temperatura'],
                    nivel_riesgo = ev['nivel_riesgo'],
                    umbrales = UmbralesCultivoDTO(
                        critico = ev['umbrales']['critico'],
                        alto = ev['umbrales']['alto'],
                        moderado = ev['umbrales']['moderado'],
                        bajo = ev['umbrales']['bajo']
                    ),
                    alertas = alertas
                )
            )
            # Reset de alertas obtenidas en la evaluación para no cargar
            # con ellas en otras evaluaciones
            alertas = []
        
        return ResumenCultivoDTO(
            total_cultivos_evaluados = len(cultivos),
            cultivos_en_riesgo_critico = riesgos['critico'],
            cultivos_en_riesgo_alto = riesgos['alto'],
            cultivos_en_riesgo_moderado = riesgos['moderado'],
            cultivos_en_riesgo_debil = riesgos['debil'],
            cultivos_sin_riesgo = riesgos['sin_riesgo'],
            evaluaciones = analisis_cultivos
        )

    @staticmethod
    def _evaluar_sin_cota(
        datos,
        localidades_disponibles : list[dict],
        localidades_analizar : Optional[list[str]],
        localidades_prediccion : Optional[list[dict]]
    ) -> ResumenEvaluacionLocalidadDTO:
        """
        Evalua el riesgo de heladas futuras sin tener en cuenta la cota de nieve
        
        :param datos: Datos futuros obtenidos de dataservice
        :param localidades_disponibles: Lista de las localidades disponibles por dataservice
        :type localidades_disponibles: list[dict]
        :param localidades_analizar: Lista de localidades a analizar el riesgo de helada
        :type localidades_analizar: Optional[list[str]]
        :param localidades_prediccion: Lista de localdades que AEMET arroja en dataservice
        :type localidades_prediccion: Optional[list[dict]]
        :return: Description
        :rtype: ResumenEvaluacionLocalidadDTO
        """

        riesgos = HeladaPredictionService._recuento_riesgos()
        lista_analisis = []
        nivel_riesgo = None

        datos_localidades_analizar = []

        datos_localidades_analizar = [
            localidad
            for localidad in localidades_disponibles
            if localidad['nombre_normalizado'] in localidades_analizar
        ]
        
        if not datos_localidades_analizar:
            return ResumenEvaluacionLocalidadDTO(
                total_localidades_evaluadas = 0,
                localidades_riesgo_critico = 0,
                localidades_riesgo_alto = 0,
                localidades_riesgo_moderado = 0,
                localidades_riesgo_bajo = 0,
                localidades_sin_riesgo = 0,
                evaluaciones = []
            )

        for localidad in datos_localidades_analizar:
            recomendaciones = []

            localidades_pred = next(
                (
                    l for l in localidades_prediccion
                    if l['nombre'] == localidad['nombre_normalizado']
                ),
                None
            )

            if not localidades_pred:    
                continue
                
            print(f"Datos localidades a analizar : {datos}")
            temperatura_minima = localidades_pred['temperatura_minima']
            temperatura_maxima = localidades_pred['temperatura_maxima']
            altitud = localidad['altitud']
            precipitaciones = datos['datos'].get('precipitaciones')
            existencia_nieblas = datos['datos'].get('aparicion_nieblas')
            cota_nieve : CotaNieveDTO = None
            score = 0

            # Análisis de temperatura
            if temperatura_minima <= 0.0: # No necesita más factores para considerar riesgo crítico de heladas
                score += 4
                recomendaciones.append("Temperaturas minimas bajo cero previstas. Altas probabilidades de heladas")
            elif temperatura_minima is 0.0:
                if datos['rachas_viento']: # Condicionante para que existan heladas a temperatura 0.0
                    score += 3
                    recomendaciones.append("Temperaturas minimas en 0 absoluto, posibilidades altas de helada debido a la existencia de viento.")
                else:
                    score += 2.5
                    recomendaciones.append("Temperaturas minimas en 0 absoluto, posibilidad de que se produzcan heladas si existen otros factores afectantes.")
            elif temperatura_minima <= 1.6:
                score += 2
                recomendaciones.append('Temperaturas minimas frías, pero sin mucho riesgo de producir heladas salvo la existencia de factores afectantes.')
            elif temperatura_minima <= 5:
                score += 1
                recomendaciones.append('Pocas posibilidades de que se produzcan heladas.')
            else:
                riesgos['sin_riesgo'] += 1
                recomendaciones.append('Sin riesgo de existencia de heladas.')

            # Análisis de precipitacion
            if precipitaciones and temperatura_minima <= 1.6:
                score += 1
                recomendaciones.append('Precipitacion previa favorece la formación de hielo.')
            
            # Análisis de nieblas
            if existencia_nieblas and temperatura_minima <= 1.6:
                score += 1
                recomendaciones.append("Condiciones de humedad elevadas.")

            if score >= 5:
                nivel_riesgo = "critico"
            elif score >= 4:
                nivel_riesgo = "alto"
            elif score >= 2:
                nivel_riesgo = "moderado"
            elif score >= 1:
                nivel_riesgo = "debil"
            else:
                nivel_riesgo = "sin_riesgo"

            riesgos[nivel_riesgo] += 1

            lista_analisis.append(
                AnalisisLocalidadDTO(
                    localidad = localidad['nombre'],
                    provincia = localidad['provincia'],
                    altitud_metros = altitud,
                    temperatura_minima = temperatura_minima,
                    temperatura_maxima = temperatura_maxima,
                    nivel_riesgo = nivel_riesgo,
                    resumen = (
                        f"La localidad {localidad['nombre']} (altitud {altitud} m) "
                        f"presenta un riesgo {nivel_riesgo} sin considerar la cota de nieve "
                        f"({cota_nieve.texto_original if cota_nieve else 'no disponible'})."
                    ),
                    recomendaciones = recomendaciones,
                    cota_nieve = None
                )
            )

        return ResumenEvaluacionLocalidadDTO(
            total_localidades_evaluadas = len(lista_analisis),
            localidades_riesgo_critico = riesgos['critico'],
            localidades_riesgo_alto = riesgos['alto'],
            localidades_riesgo_moderado = riesgos['moderado'],
            localidades_riesgo_bajo = riesgos['debil'],
            localidades_sin_riesgo = riesgos['sin_riesgo'],
            evaluaciones = lista_analisis
        )  


    @staticmethod
    def _evaluar_por_nieve(
        cota_nieve : Optional[CotaNieveDTO],
        localidades_disponibles : list[dict],
        localidades_analizar : Optional[list[str]],
        localidades_prediccion : Optional[list[dict]]
    ) -> ResumenEvaluacionLocalidadDTO:
        """
        Evalua heladas futuras en base a datos sobre la cota de nieve
        
        :param cota_nieve: Cota de nieve extraida de la prediccion por dataservice
        :type cota_nieve: CotaNieveDTO
        :param localidades_disponibles : Localidades disponibles que arroja dataservice
        :type localidades_disponibles : list[dict]
        :param localidades_analizar: Lista de localidades a analizar
        :type localidades_analizar: Optional[list[str]]
        :param localidades_prediccion: Lista de localidades que arroja la prediccion de dataservice
        :type localidades_prediccion: Optional[list[dict]]
        :return: DTO con los datos evaluados
        :rtype: ResumenEvaluacionLocalidadDTO
        """
        
        riesgos = HeladaPredictionService._recuento_riesgos()

        lista_analisis = []

        datos_localidades_analizar = []

        for localidad in localidades_disponibles:
            
            datos_localidades_analizar.append(
                next(
                    l for l in localidades_analizar
                    if l['nombre'] == localidad['nombre_normalizado']
                )
            )

        if not datos_localidades_analizar:
            return ResumenEvaluacionLocalidadDTO(
                total_localidades_evaluadas = 0,
                localidades_riesgo_critico = 0,
                localidades_riesgo_alto = 0,
                localidades_riesgo_moderado = 0,
                localidades_riesgo_bajo = 0,
                localidades_sin_riesgo = 0,
                evaluaciones = []
            )

        for localidad in datos_localidades_analizar:
            recomendaciones = []

            localidades_pred = next(
                (
                    l for l in localidades_prediccion
                    if l['nombre'] == localidad['nombre_normalizado']
                ),
                None
            )

            if not localidades_pred:    
                continue
            
            altitud = localidad['altitud']
            temperatura_minima = localidades_pred['temperatura_minima']
            temperatura_maxima = localidades_pred['temperatura_maxima']

            if cota_nieve.cota_minima <= altitud <= cota_nieve.cota_maxima:
                
                # No conocemos las temperaturas minimas dentro de la cota
                # Asumimos riesgo moderado si hay descenso
                if cota_nieve.hay_descenso:
                    riesgos['moderado'] += 1
                    nivel_riesgo = 'moderado'
                    recomendaciones.append(
                        f"La cota de nieve esta en descenso y la localidad {localidad['nombre']} se encuentra dentro del rango de altitud afectado."
                    )
                else:
                    riesgos['critico'] += 1
                    nivel_riesgo = 'critico'
                    recomendaciones.append(
                        f"La localidad {localidad['nombre']} se encuentra dentro del rango de cota de nieve previsto."
                    )
                

            elif altitud > cota_nieve.cota_maxima: # Altitud por encima de la cota
                
                # Si se encuentra más alto que la cota media obtenida
                # Lo más seguro es que sus temperaturas mínimas sean muy bajas
                riesgos['critico'] += 1
                nivel_riesgo = 'critico'
                recomendaciones.append(
                    f"La localidad {localidad['nombre']} se encuentra por encima de la cota de nieve prevista."
                )

            else: # Altitud por debajo de la cota
               
                if temperatura_minima <= 0.0: # Casi 100% hiela
                    riesgos['critico'] += 1
                    nivel_riesgo = 'critico'
                elif temperatura_minima <= 1.6: # Factor alto de helada
                    riesgos['alto'] += 1
                    nivel_riesgo = 'alto'
                elif temperatura_minima <= 7:
                    riesgos['debil'] += 1
                    nivel_riesgo = 'debil'
                else:
                    riesgos['sin_riesgo'] += 1
                    nivel_riesgo = 'sin_riesgo'


            # Creación del DTO sobre el analisis realizado por localidad y cota de nieve
            lista_analisis.append(
                AnalisisLocalidadDTO(
                    localidad=localidad['nombre'],
                    provincia=localidad['provincia'],
                    altitud_metros=altitud,
                    temperatura_minima=temperatura_minima,
                    temperatura_maxima=temperatura_maxima,
                    nivel_riesgo=nivel_riesgo,
                    resumen=(
                        f"La localidad {localidad['nombre']} (altitud {altitud} m) "
                        f"presenta un riesgo {nivel_riesgo} considerando la cota de nieve "
                        f"({cota_nieve.texto_original if cota_nieve else 'no disponible'})."
                    ),
                    recomendaciones=recomendaciones,
                    cota_nieve=cota_nieve
                )
            )

        return ResumenEvaluacionLocalidadDTO(
            total_localidades_evaluadas = len(lista_analisis),
            localidades_riesgo_critico = riesgos['critico'],
            localidades_riesgo_alto = riesgos['alto'],
            localidades_riesgo_moderado = riesgos['moderado'],
            localidades_riesgo_bajo = riesgos['debil'],
            localidades_sin_riesgo = riesgos['sin_riesgo'],
            evaluaciones = lista_analisis
        )  

    @staticmethod
    def _nivel_riesgo_predictivo(
        prediccion
    ) -> Union[NivelHelada, AlertaDTO]:
        if isinstance(prediccion, ResumenEvaluacionLocalidadDTO):
            if prediccion.localidades_riesgo_critico > 0:
                return NivelHelada.FUERTE, AlertaDTO(
                    mensaje = "Riesgo crítico de heladas en las próximas horas.",
                    recomendacion = (
                        "Posibles temperaturas bajo cero con impacto significativo. "
                        "Extremar precauciones en carretera, proteger tuberías y "
                        "evitar exposición prolongada al frío."
                    ),
                    nivel = TipoAlerta.CRITICA
                )
            elif prediccion.localidades_riesgo_alto > 0:
                return NivelHelada.MODERADA, AlertaDTO(
                    mensaje = "Alta probabilidad de heladas localizadas.",
                    recomendacion = (
                        "Posible formación de placas de hielo en zonas elevadas y umbrías. "
                        "Conducir con precaución y revisar previsiones actualizadas."
                    ),
                    nivel = TipoAlerta.ALTA
                )
            elif prediccion.localidades_riesgo_moderado > 0:
                return NivelHelada.DEBIL, AlertaDTO(
                    mensaje = "Probabilidad moderada de heladas débiles.",
                    recomendacion = (
                        "Heladas puntuales en zonas rurales o de mayor altitud. "
                        "Se recomienda seguimiento preventivo."
                    ),
                    nivel = TipoAlerta.MEDIA
                )
            else:
                return NivelHelada.SIN_RIESGO, AlertaDTO(
                    mensaje = "Sin riesgo significativo de heladas.",
                    recomendacion = "No se requieren medidas especiales.",
                    nivel = TipoAlerta.INFORMATIVA
                )   

        elif isinstance(prediccion, ResumenCultivoDTO):
            if prediccion.cultivos_en_riesgo_critico > 0:
                return NivelHelada.FUERTE, AlertaDTO(
                    mensaje = "Riesgo crítico de daños por helada en cultivos sensibles.",
                    recomendacion = (
                        "Se recomienda activar medidas de protección: riego antihelada, "
                        "cubiertas térmicas o sistemas de ventilación. "
                        "Especial atención a brotes y floración."
                    ),
                    nivel = TipoAlerta.CRITICA
                )
            elif prediccion.cultivos_en_riesgo_alto > 0:
                return NivelHelada.MODERADA, AlertaDTO(
                    mensaje = "Riesgo elevado de estrés térmico en cultivos.",
                    recomendacion = (
                        "Monitorizar temperaturas nocturnas y preparar sistemas de protección "
                        "si el cultivo se encuentra en fase sensible."
                    ),
                    nivel = TipoAlerta.ALTA
                )
            elif prediccion.cultivos_en_riesgo_moderado > 0:
                return NivelHelada.DEBIL, AlertaDTO(
                    mensaje = "Riesgo leve de helada en algunos cultivos.",
                    recomendacion = (
                        "No se esperan daños generalizados, pero conviene vigilar "
                        "cultivos tempranos o en fase de brotación."
                    ),
                    nivel = TipoAlerta.MEDIA
                )
            else:
                return NivelHelada.SIN_RIESGO, AlertaDTO(
                    mensaje = "Condiciones térmicas favorables para los cultivos.",
                    recomendacion = "No se prevén daños por helada.",
                    nivel = TipoAlerta.INFORMATIVA
                )

    @staticmethod
    def _build_observadas_predictions(
        data,
        fecha_inicio : date,
        fecha_fin : date,
        incluir_evaluacion_cultivo : bool,
        cultivos : Optional[list[str]] = None            
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

        # 5. Evaluación de cultivos
        evaluacion_cultivos = None
        if incluir_evaluacion_cultivo and stats_temp['temperatura_minima_absoluta']:
            evaluacion_cultivos = HeladaPredictionService._evaular_riesgo_cultivos(
                temperatura_minima = stats_temp['temperatura_minima_absoluta'],
                mes = fecha_fin.month,
                cultivos = cultivos
            )

        # 6. Generación del contexto
        comentarios = (
            f"Analisis basado en {stats_temp['dias']} dias de datos historicos "
            f"desde {fecha_inicio.strftime('%d/%m/%Y')} hasta {fecha_fin.strftime('%d/%m/%Y')}. "
        )

        if stats_temp['temperatura_minima_absoluta'] is not None:
            comentarios += f"Temperatura minima registrada: {stats_temp['temperatura_minima_absoluta']:.1f}C. "
        
        if prob_helada > 0:
            comentarios += f"Probabilidad estadistica de helada tardia: {prob_helada}. "
        
        comentarios += (
            f"Se detectaron {stats_temp['dias_bajo_cero']} dias con temperaturas bajo cero de los {stats_temp['dias']} dias analizados. "
            f"Nivel actual de riesgo: {riesgos_generales['nivel']}"
        )

        # Contexto de cálculo
        contexto_calculo = ContextoCalculoDTO(
            tipos_datos = [TipoDato.HISTORICOS],
            prediccion_o_estimacion = TipoResultado.ESTIMACION,
            fuente = ['SiAR'],
            fecha_generacion = datetime.now()
        )

        # 7. Construcción de DTO final
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
            riesgos_heladas_negras = riesgos_heladas_negras,
            evaluaciones_cultivo = evaluacion_cultivos
        )
    
    @staticmethod
    def _build_futuras_predicciones(
        datos_futuros,
        datos_localidades,
        incluir_evaluacion_localidad : bool,
        localidades : Optional[list[str]],
        incluir_evaulacion_cultivo : bool,
        cultivos : Optional[list[str]]
    ) -> RiesgoHeladaFuturaDTO:
        """
        Genera el DTO de predicciones futuras de heladas sobre los datos recopilados
        
        :param datos_futuros: Datos futuros obtenidos de AEMET
        :param datos_localidades: Datos de localidades disponibles
        :param incluir_evaluacion_localidad: Condicionante para determinar la evaluación de riesgos de helada por localidad
        :type incluir_evaluacion_localidad: bool
        :param localidades: Lista de localidades a evaluar
        :type localidades: Optional[list[str]]
        :param incluir_evaulacion_cultivo: Condicionante para determinar la evaluación de riesgo de heladas sobre cultivos
        :type incluir_evaulacion_cultivo: bool
        :param cultivos: Lista de cultivos a evaluar
        :type cultivos: Optional[list[str]]
        :return: DTO resultante con los datos recopilados importantes a enviar
        :rtype: RiesgoHeladaFuturaDTO
        """
        
        nivel_riesgo = None
        comentarios = "Predicciones futuras basadas en datos proporcionados por AEMET."
        alertas = []
        predicciones_cultivo = None
        predicciones_localidad = None

        #1. Obtengo el tipo de prediccion 
        tipo_prediccion = datos_futuros['type_prediction']

        mapeo_tipo_prediccion = {
            "actual" : TipoDato.ACTUALES,
            "tomorrow" : TipoDato.FUTUROS,
            "aftertomorrow" : TipoDato.FUTUROS
        }

        #2. Obtengo datos parseados de AEMET para construir su DTO
        datos_meteorologicos = DatoAEMETDTO(
            estado_cielo = datos_futuros['datos'].get('estado_cielo'),
            tendencia_temp_general = datos_futuros['datos'].get('tendencia_temp_general'),
            tendencia_temp_maxima = datos_futuros['datos'].get('tendencia_temp_max'),
            tendencia_temp_minima = datos_futuros['datos'].get('tendencia_temp_min'),
            rachas_viento = datos_futuros['datos'].get('rachas_viento'),
            precipitaciones = datos_futuros['datos'].get('precipitaciones'),
            cotas_nieve = datos_futuros['datos'].get('cotas_nieve'),
            existencia_heladas = datos_futuros['datos'].get('existencia_heladas')
        )

        #3. Construyo el DTO de Cota de nieve
        print(f"Datos aemet : {datos_futuros}")
        cota = datos_futuros['datos'].get('cotas_nieve')
        cota_nieve = None
        if cota:
            cota_minima_match = re.search(r'^\s*(\d+)', cota)
            cota_maxima_match = re.search(r'^\s*(\d+)+\D+(\d+)', cota)
            hay_descenso = re.search(r'descenso', cota)

            cota_nieve = CotaNieveDTO(
                cota_minima = int(cota_minima_match.group(1)),
                cota_maxima= int(cota_maxima_match.group(2)),
                hay_descenso = True if hay_descenso else False,
                texto_original = cota
            )

        #4. Comprobar si el usuario quiere realizar predicciones de heladas sobre localidades
        if incluir_evaluacion_localidad:
            if cota_nieve:
                predicciones_localidad = HeladaPredictionService._evaluar_por_nieve(
                    cota_nieve = cota_nieve,
                    localidades_disponibles = datos_localidades,
                    localidades_analizar = localidades,
                    localidades_prediccion = datos_futuros['datos'].get('temperatura_localidades')
                )
            else:
                predicciones_localidad = HeladaPredictionService._evaluar_sin_cota(
                    datos = datos_futuros,
                    localidades_disponibles = datos_localidades,
                    localidades_analizar = localidades,
                    localidades_prediccion = datos_futuros['datos'].get('temperatura_localidades')
                )

            nivel_riesgo, alerta = HeladaPredictionService._nivel_riesgo_predictivo(
                predicciones_localidad
            )

            alertas.append(alerta)
            comentarios += f" Se evaluaron {predicciones_localidad.total_localidades_evaluadas} localidades."

        elif incluir_evaulacion_cultivo:
            # Entre todas las localidades con temperatura que arroja la 
            # predicción de dataservice, obtenemos la mínima
            # No tenemos los cultivos asociados a localidades
            temp_min_futura = HeladaPredictionService._temperatura_minima_futuros_calculada(
                temperaturas_localidades = datos_futuros['datos'].get('temperatura_localidades')
            )

            mes = datetime.strptime(datos_futuros['datos'].get('fecha_elaboracion'), "%Y-%m-%dT%H:%M:%S").month
            predicciones_cultivo = HeladaPredictionService._evaular_riesgo_cultivos(
                temperatura_minima = temp_min_futura,
                mes = mes,
                cultivos = cultivos
            )

            nivel_riesgo, alerta = HeladaPredictionService._nivel_riesgo_predictivo(
                predicciones_cultivo
            )

            alertas.append(alerta)
            comentarios += f" Se evaluaron {predicciones_cultivo.total_cultivos_evaluados} cultivos."

        #5. Creo el DTO de contexto de cálculo
        contexto = ContextoCalculoDTO(
            tipos_datos = [mapeo_tipo_prediccion.get(tipo_prediccion)],
            prediccion_o_estimacion = TipoResultado.ESTIMACION,
            fuente = ["AEMET"],
            fecha_generacion = datetime.now()
        )

        #6. Creación del DTO resultante
        return RiesgoHeladaFuturaDTO(
            nivel = nivel_riesgo,
            comentarios = comentarios,
            alertas = alertas,
            contexto = contexto,
            tipo_prediccion = tipo_prediccion,
            evaluaciones_cultivo = predicciones_cultivo,
            riesgos_heladas_blancas = [],
            riesgos_heladas_negras = [],
            precision = TipoPrecision.MEDIA,
            datos_meteorologicos = datos_meteorologicos,
            evaluacion_localidades = predicciones_localidad
        )
    
    @staticmethod
    def listar_cultivos_disponibles() -> list[str]:
        """
        Obtiene y devuelve la lista de cultivos disponibles
        
        :return: Lista de cultivos disponibles
        :rtype: list[str]
        """
        return listar_cultivo()
    
    @classmethod
    def listar_localidades_disponibles(cls) -> list[str]:
        """
        Obtiene y devuelve la lista de localidades disponibles
        
        :return: Lista de localidades disponibles
        :rtype: list[str]
        """
        client = cls._get_cliente()

        datos_localidades = client.get_localidades_data()

        lista_localidades = []
        for dato in datos_localidades:
            lista_localidades.append(dato['nombre_normalizado'])

        return lista_localidades
    
    @classmethod
    def obtener_predicciones_helada_observadas(
        cls,
        province_code : Optional[str],
        estacion_code : Optional[str],
        incluir_evaluacion_cultivos : bool,
        cultivos : Optional[list[str]],
        type : str
    ):
        """
        Obtiene predicciones de heladas basada en datos observados historicos
        
        :param province_code: Codigo de la provincia solicitada
        :type province_code: Optional[str]
        :param estacion_code: Codigo de la estacion solicitada
        :type estacion_code: Optional[str]
        :param incluir_evaluacion_cultivo: Decide si se evalua el riesgo en cultivos
        :type incluir_evaluacion_cultivo: bool
        :param cultivos: Lista de cultivos a evaluar
        :type cultivos: Optional[list[str]]
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
            predicciones = HeladaPredictionService._build_observadas_predictions(
                data = datos,
                fecha_inicio = fecha_inicio,
                fecha_fin = hoy,
                incluir_evaluacion_cultivo = incluir_evaluacion_cultivos,
                cultivos = cultivos
            )

        return predicciones        
    
    @classmethod
    def obtener_predicciones_helada_futuras(
        cls,
        province_code : Optional[str],
        ccaa_code : Optional[str],
        zona : str,
        prediccion : str,
        incluir_eval_localidad : bool,
        incluir_eval_cultivo : bool,
        localidades : Optional[list[str]],
        cultivos : Optional[list[str]]
    ):
        """
        Obtiene predicciones de heladas basadas en datos futuros 
        
        :param province_code: Identificador de la provincia a predecir
        :type province_code: Optional[str]
        :param ccaa_code: Identificador de la comunidad autonoma a predecir
        :type ccaa_code: Optional[str]
        :param zona: Tipo de zona sobre la que se quiere hacer la prediccion (ccaa, nacional, provincial)
        :type zona: str
        :param prediccion: Tipo de prediccion que se quiere realizar (actual, tomorrow, aftertomorrow)
        :type prediccion: str
        :param incluir_eval_localidad: Indicar si se quiere evaluar el riesgo de heladas en localidades
        :type incluir_eval_localidad: bool
        :param incluir_eval_cultivo: Indicar si se quiere evaluar el riesgo de heladas sobre cultivos
        :type incluir_eval_cultivo: bool
        :param localidades: Localidades a analizar
        :type localidades: Optional[list[str]]
        :param cultivos: Cultivos a analizar
        :type cultivos: Optional[list[str]]
        """

        client = cls._get_cliente()
        datos_futuros = client.get_future_data(
            province_code = province_code,
            ccaa_code = ccaa_code,
            zona = zona,
            prediccion = prediccion
        )

        datos_localidades = client.get_localidades_data()

        if not datos_futuros:
            raise ValueError("No se pudieron obtener datos futuros sobre dataservice")
        if not datos_localidades:
            raise ValueError("No se pudieron obtener datos de localidades sobre dataservice")
        else:
            predicciones = HeladaPredictionService._build_futuras_predicciones(
                datos_futuros = datos_futuros,
                datos_localidades = datos_localidades,
                incluir_evaluacion_localidad = incluir_eval_localidad,
                localidades = localidades if localidades else None,
                incluir_evaulacion_cultivo = incluir_eval_cultivo,
                cultivos = cultivos if cultivos else None
            )
        
        return predicciones