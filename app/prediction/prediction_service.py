from config.config import Config
from .prediction_dto import *
from typing import Optional, Union
from datetime import date, timedelta
from math import erf, sqrt
from flask import current_app
from typing import Dict, Any

import re
import time
import os
import json

class PredictionService():
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
    def log_alertas(
        datos : list[dict]
    ):
        """
        Almacena logs de alertas producidas en las predicciones
        """
        try:
            BASE_DIR = os.path.dirname(os.path.abspath(__file__))
            file_path = os.path.join(BASE_DIR, "..", "logs", "alertas_salida.json")

            with open(file_path, 'w', encoding = "utf-8") as f:
                for dato in datos:
                    f.write(
                        json.dumps(
                            {
                                'mensaje' : dato.mensaje,
                                'recomendacion' : dato.recomendacion,
                                'nivel' : dato.nivel,
                                'timestamp' : str(datetime.today())
                            },
                            indent = 4,
                            ensure_ascii = False
                        )
                    )
        except Exception as e:
            print(f"Ha ocurrido un error con el log de alertas : {e}")
            raise

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
    def calcular_nivel_riesgo_porcentaje(
        temperatura : float,
        humedad : Optional[float], 
        viento : Optional[float],
        prob_heladas : Optional[float] 
    ) -> float:
        """
        Calcula el nivel de riesgo de helada en porcentaje en base a múltiples factores
        Retorna un valor entre 0 y 100
        """

        nivel_base = 0

        # Factor de temperatura (peso de 60%)
        if temperatura <= 0:
            nivel_base += 60
        elif temperatura <= 1.6:
            nivel_base += 40
        elif temperatura <= 3.0:
            nivel_base += 20
        elif temperatura <= 5.0:
            nivel_base += 10
        else:
            nivel_base += 5

        # Factor probabilidad de helada si está disponible (30%)
        if prob_heladas is not None:
            nivel_base += prob_heladas * 30
        
        # Factor humedad para heladas blancas (10%)
        if humedad is not None:
            if humedad >= 80:
                nivel_base += 10
            elif humedad >= 60:
                nivel_base += 5
        
        # Factor viento (ajuste fino)
        if viento is not None:
            if viento < 5:  # Poco viento aumenta riesgo
                nivel_base += 5
            elif viento > 15:  # Mucho viento disminuye riesgo
                nivel_base -= 5
        
        return max(0, min(100, nivel_base))

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
            if temp_min is None or humedad_media is None:
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
                "nivel" : NivelRiesgo.SIN_RIESGO.value,
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
                humedad_min_reciente = dia.get('humedadMin')
                precipitacion_reciente = dia.get('precipitacion', 0)

        # Evaluacion de condiciones
        # 1. Precipitaciones recientes reducen riesgo de heladas
        if precipitacion_reciente >= 10 and humedad_min_reciente and humedad_min_reciente >= 70:
            return {
                "nivel" : NivelRiesgo.SIN_RIESGO.value,
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
                "nivel" : NivelRiesgo.FUERTE.value,
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
                "nivel" : NivelRiesgo.MODERADA.value,
                "alertas" : [
                    AlertaDTO(
                        mensaje = f"Temperaturas minimas de {temp_min}C detectado. Riesgo moderado de heladas",
                        recomendacion = "Revisa sistemas de protección, previniendo a toda costa los brotes nuevos o jovenes",
                        nivel = TipoAlerta.PREVENTIVA.value
                    )
                ]
            }
        elif temp_min <= 3.0:
            return {
                "nivel" : NivelRiesgo.DEBIL.value,
                "alertas" : [
                    AlertaDTO(
                        mensaje = f"Temperaturas minimas de {temp_min}C detectado. Riesgo debil de heladas",
                        recomendacion = "Mantener vigiladas las condiciones meteorológicas, especialmente durante las horas nocturnas",
                        nivel = TipoAlerta.INFORMATIVA.value
                    )
                ]
            }
        else:
            return {
                "nivel" : NivelRiesgo.SIN_RIESGO.value,
                "alertas" : []
            }
            
    @staticmethod
    def _generate_alerta_variedad(
        evaluacion_variedades : Dict
    ) -> List[AlertaDTO]:
        """
        Genera alertas especificas por variedad de cultivo en base a sus evaluaciones
        
        :param evaluacion_variedades: Datos de evaluacion sobre las variedades de cultivo solicitados
        :type evaluacion_variedades: Dict
        :return: Lista de alertas sobre cada variedad de cultivo solicitado
        :rtype: List[AlertaDTO]
        """

        nivel_riesgo = evaluacion_variedades.get('nivel_riesgo')
        variedades = evaluacion_variedades.get('variedades')
        etapa = evaluacion_variedades.get('etapa_fenologica')
        temperatura = evaluacion_variedades.get('temperatura')
        porcentaje = evaluacion_variedades.get('porcentaje_riesgo', 0)
        
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

            # Caso general para todo tipo de variedades analizado
            if nivel_riesgo == "debil":
                recomendacion_variedades = categoria_recomendacion['default']
            else:
                recomendacion_variedades = categoria_recomendacion.get(variedades.lower(), {})

            tipo_alerta = {
                "fuerte" : TipoAlerta.CRITICA,
                "moderada" : TipoAlerta.PREVENTIVA,
                "debil" : TipoAlerta.INFORMATIVA
            }.get(nivel_riesgo, TipoAlerta.INFORMATIVA)

            alerta = AlertaDTO(
                mensaje = f"Variedad {variedades} en etapa de {etapa}: riesgo {nivel_riesgo} a temperatura {temperatura:.1}C (riesgo cuantificado: {porcentaje:.0f}%)",
                recomendacion = recomendacion_variedades,
                nivel = tipo_alerta
            )
            
        return alerta

    

    @classmethod
    def _evaular_nivel_por_umbral(
        cls,
        temperatura : float,
        umbrales : list
    ) -> tuple:
        """
        Determina el nivel de riesgo y umbral activo comparando la temperatura 
        contra los umbrales de cada etapa fenologica de la variedad.

        Recorre los umbrales en orden de etapa (orden ASC) y aplica el primero cuyos
        valores de criticidad encajan con la temperatura recibida.
        El umbral con menor temperatura activa determina el nivel.

        :param temperatura: Temperatura minima a evaluar
        :type temperatura: float
        :param umbrales: Lista de diccionarios con claves critico, alto, moderado, bajo y etapa fenologica
        :type umbrales: list
        :return Tupla(nivel_riesgo: str, umbral_activo: dict) | None
        :rtype: tuple
        """
        umbrales_ordenados = sorted(
            umbrales,
            key = lambda u : u.get('etapa_fenologica', {}).get('orden', 999)
        )

        nivel = 'sin_riesgo'
        umbral_activo = None

        for umbral in umbrales_ordenados:
            critico = umbral.get('critico')
            alto = umbral.get('alto')
            moderado = umbral.get('moderado')
            bajo = umbral.get('bajo')

            # Solo evaluo umbrales que tienen al menos un valor definido
            if all(v is None for v in [critico, alto, moderado, bajo]):
                continue

            if critico is not None and temperatura <= critico:
                nivel = 'critico'
                umbral_activo = umbral
                break # Nivel maximo, no hace falta seguir
            elif alto is not None and temperatura <= alto:
                if nivel in ('sin_riesgo', 'debil', 'moderado'):
                    nivel = 'alto'
                    umbral_activo = umbral
            elif moderado is not None and temperatura <= moderado:
                if nivel in ('sin_riesgo', 'debil'):
                    nivel = 'moderado'
                    umbral_activo = umbral
            elif bajo is not None and temperatura <= bajo:
                if nivel == 'sin_riesgo':
                    nivel = 'debil'
                    umbral_activo = umbral

        return nivel, umbral_activo
    
    @classmethod
    def _evaluar_riesgo_variedades(
        cls, 
        temperatura_minima : float,
        dia : int,
        variedades : Optional[list[str]] = None
    ) -> ResumenCultivoDTO:
        """
        Evalúa el riesgo de helada para cada variedad solicitada
        obtienendo sus umbrales dinámicamente desde data-service.

        :param temperatura_minima: Temperatura minima a evaluar
        :type temperatura_minima: float
        :param dia: Dia que se usa para obtener la probabilidad de riesgo de helada posterior
        :type dia: int
        :param variedades: Lista de variedades a analizar
        :type variedades: Optional[list[str]]
        :return: DTO con resumen de variedades analizadas
        :rtype: ResumenCultivoDTO
        """

        cliente = cls._get_cliente()

        analisis_variedades = []
        riesgos = PredictionService._recuento_riesgos()

        for nombre_variedad in (variedades or []):
            # 1. Obtengo los umbrales de las variedades desde data-service
            umbrales = cliente.get_umbrales_variedad(
                nombre_variedad = nombre_variedad
            )

            # 2. Determino el nivel de riesgo comparando temperatura con umbrales
            nivel, umbral_activo = PredictionService._evaular_nivel_por_umbral(
                temperatura = temperatura_minima,
                umbrales = umbrales
            )

            etapa_nombre = (
                umbral_activo.get('etapa_fenologica', {}).get('nombre', 'Desconocida')
                if umbral_activo else 'Sin etapa fenologica'
            )

            prob_helada = PredictionService.prob_helada_posterior(
                dia = dia,
                media = Config.MEDIA_ULTIMA_HELADA,
                desviacion = Config.DESVIACION_HELADA
            )

            porcentaje_riesgo = PredictionService.calcular_nivel_riesgo_porcentaje(
                temperatura = temperatura_minima,
                humedad = None,
                viento = None,
                prob_heladas = prob_helada
            )

            # 3. Genero las alertas especificas para esta variedad
            alerta_evaluacion = PredictionService._generate_alerta_variedad(
                evaluacion_variedades = {
                    'nivel_riesgo' : nivel,
                    'variedades':  nombre_variedad,
                    'etapa_fenologica' : etapa_nombre,
                    'temperatura' : temperatura_minima,
                    'porcentaje_riesgo' : porcentaje_riesgo
                }
            )

            # 4. Actualizo contadores de riesgos
            if nivel == 'critico':
                riesgos['critico'] += 1
            elif nivel == 'alto':
                riesgos['alto'] += 1
            elif nivel == 'moderado':
                riesgos['moderado'] += 1
            elif nivel == 'debil':
                riesgos['debil'] += 1
            else:
                riesgos['sin_riesgo'] += 1

            # 5. Construyo el DTO de analisis
            umbrales_dto = None
            if umbral_activo:
                umbrales_dto = UmbralesCultivoDTO(
                    critico = umbral_activo.get('critico'),
                    alto = umbral_activo.get('alto'),
                    moderado = umbral_activo.get('moderado'),
                    bajo = umbral_activo.get('bajo')
                )

            analisis_variedades.append(
                AnalisisCultivoDTO(
                    variedad = nombre_variedad,
                    nombre_cientifico = None,
                    etapa_fenologica = etapa_nombre,
                    temperatura_evaluada = temperatura_minima,
                    nivel_riesgo = nivel,
                    umbrales = umbrales_dto,
                    porcentaje_riesgo = porcentaje_riesgo,
                    alertas = [alerta_evaluacion] if alerta_evaluacion else []
                )
            )
        
        return ResumenCultivoDTO(
            total_variedades_evaluados = len(analisis_variedades),
            variedades_en_riesgo_critico = riesgos['critico'],
            variedades_en_riesgo_alto = riesgos['alto'],
            variedades_en_riesgo_moderado = riesgos['moderado'],
            variedades_en_riesgo_debil = riesgos['debil'],
            variedades_sin_riesgo = riesgos['sin_riesgo'],
            evaluaciones = analisis_variedades 
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

        riesgos = PredictionService._recuento_riesgos()
        lista_analisis = []
        nivel_riesgo = None

        datos_localidades_analizar = []
        datos_localidades_analizar = [
            localidad
            for localidad in localidades_disponibles
            if localidad['nombre_normalizado'] in localidades_analizar
        ]
        print(datos_localidades_analizar)
        
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
                    if l['nombre'] == localidad['nombre']
                ),
                None
            )

            if not localidades_pred:    
                continue
                
            temperatura_minima = localidades_pred['temperatura_minima']
            temperatura_maxima = localidades_pred['temperatura_maxima']
            altitud = localidad['altitud']
            precipitaciones = datos['datos'].get('precipitaciones')
            existencia_nieblas = datos['datos'].get('aparicion_nieblas')
            cota_nieve : CotaNieveDTO = None
            score = 0

            # Análisis de temperatura
            if temperatura_minima < 0.0: # No necesita más factores para considerar riesgo crítico de heladas
                score += 4
                recomendaciones.append("Temperaturas minimas bajo cero previstas. Altas probabilidades de heladas")
            elif temperatura_minima == 0.0:
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

            # Calcular porcentaje de riesgo
            procentaje_riesgo = PredictionService.calcular_nivel_riesgo_porcentaje(
                temperatura = temperatura_minima,
                humedad = 70 if existencia_nieblas else 50,
                viento = datos['datos'].get('rachas_viento', 0),
                prob_heladas = None
            )

            lista_analisis.append(
                AnalisisLocalidadDTO(
                    localidad = localidad['nombre'],
                    provincia = localidad['provincia'],
                    altitud_metros = altitud,
                    temperatura_minima = temperatura_minima,
                    temperatura_maxima = temperatura_maxima,
                    nivel_riesgo = nivel_riesgo,
                    porcentaje_riesgo = procentaje_riesgo,
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
        
        riesgos = PredictionService._recuento_riesgos()

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
                    riesgos['critico'] += 1
                    nivel_riesgo = 'critico'
                    recomendaciones.append(
                        f"La cota de nieve esta en descenso y la localidad {localidad['nombre']} se encuentra dentro del rango de altitud afectado."
                    )
                else:
                    riesgos['moderado'] += 1
                    nivel_riesgo = 'moderado'
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


            lista_analisis.append(
                AnalisisLocalidadDTO(
                    localidad=localidad['nombre'],
                    provincia=localidad['provincia'],
                    altitud_metros=altitud,
                    temperatura_minima=temperatura_minima,
                    temperatura_maxima=temperatura_maxima,
                    porcentaje_riesgo = 60,
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
    ) -> Union[NivelRiesgo, AlertaDTO]:
        if isinstance(prediccion, ResumenEvaluacionLocalidadDTO):
            if prediccion.localidades_riesgo_critico > 0:
                return NivelRiesgo.FUERTE, AlertaDTO(
                    mensaje = "Riesgo crítico de heladas en las próximas horas.",
                    recomendacion = (
                        "Posibles temperaturas bajo cero con impacto significativo. "
                        "Extremar precauciones en carretera, proteger tuberías y "
                        "evitar exposición prolongada al frío."
                    ),
                    nivel = TipoAlerta.CRITICA
                )
            elif prediccion.localidades_riesgo_alto > 0:
                return NivelRiesgo.MODERADA, AlertaDTO(
                    mensaje = "Alta probabilidad de heladas localizadas.",
                    recomendacion = (
                        "Posible formación de placas de hielo en zonas elevadas y umbrías. "
                        "Conducir con precaución y revisar previsiones actualizadas."
                    ),
                    nivel = TipoAlerta.ALTA
                )
            elif prediccion.localidades_riesgo_moderado > 0:
                return NivelRiesgo.DEBIL, AlertaDTO(
                    mensaje = "Probabilidad moderada de heladas débiles.",
                    recomendacion = (
                        "Heladas puntuales en zonas rurales o de mayor altitud. "
                        "Se recomienda seguimiento preventivo."
                    ),
                    nivel = TipoAlerta.MEDIA
                )
            else:
                return NivelRiesgo.SIN_RIESGO, AlertaDTO(
                    mensaje = "Sin riesgo significativo de heladas.",
                    recomendacion = "No se requieren medidas especiales.",
                    nivel = TipoAlerta.INFORMATIVA
                )   

        elif isinstance(prediccion, ResumenCultivoDTO):
            if prediccion.variedades_en_riesgo_critico > 0:
                return NivelRiesgo.FUERTE, AlertaDTO(
                    mensaje = "Riesgo crítico de daños por helada en cultivos sensibles.",
                    recomendacion = (
                        "Se recomienda activar medidas de protección: riego antihelada, "
                        "cubiertas térmicas o sistemas de ventilación. "
                        "Especial atención a brotes y floración."
                    ),
                    nivel = TipoAlerta.CRITICA
                )
            elif prediccion.variedades_en_riesgo_alto > 0:
                return NivelRiesgo.MODERADA, AlertaDTO(
                    mensaje = "Riesgo elevado de estrés térmico en cultivos.",
                    recomendacion = (
                        "Monitorizar temperaturas nocturnas y preparar sistemas de protección "
                        "si el cultivo se encuentra en fase sensible."
                    ),
                    nivel = TipoAlerta.PREVENTIVA
                )
            elif prediccion.variedades_en_riesgo_moderado > 0:
                return NivelRiesgo.DEBIL, AlertaDTO(
                    mensaje = "Riesgo leve de helada en algunos cultivos.",
                    recomendacion = (
                        "No se esperan daños generalizados, pero conviene vigilar "
                        "cultivos tempranos o en fase de brotación."
                    ),
                    nivel = TipoAlerta.INFORMATIVA
                )
            else:
                return NivelRiesgo.SIN_RIESGO, AlertaDTO(
                    mensaje = "Condiciones térmicas favorables para los cultivos.",
                    recomendacion = "No se prevén daños por helada.",
                    nivel = TipoAlerta.INFORMATIVA
                )
    
    @staticmethod
    def _build_observadas_predictions(
        data,
        fecha_inicio : date,
        fecha_fin : date,
        incluir_evaluacion_variedades : bool,
        variedades : Optional[list[str]] = None            
    ) -> RiesgoHeladaObservadaDTO:
        """
        Construye los DTOs de predicciones de heladas sobre datos observados
        
        :param data: Datos historicos observados
        :param fecha_inicio: Fecha de inicio del periodo analizado
        :type fecha_inicio: date
        :param fecha_fin: Fecha de finalización del periodo analizado
        :type fecha_fin: date
        :param incluir_evaluacion_variedades: Decide si se debe evaluar el riesgo en varieades o no
        :type incluir_evaluacion_variedades: bool
        :param variedades: Lista de variedes de cultivo a analizar (opcional)
        :type variedades: Optional[list[str]]
        :return: DTO cargado
        :rtype: RiesgoHeladaDTO
        """

        # 1. Obtención de datos calculados sobre temperaturas minimas
        stats_temp = PredictionService._datos_historicos_calculados_temp(
            datos = data
        )

        registro_temp_min = RegistroTempMinDTO(
            dias_bajo_cero = stats_temp['dias_bajo_cero'],
            temperatura_minima_registrada = stats_temp['temperatura_minima_absoluta'],
            fecha_temp_bajo_cero = stats_temp['timestamps_bajo_cero']
        )

        # 2. Identificación sobre tipo de heladas
        heladas_blancas_list, heladas_negras_list = PredictionService._riesgo_tipo_helada(
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
        riesgos_generales = PredictionService._determinar_nivel_riesgo(
            datos = data
        )

        # 4. Calculo probabilidad estadística de heladas tardías
        prob_helada = 0.0
        if stats_temp['fecha_temp_min_abs']:
            dia_juliano_temp_min = PredictionService.dia_juliano(
                fecha = stats_temp['fecha_temp_min_abs']
            )
            prob_helada = PredictionService.prob_helada_posterior(
                dia = dia_juliano_temp_min,
                media = Config.MEDIA_ULTIMA_HELADA,
                desviacion = Config.DESVIACION_HELADA 
            ) * 100 # Obtengo el porcentaje

        # 5. Evaluación de variedades de cultivo
        evaluacion_variedades = None
        if incluir_evaluacion_variedades and stats_temp['temperatura_minima_absoluta']:
            evaluacion_variedades = PredictionService._evaluar_riesgo_variedades(
                temperatura_minima = stats_temp['temperatura_minima_absoluta'],
                dia = fecha_fin.day,
                variedades = variedades
            )

        # 6. Generación del contexto
        comentarios = (
            f"Analisis basado en {stats_temp['dias']} dias de datos historicos "
            f"desde {fecha_inicio.strftime('%d/%m/%Y')} hasta {fecha_fin.strftime('%d/%m/%Y')}. "
        )

        if stats_temp['temperatura_minima_absoluta'] is not None:
            comentarios += f"Temperatura minima registrada: {stats_temp['temperatura_minima_absoluta']:.1f}C. "
        
        # Se indica si o si la probabilidad obtenida de heladas, independientemente de que sea 0
        if prob_helada > 0.0 or prob_helada == 0:
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

        # Almaceno las alertas producidas en la prediccion en un log
        PredictionService.log_alertas(
            datos = riesgos_generales['alertas']
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
            evaluaciones_variedades = evaluacion_variedades
        )
    
    @classmethod
    def aplicar_condiciones_horas_frio(
        cls,
        variedades : list[str],
        nivel_riesgo_actual : NivelRiesgo,
        alertas : list
    ) -> tuple:
        """
        Consulta las horas de frío acumuladas de cada variedad y, si alguna
        no ha completado su requerimiento mínimo, escala el nivel de riesgo
        y añade una alerta específica.

        La lógica de escalado es:
        - Variedad con < 50% de horas_frio_min: +2 niveles (SIN_RIESGO→MODERADA,
          DEBIL→FUERTE, etc.)
        - Variedad con 50-99% de horas_frio_min: +1 nivel
        - Variedad con >= horas_frio_min: sin cambio, alerta informativa si ya
          superó el máximo (posible invernalización excesiva)

        Solo se escala hasta FUERTE como máximo. El escalado más severo encontrado
        entre todas las variedades es el que prevalece.

        :param variedades: Nombres de variedades a consultar
        :type variedades: list[str]
        :param nivel_riesgo_actual: Nivel de riesgo calculado antes de este condicionante
        :type nivel_riesgo_actual: NivelRiesgo
        :param alertas: Lista de alertas acumuladas hasta ahora (se añaden in-place)
        :type alertas: list
        :return: Tupla (nivel_riesgo_final: NivelRiesgo, alertas: list)
        :rtype: tuple
        """
        client = cls._get_cliente()

        # Escala ordinal para poder hacer aritmética de niveles
        escala = [
            NivelRiesgo.SIN_RIESGO,
            NivelRiesgo.DEBIL,
            NivelRiesgo.MODERADA,
            NivelRiesgo.FUERTE
        ]

        max_escalado = 0  # Máximo número de niveles a subir por horas de frío

        for nombre_variedad in variedades:
            datos_hf = client.get_horas_frio_variedad(
                nombre_variedad = nombre_variedad
            )

            if not datos_hf:
                alertas.append(AlertaDTO(
                    mensaje = f"No se pudieron obtener las horas de frío de '{nombre_variedad}'. ",
                    recomendacion = "Verificar disponibilidad de datos en data-service.",
                    nivel = TipoAlerta.INFORMATIVA
                ))
                continue

            hf_min = datos_hf.get('horas_frio_min')
            hf_max = datos_hf.get('horas_frio_max')
            hf_actuales = datos_hf.get('horas_frio_actuales')

            if hf_min is None or hf_actuales is None:
                alertas.append(AlertaDTO(
                    mensaje = f"Datos de horas de frío incompletos para '{nombre_variedad}'.",
                    recomendacion = "Revisar configuración de umbrales en data-service.",
                    nivel = TipoAlerta.INFORMATIVA
                ))
                continue

            porcentaje_completado = (hf_actuales / hf_min) * 100 if hf_min > 0 else 100

            if porcentaje_completado < 50:
                # Variedad muy lejos de su requerimiento: muy vulnerable
                escalado = 2
                alertas.append(AlertaDTO(
                    mensaje = (
                        f"La variedad '{nombre_variedad}' solo ha acumulado {hf_actuales:.1f} "
                        f"de {hf_min} horas de frío requeridas ({porcentaje_completado:.0f}%). "
                        "La planta no ha completado su vernalización y es extremadamente "
                        "sensible a heladas."
                    ),
                    recomendacion = (
                        "Aplicar protección activa: cobertura térmica y/o riego antihelada. "
                        "La falta de vernalización aumenta significativamente el daño potencial."
                    ),
                    nivel = TipoAlerta.CRITICA
                ))

            elif porcentaje_completado < 100:
                # Variedad en proceso de vernalización: sensibilidad elevada
                escalado = 1
                alertas.append(AlertaDTO(
                    mensaje = (
                        f"La variedad '{nombre_variedad}' ha acumulado {hf_actuales:.1f} "
                        f"de {hf_min} horas de frío requeridas ({porcentaje_completado:.0f}%). "
                        "La vernalización está incompleta, lo que incrementa su vulnerabilidad."
                    ),
                    recomendacion = (
                        "Mantener vigilancia sobre las temperaturas nocturnas y preparar "
                        "medidas de protección preventivas."
                    ),
                    nivel = TipoAlerta.PREVENTIVA
                ))

            else:
                # Vernalización completa
                escalado = 0
                mensaje_hf = (
                    f"La variedad '{nombre_variedad}' ha completado su requerimiento "
                    f"de horas de frío ({hf_actuales:.1f} / {hf_min})."
                )
                # Advertencia adicional si se ha superado el máximo
                if hf_max is not None and hf_actuales > hf_max:
                    mensaje_hf += (
                        f" AVISO: se han superado las {hf_max} horas máximas recomendadas "
                        f"({hf_actuales:.1f} acumuladas). Posible vernalización excesiva."
                    )
                    alertas.append(AlertaDTO(
                        mensaje = mensaje_hf,
                        recomendacion = "Consultar con el técnico agronómico sobre el impacto de la vernalización excesiva.",
                        nivel = TipoAlerta.PREVENTIVA
                    ))
                else:
                    alertas.append(AlertaDTO(
                        mensaje = mensaje_hf,
                        recomendacion = "No se requieren medidas adicionales por horas de frío.",
                        nivel = TipoAlerta.INFORMATIVA
                    ))

            max_escalado = max(max_escalado, escalado)

        # Aplicamos el escalado más severo encontrado
        if max_escalado > 0:
            indice_actual = escala.index(nivel_riesgo_actual) if nivel_riesgo_actual in escala else 0
            indice_final = min(indice_actual + max_escalado, len(escala) - 1)
            nivel_final = escala[indice_final]

            if nivel_final != nivel_riesgo_actual:
                alertas.append(AlertaDTO(
                    mensaje = (
                        f"El nivel de riesgo ha sido escalado de {nivel_riesgo_actual.value} "
                        f"a {nivel_final.value} por el condicionante de horas de frío insuficientes."
                    ),
                    recomendacion = "Revisar el estado fenológico de las variedades afectadas.",
                    nivel = TipoAlerta.ALTA
                ))
        else:
            nivel_final = nivel_riesgo_actual

        return nivel_final, alertas

    @staticmethod
    def _build_futuras_predicciones(
        datos_futuros,
        datos_localidades,
        incluir_evaluacion_localidad : bool,
        localidades : Optional[list[str]],
        incluir_evaulacion_variedades : bool,
        variedades : Optional[list[str]]
    ) -> RiesgoHeladaFuturaDTO:
        """
        Genera el DTO de predicciones futuras de heladas sobre los datos recopilados
        
        :param datos_futuros: Datos futuros obtenidos de AEMET
        :param datos_localidades: Datos de localidades disponibles
        :param incluir_evaluacion_localidad: Condicionante para determinar la evaluación de riesgos de helada por localidad
        :type incluir_evaluacion_localidad: bool
        :param localidades: Lista de localidades a evaluar
        :type localidades: Optional[list[str]]
        :param incluir_evaulacion_variedades: Condicionante para determinar la evaluación de riesgo de heladas sobre variedades de cultivo
        :type incluir_evaulacion_variedades: bool
        :param variedades: Lista de variedades de cultivo a evaluar
        :type variedades: Optional[list[str]]
        :return: DTO resultante con los datos recopilados importantes a enviar
        :rtype: RiesgoHeladaFuturaDTO
        """
        
        nivel_riesgo = None
        comentarios = "Predicciones futuras basadas en datos proporcionados por AEMET."
        alertas = []
        predicciones_variedad = None
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
        cota = datos_futuros['datos'].get('cotas_nieve')
        cota_nieve = None
        if cota:
            # 1er respaldo
            cota_minima_match = re.search(r'^\s*(\d+)', cota)
            cota_maxima_match = re.search(r'^\s*(\d+)+\D+(\d+)', cota)

            if (cota_maxima_match and cota_minima_match) is None:
                cota_match = re.search(r'(\d+)-(\d+)', cota) # 2do respaldo
            
            hay_descenso = re.search(r'descenso', cota)
            cota_nieve = CotaNieveDTO(
                cota_minima = int(cota_minima_match.group(1)) if cota_minima_match else int(cota_match.group(1)),
                cota_maxima= int(cota_maxima_match.group(2)) if cota_maxima_match else int(cota_match.group(2)),
                hay_descenso = True if hay_descenso else False,
                texto_original = cota
            )

        #4. Comprobar si el usuario quiere realizar predicciones de heladas sobre localidades
        if incluir_evaluacion_localidad:
            if cota_nieve:
                predicciones_localidad = PredictionService._evaluar_por_nieve(
                    cota_nieve = cota_nieve,
                    localidades_disponibles = datos_localidades,
                    localidades_analizar = localidades,
                    localidades_prediccion = datos_futuros['datos'].get('temperatura_localidades')
                )
            else:
                predicciones_localidad = PredictionService._evaluar_sin_cota(
                    datos = datos_futuros,
                    localidades_disponibles = datos_localidades,
                    localidades_analizar = localidades,
                    localidades_prediccion = datos_futuros['datos'].get('temperatura_localidades')
                )

            nivel_riesgo, alerta = PredictionService._nivel_riesgo_predictivo(
                predicciones_localidad
            )

            alertas.append(alerta)
            comentarios += f" Se evaluaron {predicciones_localidad.total_localidades_evaluadas} localidades."

        elif incluir_evaulacion_variedades:
            # Entre todas las localidades con temperatura que arroja la 
            # predicción de dataservice, obtenemos la mínima
            # No tenemos las variedades asociados a localidades
            temp_min_futura = PredictionService._temperatura_minima_futuros_calculada(
                temperaturas_localidades = datos_futuros['datos'].get('temperatura_localidades')
            )

            dia = datetime.strptime(datos_futuros['datos'].get('fecha_elaboracion'), "%Y-%m-%dT%H:%M:%S").day
            predicciones_variedad = PredictionService._evaluar_riesgo_variedades(
                temperatura_minima = temp_min_futura,
                dia = dia,
                variedades = variedades
            )

            nivel_riesgo, alerta = PredictionService._nivel_riesgo_predictivo(
                predicciones_variedad
            )

            if variedades and len(variedades) > 0:
                nivel_riesgo_ajustado, alertas_actualizadas = PredictionService.aplicar_condiciones_horas_frio(
                    variedades = variedades,
                    nivel_riesgo_actual = nivel_riesgo,
                    alertas = alertas
                )
                nivel_riesgo = nivel_riesgo_ajustado
                alertas = alertas_actualizadas

            alertas.append(alerta)
            comentarios += f" Se evaluaron {predicciones_variedad.total_variedades_evaluados} variedades de cultivo."

        #5. Creo el DTO de contexto de cálculo
        contexto = ContextoCalculoDTO(
            tipos_datos = [mapeo_tipo_prediccion.get(tipo_prediccion)],
            prediccion_o_estimacion = TipoResultado.ESTIMACION,
            fuente = ["AEMET"],
            fecha_generacion = datetime.now()
        )

        #6. Almacenar las alertas en el log
        PredictionService.log_alertas(
            datos = alertas
        )

        #7. Creación del DTO resultante
        return RiesgoHeladaFuturaDTO(
            nivel = nivel_riesgo,
            comentarios = comentarios,
            alertas = alertas,
            contexto = contexto,
            tipo_prediccion = tipo_prediccion,
            evaluaciones_variedades = predicciones_variedad,
            riesgos_heladas_blancas = [],
            riesgos_heladas_negras = [],
            precision = TipoPrecision.MEDIA,
            datos_meteorologicos = datos_meteorologicos,
            evaluacion_localidades = predicciones_localidad
        )

    @classmethod
    def listar_variedades_disponibles(
        cls
    ) -> list[str]:
        """
        Obtiene y devuelve la lista de variedades disponibles
        
        :return: Lista de variedades disponibles
        :rtype: list[str]
        """
        client = cls._get_cliente()
        datos = client.get_variedades()

        if not datos:
            return []

        return datos

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
        incluir_evaluacion_variedades : bool,
        variedades : Optional[list[str]],
        type : str
    ):
        """
        Obtiene predicciones de heladas basada en datos observados historicos
        
        :param province_code: Codigo de la provincia solicitada
        :type province_code: Optional[str]
        :param estacion_code: Codigo de la estacion solicitada
        :type estacion_code: Optional[str]
        :param incluir_evaluacion_variedades: Decide si se evalua el riesgo en variedades de cultivo
        :type incluir_evaluacion_variedades: bool
        :param variedades: Lista de variedades de cultivo a evaluar
        :type variedades: Optional[list[str]]
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
            predicciones = PredictionService._build_observadas_predictions(
                data = datos,
                fecha_inicio = fecha_inicio,
                fecha_fin = hoy,
                incluir_evaluacion_variedades = incluir_evaluacion_variedades,
                variedades = variedades
            )

        return predicciones        
    
    @classmethod
    def obtener_predicciones_helada_futuras(
        cls,
        province_code : Optional[str],
        ccaa_code : Optional[str],
        zona : str,
        incluir_eval_localidad : bool,
        incluir_eval_variedades : bool,
        localidades_normalizadas : Optional[list[str]],
        variedades : Optional[list[str]]
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
        :param incluir_eval_variedades: Indicar si se quiere evaluar el riesgo de heladas sobre variedades de cultivos
        :type incluir_eval_variedades: bool
        :param localidades_normalizadas: Localidades a analizar configuradas con un buen formato
        :type localidades_normalizadas: Optional[list[str]]
        :param variedades: Variedades de cultivos a analizar
        :type variedades: Optional[list[str]]
        """

        client = cls._get_cliente()
        datos_futuros = client.get_future_data(
            province_code = province_code,
            ccaa_code = ccaa_code,
            zona = zona,
            prediccion = "tomorrow"
        )
        # Comprobar el estado de la carga de datos antes de obtener los datos de data-service
        if datos_futuros.get('status') == "PENDING":
            time.sleep(5) # Después de ese tiempo ya deberían estar cargados los datos en la base de datos
            datos_futuros = client.get_future_data(
                province_code = province_code,
                ccaa_code = ccaa_code,
                zona = zona,
                prediccion = "tomorrow"
            )

        datos_localidad = None # Almacena datos de localidades de data-service, servirán para generar predicciones basadas en cotas de nieve

        if incluir_eval_localidad:
            datos_localidad = client.get_localidades_data()

        if not datos_futuros:
            raise ValueError("No se pudieron obtener datos futuros sobre dataservice")
        elif incluir_eval_localidad and not datos_localidad:
            raise ValueError("No se pudieron obtener datos de localidades sobre dataservice")
        else:
            predicciones = PredictionService._build_futuras_predicciones(
                datos_futuros = datos_futuros,
                datos_localidades = datos_localidad if datos_localidad else None,
                incluir_evaluacion_localidad = True if incluir_eval_localidad else False,
                localidades = localidades_normalizadas if localidades_normalizadas else None,
                incluir_evaulacion_variedades = True if incluir_eval_variedades else False,
                variedades = variedades if variedades else None
            )

        return predicciones