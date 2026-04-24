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
    


    @classmethod
    def _filtrar_y_agregar_datos_por_dia(cls, datos_dtagro: list, dia_actual: date) -> dict:
        """
        Filtra los datos de los sensores para un día específico y devuelve 
        un diccionario con los valores agregados (medias, sumas, etc.) listos 
        para ser evaluados por las condiciones de la plaga.
        """
        lecturas_del_dia = []

        # 1. Filtrar todas las lecturas correspondientes a 'dia_actual'
        for sensor_global in datos_dtagro:
            for lectura in sensor_global['resultados']:
                # Comprobamos si el timestamp viene como string o como objeto datetime
                if isinstance(lectura['timestamp'], str):
                    fecha_lectura = datetime.fromisoformat(lectura['timestamp'].replace('Z', '+00:00')).date()
                elif isinstance(lectura['timestamp'], datetime):
                    fecha_lectura = lectura['timestamp'].date()
                else:
                    fecha_lectura = lectura['timestamp']

                if fecha_lectura == dia_actual:
                    lecturas_del_dia.append(lectura)

        # Si no hay lecturas de sensores para ese día, devolvemos un diccionario vacío
        if not lecturas_del_dia:
            return {}

        def media(valores):
            filtrados = [v for v in valores if v is not None and v != 0.0]
            return sum(filtrados) / len(filtrados) if filtrados else None
        
        def maximo(valores):
            filtrados = [v for v in valores if v is not None and v != 0.0]
            return max(filtrados) if filtrados else None
        
        def minimo(valores):
            filtrados = [v for v in valores if v is not None and v != 0.0]
            return min(filtrados) if filtrados else None

        return {
            "temperatura_aire" : media([l['temperatura_maxima'] for l in lecturas_del_dia]),
            "temperatura_media" : media([l['temperatura_maxima'] for l in lecturas_del_dia]),
            "temperatura_max" : maximo([l['temperatura_maxima'] for l in lecturas_del_dia]),
            "temperatura_min" : minimo([l['temperatura_minima'] for l in lecturas_del_dia]),
            "temperatura_suelo" : media([l['temperatura_suelo'] for l in lecturas_del_dia]),
            "humedad_relativa" : media([l['humedad_foliar'] for l in lecturas_del_dia]),
            "humedad_suelo" : media([l['humedad_suelo'] for l in lecturas_del_dia]),
            "humedad_hoja" : media([l['temperatura_hojas'] for l in lecturas_del_dia]),
        }

    @classmethod
    def obtener_prediccion_plagas_estimadas(cls, cultivo: str, datos_sensores, fecha_inicio, fecha_fin):
        """
        Calcula predicción de plagas para un cultivo en un rango de fechas
        
        :param cultivo: Nombre del cultivo
        :param datos_sensores: Lista de EUIs de sensores
        :param fecha_inicio: Fecha de inicio (date object)
        :param fecha_fin: Fecha de fin (date object)
        """
        try:
            cliente = cls._get_cliente()

            # 1. Obtener datos de sensores para todo el rango
            datos_dtagro = cliente.get_datos_sensores(
                euis = datos_sensores,
                fecha_inicio = fecha_inicio,
                fecha_fin = fecha_fin
            )

            # 2. Obtener datos meteorológicos SiAR (si están disponibles)
            datos_siar_por_fecha = cls._obtener_datos_siar(
                cliente = cliente,
                fecha_inicio = fecha_inicio,
                fecha_fin = fecha_fin
            )

            # 3. Construir diccionario de datos por día (priorizando sensores)
            datos_por_dia = cls._construir_datos_por_dia(
                datos_dtagro = datos_dtagro,
                datos_siar = datos_siar_por_fecha,
                fecha_inicio = fecha_inicio,
                fecha_fin = fecha_fin
            )

            # 4. Obtener plagas del cultivo
            plagas_cultivos = cliente.get_plagas_por_cultivo(cultivo.capitalize())

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
                                datos = datos_por_dia.get(dia_actual, {}),
                                plaga = plaga_config,
                                fecha = dia_actual
                            )
                        else:
                            # Pasar los datos meteorológicos del día específico
                            datos_meteo_dia = datos_siar_por_fecha.get(dia_actual, {})

                            alerta_dia = EvaluarPlaga.evaluar_plaga_generica(
                                condiciones_evaluables = plaga_config.get('condiciones_evaluables'),
                                datos_por_dia = datos_por_dia,
                                fecha_evaluacion = dia_actual,
                                plaga = plaga_config,
                                meteo = datos_meteo_dia  # Solo datos del día actual
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
    def _obtener_datos_siar(cls, cliente, fecha_inicio: date, fecha_fin: date) -> dict:
        """
        Obtiene y parsea los datos meteorológicos del SiAR para el rango de fechas
        
        :return: Diccionario {date: {variable_siar: valor}}
        """
        try:
            datos_meteo_raw = cliente.get_historic_data(
                province_code="CC",
                estacion_code=None,
                type="DIA",
                start_date=fecha_inicio,
                end_date=fecha_fin
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
            datos_sensor_dia = cls._filtrar_y_agregar_datos_por_dia(datos_dtagro, dia)
            
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