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
        datos_por_dia: dict,        # {date: {variable: valor}}
        fecha_evaluacion: date,
        plaga: dict,
        meteo: dict = None
    ) -> AlertaPlagaDTO:

        ventanas = plaga.get("ventana_temporal") or []
        datos_hoy = datos_por_dia.get(fecha_evaluacion, {})

        # 1. Evaluación simple del día (siempre se ejecuta)
        resultado_simple = EvaluarPlaga._evaluar_dia_simple(
            condiciones_evaluables = condiciones_evaluables,
            datos_del_dia = datos_hoy,
            plaga = plaga,
            meteo_dia = meteo or {}
        )

        if not ventanas:
            return resultado_simple

        # 2. Si hay ventanas temporales, evaluamos cada una
        mejor_nivel = resultado_simple.nivel
        mejor_resultado = resultado_simple

        resultados_ventantas = []
        for ventana in ventanas:
            modo = ventana.get("modo")
            nivel_objetivo = TipoAlerta[ventana.get("nivel_si_cumple", "PREVENTIVA")]
            # Uso condiciones_override si existen, si no las generales
            condiciones = ventana.get("condiciones_evaluables_override") or condiciones_evaluables

            if modo == "consecutivo":
                resultado_ventana = EvaluarPlaga._evaluar_consecutivo(
                    condiciones=condiciones,
                    datos_por_dia=datos_por_dia,
                    fecha_evaluacion=fecha_evaluacion,
                    dias_requeridos=ventana["dias_consecutivos_requeridos"],
                    nivel_objetivo=nivel_objetivo,
                    plaga=plaga,
                    meteo = meteo
                )
            elif modo == "acumulacion_gdd":
                resultado_ventana = EvaluarPlaga._evaluar_gdd(
                    datos_por_dia=datos_por_dia,
                    fecha_evaluacion=fecha_evaluacion,
                    ventana=ventana,
                    nivel_objetivo=nivel_objetivo,
                    plaga=plaga
                )
            else:
                continue

            resultados_ventantas.append(resultado_ventana)

            # Nos quedamos con el nivel más alto encontrado
            if EvaluarPlaga.NIVEL_PRIORIDAD.get(resultado_ventana.nivel.value, 0) > \
               EvaluarPlaga.NIVEL_PRIORIDAD.get(mejor_nivel.value, 0):
                mejor_nivel = resultado_ventana.nivel
                mejor_resultado = resultado_ventana

        # Muestra información del cumplimiento parcial de las condiciones sobre las ventanas evaluadas
        info_ventanas_parciales = [
            r.mensaje for r in resultados_ventantas
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
            valor_real = datos_del_dia.get(tipo_variable)
            
            # Intentar obtener del meteo si no hay datos de sensores
            valor_meteo = None
            if tipo_variable in EvaluarPlaga.MAP_SIAR_CONDICIONES:
                var_siar = EvaluarPlaga.MAP_SIAR_CONDICIONES[tipo_variable]
                valor_meteo = meteo_dia.get(var_siar)
            
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
                "valor_real" : valor_usado,
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
            else:
                break

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
        ventana, nivel_objetivo, plaga
    ) -> AlertaPlagaDTO:
        temperatura_base = ventana["temperatura_base"]
        gdd_objetivo = ventana["gdd_objetivo"]
        dias_ventana = ventana["dias_ventana"]

        # Soporte para fecha_inicio_acumulacion fija (ej: Rhagoletis desde 01-marzo)
        fecha_inicio_str = ventana.get("fecha_inicio_acumulacion")
        if fecha_inicio_str:
            mes, dia = map(int, fecha_inicio_str.split("-"))
            fecha_inicio_acum = date(fecha_evaluacion.year, mes, dia)
            dias_a_evaluar = (fecha_evaluacion - fecha_inicio_acum).days + 1
        else:
            dias_a_evaluar = dias_ventana

        gdd_acumulado = 0.0

        for i in range(dias_a_evaluar):
            dia = fecha_evaluacion - timedelta(days=i)
            datos_dia = datos_por_dia.get(dia, {})

            t_max = datos_dia.get("temperatura_max")
            t_min = datos_dia.get("temperatura_min")

            if t_max is not None and t_min is not None:
                gdd_dia = max(0.0, (t_max + t_min) / 2 - temperatura_base)
                gdd_acumulado += gdd_dia

        cumple = gdd_acumulado >= gdd_objetivo
        nivel = nivel_objetivo if cumple else (
            TipoAlerta.PREVENTIVA if gdd_acumulado >= gdd_objetivo * 0.7 else TipoAlerta.SIN_RIESGO
        )

        return AlertaPlagaDTO(
            mensaje={"gdd_acumulado" : gdd_acumulado, "gdd_objetivo" : gdd_objetivo},
            nivel=nivel,
            nombre_plaga=plaga['nombre'],
            condiciones_cumplidas=[{"gdd_acumulado" : gdd_acumulado}] if cumple else [],
            condiciones_pendientes=[] if cumple else [{"gdd_acumulado" : gdd_acumulado, "gdd_objetivo" : gdd_objetivo}],
            tipo_organismo=plaga['tipo'],
            agente_causante = plaga['agente_causante'],
            url_referencia = plaga['mas_info'],
            recomendacion = ""
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