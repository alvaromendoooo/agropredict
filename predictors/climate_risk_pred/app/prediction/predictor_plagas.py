from datetime import datetime, date, timedelta
from .plague_evaluate import EvaluarPlaga
from .prediction_dto import RiesgoPlagaCultivoDTO, PlagaDTO, CultivoDTO
from typing import Optional
from flask import current_app

class PredictorPlagasService:

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
    def _build_cultivo_plagas_calculadas(
        datos : list[dict]
    ) -> Optional[list[RiesgoPlagaCultivoDTO]]:
        """
        Convierte en DTOs de tipo RiesgoPlagaCultivoDTO todos los 
        datos obtenidos por parámetros

        :param datos: Lista de datos obtenidos
        :type datos: list[dict]
        :return: DTO cargado
        :rtype: Optional[RiesgoPlagaCultivoDTO]
        """

        if not datos:
            return None

        lista_dtos = []
        for dato in datos:
            lista_dtos.append(
                RiesgoPlagaCultivoDTO(
                    cultivo = CultivoDTO(
                        nombre = dato['cultivo'],
                        grupo = dato['grupo']
                    ),
                    plagas = [
                        PlagaDTO(
                            nombre = p['nombre'],
                            agente_causante = p['agente_causante'],
                            momento_critico = p['momento_critico'],
                            observaciones = p['observaciones'],
                            mas_info = p['mas_info'],
                            tipo = p['tipo'],
                            nivel_riesgo = p['nivel_riesgo']
                        )
                        for p in dato['plagas']
                    ]
                )
            )
        
        return lista_dtos

    @classmethod
    def obtener_prediccion_plagas_calculadas(
        cls,
        cultivos : list[str]
    ):
        """
        Realiza el cálculo de predicción sobre riesgos de plagas, sobre datos proporcionados 
        por data-service e itacyl. No necesita controlar variables climáticas porque la 
        precisión ya calculada viene de los datos obtenidos.

        :param cultivos: Lista de nombres de cultivos a predecir
        :type cultivos: list[str]
        """

        if not cultivos:
            return None
        
        cliente = cls._get_cliente()
        data = cliente.get_cultivo_plaga_calendar(
            nombres_cultivos = cultivos
        )

        # Obtención de la semana actual para construir la lógica del método
        semana = datetime.today().isocalendar()[1] # Obtengo la semana que me devuelve la ISO 8601

        # Obtención de los niveles de riesgos para la semana en la que nos encontramos
        riesgos_plagas = []

        for d in data:
            plagas = d['plaga']
            plagas_dict = {}
            for p in plagas:
                calendario = p['calendario']
                objeto_riesgo = next((r for r in calendario if r['semana'] == semana), None)

                riesgo = objeto_riesgo['nivel_alerta']

                if 0 <= riesgo < 50:
                    importancia = 'BAJA'
                elif 50 <= riesgo < 75:
                    importancia = 'MEDIA'
                else:
                    importancia = 'ALTA'

                if p['public_id'] not in plagas_dict:
                    plagas_dict[p['public_id']] = {
                        'nombre' : p['nombre'],
                        'agente_causante' : p['agente_causante'],
                        'momento_critico' : p['momento_critico'],
                        'observaciones' : p['observaciones'],
                        'mas_info' : p['mas_info'],
                        'tipo' : p['tipo'],
                        'nivel_riesgo' : importancia 
                    }

            riesgos_plagas.append(
                {
                    'cultivo' : d['cultivo']['nombre'],
                    'grupo' : d['cultivo']['grupo'],
                    'plagas' : list(plagas_dict.values())
                }
            )

        predicciones_plagas = PredictorPlagasService._build_cultivo_plagas_calculadas(
            datos = riesgos_plagas
        )

        if not predicciones_plagas:
            return None
        
        return predicciones_plagas
    

    @staticmethod
    def _transformar_datos_sensores(
        datos_sensores: list
    ) -> dict:               
        """
        Transforma la respuesta del servicio de sensores al formato
        que espera EvaluarPlaga: {date: {nombre_predictor: valor}}
        """
        datos_por_dia = {}
        for sensor in datos_sensores:
            for resultado in sensor.get('datos_recopilados').get('resultados', []):
                timestamp_str = resultado.get('timestamp')
                campo = resultado.get('campo')   # ya viene como nombre_predictor
                valor = resultado.get('valor')

                fecha = datetime.fromisoformat(
                    timestamp_str.replace('Z', '+00:00')
                ).date()

                if fecha not in datos_por_dia:
                    datos_por_dia[fecha] = {}

                datos_por_dia[fecha][campo] = valor

        return datos_por_dia
    
    
    @staticmethod
    def _hay_plagas_con_ventana_deslizante(plaga):
        ventanas = plaga.get('ventana_temporal')
        if not ventanas:
            return False
        return any(
            v.get('modo') == 'acumulacion_gdd' and
            (v.get('dias_ventana') is not None or v.get('fecha_inicio_acumulacion') is not None)
            for v in ventanas
        )

    @classmethod
    def _obtener_datos_temporales_siar(
        cls,
        cliente, 
        fecha_inicio,
        fecha_fin,
        codigo_estacion, 
        codigo_provincia,
        dias_temporales
    ):
        datos_siar_por_fecha = None
        datos_siar_acumulados = {}

        """
        Obtención de datos climáticos sobre SiAR para fechas asociadas a ventanas temporales 
        en acumulacion_gdd y en simple, permitiendo generar evaluaciones simples como 
        base informativa
        """
        # Obtengo los datos de SiAR sobre el periodo de días indicado en la ventana temporal
        fecha_inicio_extendido = fecha_inicio - timedelta(days = dias_temporales)
        datos_siar_completos_extendidos = cls._obtener_datos_siar(
            cliente          = cliente,
            fecha_inicio     = fecha_inicio_extendido,
            fecha_fin        = fecha_fin,
            codigo_estacion  = codigo_estacion,
            codigo_provincia = codigo_provincia 
        )

        # Para evaluación simple
        datos_siar_por_fecha = {
            fecha : datos
            for fecha, datos in datos_siar_completos_extendidos.items()
            if fecha_inicio <= fecha <= fecha_fin
        }

        datos_siar_acumulados = {}
        fecha_actual = fecha_inicio
        while fecha_actual <= fecha_fin:
            fecha_ventana_inicio = fecha_actual - timedelta(days=dias_temporales)
            datos_siar_acumulados[fecha_actual] = {
                fecha: datos
                for fecha, datos in datos_siar_completos_extendidos.items()
                if fecha_ventana_inicio <= fecha <= fecha_actual
            }
            fecha_actual += timedelta(days=1)
        
        return datos_siar_acumulados, datos_siar_por_fecha

    @classmethod
    def obtener_prediccion_plagas_estimadas(
        cls, 
        cultivo: str, 
        datos_sensores : list, 
        fecha_inicio, 
        fecha_fin, 
        id_plaga : Optional[str] = None,
        codigo_estacion : Optional[str] = None,
        codigo_provincia : Optional[str] = None,):
        """
        Calcula predicción de plagas para un cultivo en un rango de fechas
        
        :param cultivo: Nombre del cultivo
        :param datos_sensores: Lista de EUIs de sensores
        :param fecha_inicio: Fecha de inicio (date object)
        :param fecha_fin: Fecha de fin (date object)
        """
        try:
            cliente = cls._get_cliente()
            registro_datos_dtagro = []

            # 1. Obtener plagas del cultivo
            plagas_cultivos = cliente.get_plagas_por_cultivo(cultivo.capitalize(), id_plaga)

            # Lista plana de todas las plagas
            plagas = [p for cultivo_data in plagas_cultivos for p in cultivo_data.get('plaga', [])]

            # Separar las que tienen ventana GDD de las que no
            plagas_con_gdd = [p for p in plagas if PredictorPlagasService._hay_plagas_con_ventana_deslizante(p)]
            plagas_sin_gdd = [p for p in plagas if not PredictorPlagasService._hay_plagas_con_ventana_deslizante(p)]

            # Calcular el máximo dias_ventana solo sobre las que lo necesitan
            max_dias_ventana = max(
                v.get('dias_ventana', 0)
                for p in plagas_con_gdd
                for v in p.get('ventana_temporal', [])
                if v.get('modo') == 'acumulacion_gdd' and v.get('dias_ventana') is not None
            ) if plagas_con_gdd else 0

            # Amplio el rango de fechas solo si es necesario por la aparición de acumuladas_gdd 
            fecha_inicio_sensores = fecha_inicio - timedelta(days=max_dias_ventana) if max_dias_ventana > 0 else fecha_inicio

            # 2. Obtener datos de sensores para todo el rango
            for dato_sensor in datos_sensores:
                datos_dtagro = cliente.get_datos_sensores(
                    eui              = dato_sensor['sensor'],
                    fecha_inicio     = fecha_inicio_sensores,
                    fecha_fin        = fecha_fin,
                    nombre_dtagro    = dato_sensor['nombre_dt_agro'],
                    nombre_predictor = dato_sensor['nombre_predictor_plaga']
                )
                diccionario_dato_dtagro = { # Mantengo una relación de metadatos de sensor junto con sus valores, para distinguir los valores de cada uno
                    'sensor' : dato_sensor['sensor'],
                    'nombre_dtagro' : dato_sensor['nombre_dt_agro'],
                    'nombre_predictor' : dato_sensor['nombre_predictor_plaga'],
                    'datos_recopilados' : datos_dtagro
                }

                registro_datos_dtagro.append(diccionario_dato_dtagro)

            # 3. Construir diccionario de datos por día (priorizando sensores)
            datos_por_dia_sensores = PredictorPlagasService._transformar_datos_sensores(registro_datos_dtagro)

            # 4. Obtener datos meteorológicos SiAR (si están disponibles). Dependiendo del tipo de plaga a evaluar, se realizará sobre el día de hoy 
            # o sobre una fecha determinada
            datos_siar_por_fecha_periodica, datos_siar_por_fecha = cls._obtener_datos_temporales_siar(
                cliente          = cliente,
                fecha_inicio     = fecha_inicio,
                fecha_fin        = fecha_fin,
                codigo_estacion  = codigo_estacion,
                codigo_provincia = codigo_provincia,
                dias_temporales  = max_dias_ventana,
            )

            if not plagas_cultivos:
                raise ValueError(f"No se encontraron plagas para el cultivo: {cultivo}")

            # 5. Evaluar cada plaga
            resultado_por_plaga = []
            delta_dias = (fecha_fin - fecha_inicio).days

            for plaga_cultivo in plagas_cultivos:
                for plaga_config in plaga_cultivo['plaga']:

                    registro_probabilidades = []
                    for i in range(delta_dias + 1):
                        dia_actual = fecha_inicio + timedelta(days=i)

                        # Si se decide evaluar con un algoritmo adhoc, se hace una llamada externa a ese algoritmo
                        if plaga_config['algoritmo'] == "adhoc" and plaga_config.get('algoritmo_url'):
                            alerta_dia = EvaluarPlaga.evaluar_algoritmo_externo(
                                url = plaga_config.get('algoritmo_url'),
                                datos = datos_por_dia_sensores.get(dia_actual, {}),
                                plaga = plaga_config,
                                fecha = dia_actual
                            )
                        else:
                            # Pasar los datos meteorológicos del día específico
                            datos_meteo_dia = datos_siar_por_fecha.get(dia_actual, {})

                            alerta_dia = EvaluarPlaga.evaluar_plaga_generica(
                                condiciones_evaluables = plaga_config.get('condiciones_evaluables'),
                                datos_por_dia          = datos_por_dia_sensores,
                                fecha_evaluacion       = dia_actual,
                                plaga                  = plaga_config,
                                meteo_dia              = datos_meteo_dia,  # Solo datos del día actual
                                meteo_periodica        = datos_siar_por_fecha_periodica # Datos ampliados con el periodo de la ventana temporal
                            )

                        registro_probabilidades.append({
                            "fecha": dia_actual.strftime('%Y-%m-%d'),
                            "nivel_riesgo": alerta_dia.nivel.value,
                            "mensaje": alerta_dia.mensaje,
                            "condiciones_cumplidas": alerta_dia.condiciones_cumplidas,
                            "condiciones_pendientes": alerta_dia.condiciones_pendientes
                        })

                    resultado_por_plaga.append({
                        "plaga_id": plaga_config['public_id'],
                        "nombre": plaga_config['nombre'],
                        "tipo": plaga_config['tipo'],
                        "ventana_temporal": plaga_config.get('ventana_temporal', []),
                        "condiciones_evaluables": plaga_config.get('condiciones_evaluables', []),
                        "datos_probabilidad": registro_probabilidades
                    })

            return {
                "cultivo": cultivo,
                "fecha_inicio": fecha_inicio.strftime('%Y-%m-%d'),
                "fecha_final": fecha_fin.strftime('%Y-%m-%d'),
                "plagas_evaluadas": resultado_por_plaga
            }

        except Exception as e:
            current_app.logger.error(f"Error en predicción estimada: {e}", exc_info=True)
            raise

    @classmethod
    def _obtener_datos_siar(cls, cliente, fecha_inicio: date, fecha_fin: date, codigo_estacion: Optional[str], codigo_provincia: Optional[str]) -> dict:
        """
        Obtiene y parsea los datos meteorológicos del SiAR para el rango de fechas
        
        :return: Diccionario {date: {variable_siar: valor}}
        """
        try:
            datos_meteo_raw = cliente.get_historic_data(
                province_code = codigo_provincia,
                estacion_code = codigo_estacion,
                tipo          = "DIA",
                start_date    = fecha_inicio,
                end_date      = fecha_fin
            )
            
            return cls._parsear_datos_siar(datos_meteo_raw)
        
        except Exception as e:
            current_app.logger.warning(f"No se pudieron obtener datos SiAR: {e}")
            return {}

    @staticmethod
    def _parsear_datos_siar(datos_siar: dict) -> dict:
        """
        Convierte los datos del SiAR al formato {fecha: {variable: valor}}
        
        :param datos_siar: Respuesta del servicio SiAR
        :return: Diccionario con fechas como keys
        """
        if not datos_siar or 'datos' not in datos_siar:
            return {}
        
        datos_por_fecha = {}
        for registro in datos_siar['datos']:
            fecha_str = registro.get('fecha')
            if not fecha_str:
                continue
                
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            
            # Mapear directamente las variables SiAR
            datos_por_fecha[fecha] = {
                'tempMedia': registro.get('tempMedia'),
                'tempMax': registro.get('tempMax'),
                'tempMin': registro.get('tempMin'),
                'humedadMedia': registro.get('humedadMedia'),
                'precipitacion': registro.get('precipitacion'),
                'velViento': registro.get('velViento'),
                'radiacion': registro.get('radiacion'),
                'etpMon': registro.get('etpMon')
            }
        
        return datos_por_fecha

    @classmethod
    def _construir_datos_por_dia(cls, datos_dtagro: list, datos_siar: dict, 
                                fecha_inicio: date, fecha_fin: date) -> dict:
        """
        Construye diccionario de datos por día fusionando sensores y SiAR
        
        Prioridad: Datos de sensores > Datos SiAR
        """
        delta_dias = (fecha_fin - fecha_inicio).days
        datos_por_dia = {}
        
        for i in range(delta_dias + 1):
            dia = fecha_inicio + timedelta(days=i)
            
            # Obtener datos de sensores para este día
            datos_sensor_dia = PredictorPlagasService._transformar_datos_sensores(datos_dtagro)
            
            # Obtener datos SiAR para este día (si existen)
            datos_siar_dia = datos_siar.get(dia, {})
            
            # Mapear variables SiAR a nombres esperados por las condiciones
            datos_siar_mapeados = {}
            for var_siar, valor in datos_siar_dia.items():
                # Buscar a qué variable de condición corresponde
                for var_condicion, var_siar_key in EvaluarPlaga.MAP_SIAR_CONDICIONES.items():
                    if var_siar_key == var_siar:
                        datos_siar_mapeados[var_condicion] = valor
                        break
            
            # Fusionar: los sensores tienen prioridad (sobreescriben)
            datos_completos = {**datos_siar_mapeados, **datos_sensor_dia}
            datos_por_dia[dia] = datos_completos
            
            # Log para debugging
            if datos_sensor_dia:
                current_app.logger.debug(f"Día {dia}: {len(datos_sensor_dia)} variables de sensores")
            elif datos_siar_mapeados:
                current_app.logger.debug(f"Día {dia}: usando datos SiAR")
            else:
                current_app.logger.debug(f"Día {dia}: sin datos disponibles")
        
        return datos_por_dia
    
    @classmethod
    def _obtener_parcelas_asociadas_cultivo(
        cls,
        cultivo : str,
        parcela_id : Optional[str] = None
    ):
        """
        Consulta sobre el servicio de datos para obtener las parcelas 
        asociadas al cultivo indicado o la parcela exacta 
        asociada al cultivo
        
        :param cultivo : Nombre del cultivo [str]
        :param parcela_id : Identificador público de la parcla [Optional[str]]
        """
        cliente = cls._get_cliente()

        return cliente.get_parcelas_con_cultivos(cultivo, parcela_id)        
    
    @classmethod
    def _obtener_plagas_asociadas_cultivo(
        cls, 
        cultivo: str,
        id_plaga : Optional[str] = None
    ):
        """
        Consulta sobre el servicio de datos las plagas que afectan 
        al cultivo indicado por parámetros
        """
        cliente = cls._get_cliente()

        return cliente.get_plagas_por_cultivo(cultivo, id_plaga)