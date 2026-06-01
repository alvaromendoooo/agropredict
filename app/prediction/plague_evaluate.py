from .prediction_dto import AlertaPlagaDTO, TipoAlerta
from datetime import datetime, timedelta, date
import operator

class EvaluarPlaga:

    OPERADORES = {
        ">=": operator.ge,
        "<=": operator.le,
        ">": operator.gt,
        "<": operator.lt,
        "==": operator.eq,
        "=": operator.eq
    }

    MAP_SIAR_CONDICIONES = {
        "temperatura_aire" : "tempMedia",
        "temperatura_media" : "tempMedia",
        "temperatura_max" : "tempMax",
        "temperatura_min" : "tempMin",
        "humedad_relativa" : "humedadMedia",
        "precipitacion" : "precipitacion",
        "velocidad_viento" : "velViento",
        "radiacion_solar" : "radiacion",
        "evapotranspiracion" : "etpMon"
    }

    NIVEL_PRIORIDAD = {
        "SIN_RIESGO": 0,
        "PREVENTIVA": 1,
        "CRITICA": 2
    }

    # ── Evaluacion externa ──────────────────────────────────────────────────────
    @staticmethod
    def evaluar_algoritmo_externo(
        url : str,
        datos,
        plaga,
        fecha
    ):
        import requests
        response = requests.post(url, json = {
            "plaga_id" : plaga['public_id'],
            "fecha" : fecha.strftime("%Y-%m-%d"),
            "datos" : datos
        })

        resultado = response.json()

        return AlertaPlagaDTO(
            mensaje = resultado.get('mensaje'),
            nivel = TipoAlerta[resultado["nivel_riesgo"]],
            nombre_plaga = plaga["nombre"],
            condiciones_cumplidas = resultado.get("condiciones_cumplidas", []),
            condiciones_pendientes = resultado.get("condiciones_pendientes", []),
            tipo_organismo = plaga["tipo"],
            agente_causante = plaga["agente_causante"],
            url_referencia = plaga.get("mas_info", ""),
            recomendacion = resultado.get("recomendacion", "")
        )

    # ── Método principal ──────────────────────────────────────────────────────

    @staticmethod
    def evaluar_plaga_generica(
        condiciones_evaluables: list,
        datos_por_dia: dict,
        fecha_evaluacion: date,
        plaga: dict,
        meteo_dia: dict = None,
        meteo_periodica: dict = None
    ) -> AlertaPlagaDTO:

        ventanas = plaga.get("ventana_temporal") or []
        datos_hoy = datos_por_dia.get(fecha_evaluacion, {})

        # Comprobamos si hay alguna ventana GDD para aplicar lógica compuesta
        tiene_ventana_gdd = any(v.get("modo") == "acumulacion_gdd" for v in ventanas)

        # 1. Evaluación simple del día (siempre se ejecuta)
        resultado_simple = EvaluarPlaga._evaluar_dia_simple(
            condiciones_evaluables = condiciones_evaluables,
            datos_del_dia          = datos_hoy,
            plaga                  = plaga,
            meteo_dia              = meteo_dia or {}
        )

        if not ventanas:
            return resultado_simple

        # 2. Evaluar ventanas temporales
        mejor_nivel     = resultado_simple.nivel
        mejor_resultado = resultado_simple

        # Si hay GDD + condiciones simples, no mezclo niveles directamente
        # La evaluación simple solo puntúa de forma independiente cuando NO hay ventana GDD
        if tiene_ventana_gdd:
            mejor_nivel     = TipoAlerta.SIN_RIESGO
            mejor_resultado = resultado_simple  # lo usamos como base informativa

        resultados_ventanas = []
        for ventana in ventanas:
            modo = ventana.get("modo")
            nivel_objetivo = TipoAlerta[ventana.get("nivel_si_cumple", "PREVENTIVA")]
            condiciones = ventana.get("condiciones_evaluables_override") or condiciones_evaluables

            if modo == "consecutivo":
                resultado_ventana = EvaluarPlaga._evaluar_consecutivo(
                    condiciones      = condiciones,
                    datos_por_dia    = datos_por_dia,
                    fecha_evaluacion = fecha_evaluacion,
                    dias_requeridos  = ventana["dias_consecutivos_requeridos"],
                    nivel_objetivo   = nivel_objetivo,
                    plaga            = plaga,
                    meteo            = meteo_dia
                )
            elif modo == "acumulacion_gdd":
                resultado_gdd = EvaluarPlaga._evaluar_gdd(
                    datos_por_dia    = datos_por_dia,
                    fecha_evaluacion = fecha_evaluacion,
                    ventana          = ventana,
                    nivel_objetivo   = nivel_objetivo,
                    plaga            = plaga,
                    meteo_periodico  = meteo_periodica
                )

                # GDD es requisito, condición simple es verificación ──
                # Si el GDD llega a nivel objetivo Y hay condiciones simples que verificar,
                # el nivel final sube a CRITICA solo si ambas se cumplen.
                if resultado_gdd.nivel == nivel_objetivo and condiciones_evaluables:
                    todas_secundarias_ok = EvaluarPlaga._todas_condiciones_cumplidas(
                        condiciones = condiciones_evaluables,
                        datos_dia   = datos_hoy,
                        meteo_dia   = meteo_dia or {}
                    )
                    if todas_secundarias_ok:
                        resultado_ventana = resultado_gdd  # CRITICA: GDD + temp suelo OK
                    else:
                        # GDD cumplido pero temperatura suelo no: bajamos a PREVENTIVA
                        resultado_ventana = AlertaPlagaDTO(
                            mensaje                = resultado_gdd.mensaje,
                            nivel                  = TipoAlerta.PREVENTIVA,
                            nombre_plaga           = plaga['nombre'],
                            condiciones_cumplidas  = resultado_gdd.condiciones_cumplidas,
                            condiciones_pendientes = resultado_gdd.condiciones_pendientes + [
                                {"variable": "temperatura_suelo", "estado": "pendiente_verificacion"}
                            ],
                            tipo_organismo         = plaga['tipo'],
                            agente_causante        = plaga['agente_causante'],
                            url_referencia         = plaga.get('mas_info', ''),
                            recomendacion          = ""
                        )
                else:
                    resultado_ventana = resultado_gdd
            else:
                continue

            resultados_ventanas.append(resultado_ventana)

            if EvaluarPlaga.NIVEL_PRIORIDAD.get(resultado_ventana.nivel.value, 0) > \
            EvaluarPlaga.NIVEL_PRIORIDAD.get(mejor_nivel.value, 0):
                mejor_nivel = resultado_ventana.nivel
                mejor_resultado = resultado_ventana

        info_ventanas_parciales = [
            r.mensaje for r in resultados_ventanas
            if r != mejor_resultado and r.nivel != TipoAlerta.CRITICA
        ]
        for info in info_ventanas_parciales:
            mejor_resultado.condiciones_pendientes.append(info)

        return AlertaPlagaDTO(
            mensaje=mejor_resultado.mensaje,
            nivel=mejor_nivel,
            nombre_plaga=plaga['nombre'],
            condiciones_cumplidas=mejor_resultado.condiciones_cumplidas,
            condiciones_pendientes=mejor_resultado.condiciones_pendientes,
            tipo_organismo=plaga['tipo'],
            agente_causante=plaga['agente_causante'],
            url_referencia=plaga.get('mas_info', ''),
            recomendacion=""
        )

    # ── Evaluación simple (Patrón 1) ──────────────────────────────────────────

    @staticmethod
    def _evaluar_dia_simple(condiciones_evaluables, datos_del_dia, plaga, meteo_dia=None) -> AlertaPlagaDTO:
        """
        Evalúa condiciones para un día específico
        
        :param meteo_dia: Diccionario con datos meteorológicos del día (variables SiAR originales)
        """
        cumplidas = []
        pendientes = []
        meteo_dia = meteo_dia or {}

        for condicion in condiciones_evaluables:
            tipo_variable = condicion["tipo"]
            valor_umbral = condicion["valor"]
            operador_str = condicion.get("operador", "==")
            operador_func = EvaluarPlaga.OPERADORES.get(operador_str)
            
            # Obtener valor de sensores
            valor_real : float = datos_del_dia.get(tipo_variable)
            
            # Intentar obtener del meteo si no hay datos de sensores
            valor_meteo = None
            if tipo_variable in EvaluarPlaga.MAP_SIAR_CONDICIONES:
                var_siar = EvaluarPlaga.MAP_SIAR_CONDICIONES[tipo_variable]
                valor_meteo : float = meteo_dia.get(var_siar)
            
            # Decidir qué valor usar
            valor_usado = None
            fuente = None
            
            if valor_real is not None:
                valor_usado = valor_real
                fuente = "sensor"

            elif valor_meteo is not None:
                valor_usado = valor_meteo
                fuente = "meteorológico"
            
            # Estructura generica de cumplimiento de condiciones
            generico_cumplimiento = {
                "variable" : tipo_variable,
                "valor_real" : round(valor_usado or 0, 2),
                "operador" : operador_str,
                "umbral" : valor_umbral,
                "fuente" : fuente
            }
            
            if valor_usado is not None:
                if operador_func(valor_usado, valor_umbral):
                    cumplidas.append(generico_cumplimiento)
                else:
                    pendientes.append(generico_cumplimiento)
            else:
                pendientes.append(f"Sin datos para {tipo_variable}")

        nivel = EvaluarPlaga._definir_nivel_riesgo(len(cumplidas), len(condiciones_evaluables))

        return AlertaPlagaDTO(
            mensaje = f"Evaluación {plaga['nombre']}: {len(cumplidas)}/{len(condiciones_evaluables)} condiciones",
            nivel = nivel,
            nombre_plaga = plaga['nombre'],
            condiciones_cumplidas = cumplidas,
            condiciones_pendientes = pendientes,
            url_referencia = plaga.get('mas_info', ''),
            tipo_organismo = plaga['tipo'],
            agente_causante = plaga['agente_causante'],
            recomendacion=""
        )

    # ── Evaluación consecutiva (Patrón 2) ────────────────────────────────────

    @staticmethod
    def _evaluar_consecutivo(
        condiciones, datos_por_dia, fecha_evaluacion,
        dias_requeridos, nivel_objetivo, plaga, meteo
    ) -> AlertaPlagaDTO:
        
        dias_consecutivos = 0

        for i in range(dias_requeridos):
            dia = fecha_evaluacion - timedelta(days=i)
            datos_dia = datos_por_dia.get(dia, {})
            meteo_dia = meteo.get(dia, {}) if isinstance(meteo, dict) else {}

            if EvaluarPlaga._todas_condiciones_cumplidas(condiciones, datos_dia, meteo_dia):
                dias_consecutivos += 1
            # Elimino el break si hay un día que no lo cumple, así veo el registro completo de números de 
            # días que lo ha cumplido

        cumple = dias_consecutivos >= dias_requeridos
        nivel = nivel_objetivo if cumple else (
            TipoAlerta.PREVENTIVA if dias_consecutivos > 0 else TipoAlerta.SIN_RIESGO
        )

        return AlertaPlagaDTO(
            mensaje={"dias_consecutivos" : dias_consecutivos, "dias_requeridos" : dias_requeridos},
            nivel=nivel,
            nombre_plaga=plaga['nombre'],
            condiciones_cumplidas=[{"dias_consecutivos" : dias_consecutivos}] if dias_consecutivos > 0 else [],
            condiciones_pendientes=[] if cumple else [{"dias_consecutivos" : dias_consecutivos, "dias_requeridos" : dias_requeridos}],
            tipo_organismo=plaga['tipo'],
            agente_causante=plaga['agente_causante'],
            url_referencia=plaga.get('mas_info', ''),
            recomendacion=""
        )
    
    # ── Evaluación GDD (Patrón 3) ─────────────────────────────────────────────

    @staticmethod
    def _evaluar_gdd(
        datos_por_dia, fecha_evaluacion,
        ventana, nivel_objetivo, plaga,
        meteo_periodico
    ) -> AlertaPlagaDTO:
        temperatura_base = ventana["temperatura_base"]
        gdd_objetivo = ventana["gdd_objetivo"]
        dias_ventana = ventana["dias_ventana"]

        fecha_inicio_str = ventana.get("fecha_inicio_acumulacion")
        if fecha_inicio_str:
            mes, dia = map(int, fecha_inicio_str.split("-"))
            fecha_inicio_acum = date(fecha_evaluacion.year, mes, dia)
            dias_a_evaluar = (fecha_evaluacion - fecha_inicio_acum).days + 1
        else:
            dias_a_evaluar = dias_ventana

        gdd_acumulado = 0.0

        # meteo_periodico viene como {fecha_evaluacion: {fecha_dia: {vars_siar}}}
        # Intento usar el bloque de datos precargado para esta fecha de evaluación.
        # Si no existe (plaga sin ventana GDD o primera carga), uso datos_por_dia.
        datos_ventana = (meteo_periodico or {}).get(fecha_evaluacion, {})
        usar_meteo_periodico = bool(datos_ventana)

        for i in range(dias_a_evaluar):
            dia = fecha_evaluacion - timedelta(days=i)
            if datos_por_dia:
                # Uso dato de sensores por ser prioritarios al cálculo
                datos_dia = datos_por_dia.get(dia, {})
                t_max     = datos_dia.get("temperatura_max")
                t_min     = datos_dia.get("temperatura_min")
            elif usar_meteo_periodico:
                # Fallback: datos de sensores periódico por ventana temporal en caso de no obtener datos de sensores
                datos_dia_siar = datos_ventana.get(dia, {})
                t_max          = datos_dia_siar.get("tempMax")
                t_min          = datos_dia_siar.get("tempMin")
            else:
                return None

            if t_max is not None and t_min is not None:
                gdd_dia        = max(0.0, (t_max + t_min) / 2 - temperatura_base)
                gdd_acumulado += gdd_dia

        cumple = gdd_acumulado >= gdd_objetivo
        nivel = nivel_objetivo if cumple else (
            TipoAlerta.PREVENTIVA if gdd_acumulado >= gdd_objetivo * 0.7 else TipoAlerta.SIN_RIESGO
        )

        return AlertaPlagaDTO(
            mensaje={"gdd_acumulado": round(gdd_acumulado, 2), "gdd_objetivo": gdd_objetivo},
            nivel=nivel,
            nombre_plaga=plaga['nombre'],
            condiciones_cumplidas=[{"gdd_acumulado": round(gdd_acumulado, 2)}] if cumple else [],
            condiciones_pendientes=[] if cumple else [{"gdd_acumulado": round(gdd_acumulado, 2), "gdd_objetivo": gdd_objetivo}],
            tipo_organismo=plaga['tipo'],
            agente_causante=plaga['agente_causante'],
            url_referencia=plaga.get('mas_info', ''),
            recomendacion=""
        )

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _todas_condiciones_cumplidas(condiciones, datos_dia, meteo_dia=None) -> bool:
        """
        Verifica si todas las condiciones se cumplen para un día
        
        :param meteo_dia: Diccionario con datos meteorológicos del día (variables SiAR)
        """
        meteo_dia = meteo_dia or {}
        
        for condicion in condiciones:
            operador_func = EvaluarPlaga.OPERADORES.get(condicion.get("operador", "=="))
            valor_umbral = condicion["valor"]
            
            # Priorizar datos de sensores
            valor = datos_dia.get(condicion["tipo"])
            
            # Fallback a datos meteorológicos
            if valor is None and condicion["tipo"] in EvaluarPlaga.MAP_SIAR_CONDICIONES:
                var_siar = EvaluarPlaga.MAP_SIAR_CONDICIONES[condicion["tipo"]]
                valor = meteo_dia.get(var_siar)
            
            if valor is None:
                return False
                
            if not operador_func(valor, valor_umbral):
                return False
                
        return True

    @staticmethod
    def _definir_nivel_riesgo(condiciones_cumplidas, condiciones_totales):
        if condiciones_totales == 0:
            return TipoAlerta.SIN_RIESGO
        if condiciones_cumplidas == condiciones_totales:
            return TipoAlerta.CRITICA
        elif condiciones_cumplidas > 0:
            return TipoAlerta.PREVENTIVA
        else:
            return TipoAlerta.SIN_RIESGO