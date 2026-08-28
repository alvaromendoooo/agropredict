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

    @staticmethod
    def _evaluacion_por_consecucion(
        ventana : dict,
        datos_hoy,
        meteo_dia,
        condiciones_evaluables,
        condiciones,
        resultado_simple,
        datos_por_dia,
        fecha_evaluacion,
        nivel_objetivo,
        plaga
    ):
        simple_hoy_cumple = EvaluarPlaga._todas_condiciones_cumplidas(
            condiciones = condiciones_evaluables,
            datos_dia   = datos_hoy,
            meteo_dia   = meteo_dia or {}
        )

        # Siempre evaluamos el consecutivo para dar contexto
        resultado_consecutivo = EvaluarPlaga._evaluar_consecutivo(
            condiciones      = condiciones,
            datos_por_dia    = datos_por_dia,
            fecha_evaluacion = fecha_evaluacion,
            dias_requeridos  = ventana["dias_consecutivos_requeridos"],
            nivel_objetivo   = nivel_objetivo,
            plaga            = plaga,
            meteo            = meteo_dia
        )

        # Extraer días de forma segura
        dias = resultado_consecutivo.mensaje.get("dias_consecutivos", 0) \
            if isinstance(resultado_consecutivo.mensaje, dict) else 0
        consecutivo_cumple = dias >= ventana["dias_consecutivos_requeridos"]

        # Tabla de niveles:
        # simple SÍ + consecutivo SÍ → CRITICA
        # simple SÍ + consecutivo NO → PREVENTIVA
        # simple NO + consecutivo SÍ → SIN_RIESGO  (día actual rompe racha)
        # simple NO + consecutivo NO → SIN_RIESGO
        if simple_hoy_cumple and consecutivo_cumple:
            nivel_ventana = nivel_objetivo
        elif simple_hoy_cumple and not consecutivo_cumple:
            nivel_ventana = TipoAlerta.PREVENTIVA
        else:
            nivel_ventana = TipoAlerta.SIN_RIESGO

        # Obtengo información de condiciones evaluables dentro de la ventana temporal para 
        # aplicar contexto al cálculo
        condiciones_override_info = []
        for c in condiciones:
            tipo = c["tipo"]
            valor_real = datos_hoy.get(tipo) or (
                meteo_dia or {}).get(EvaluarPlaga.MAP_SIAR_CONDICIONES.get(tipo, ""), None)
            condiciones_override_info.append({
                "variable": tipo,
                "operador": c.get("operador", "=="),
                "umbral": c["valor"],
                "valor_real": round(valor_real, 2) if valor_real is not None else None,
                "estado": "cumplida" if consecutivo_cumple else "pendiente"
            })

        return AlertaPlagaDTO(
            mensaje=resultado_simple.mensaje if simple_hoy_cumple else resultado_consecutivo.mensaje,
            nivel=nivel_ventana,
            nombre_plaga=plaga['nombre'],
            condiciones_cumplidas=(
                resultado_simple.condiciones_cumplidas + condiciones_override_info + [
                    {"dias_consecutivos": dias, "dias_requeridos": ventana["dias_consecutivos_requeridos"]}
                ]
            ) if (simple_hoy_cumple and consecutivo_cumple) else (
                resultado_simple.condiciones_cumplidas if simple_hoy_cumple else []
            ),
            condiciones_pendientes=(
                [] if (simple_hoy_cumple and consecutivo_cumple) else
                resultado_simple.condiciones_pendientes + condiciones_override_info + [
                    {"dias_consecutivos": dias, "dias_requeridos": ventana["dias_consecutivos_requeridos"]}
                ]
            ),
            tipo_organismo=plaga['tipo'],
            agente_causante=plaga['agente_causante'],
            url_referencia=plaga.get('mas_info', ''),
            recomendacion=""
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
        mejor_nivel     = TipoAlerta.SIN_RIESGO
        mejor_resultado = None

        resultados_ventanas = []
        for ventana in ventanas:
            modo = ventana.get("modo")
            nivel_objetivo = TipoAlerta[ventana.get("nivel_si_cumple", "PREVENTIVA")]
            condiciones = ventana.get("condiciones_evaluables_override") or condiciones_evaluables

            if modo == "consecutivo":
                
                resultado_ventana = EvaluarPlaga._evaluacion_por_consecucion(
                    ventana = ventana,
                    datos_hoy = datos_hoy,
                    meteo_dia = meteo_dia,
                    condiciones_evaluables = condiciones_evaluables,
                    condiciones = condiciones,
                    resultado_simple = resultado_simple,
                    datos_por_dia = datos_por_dia,
                    fecha_evaluacion = fecha_evaluacion,
                    nivel_objetivo = nivel_objetivo,
                    plaga = plaga
                )
                resultados_ventanas.append(resultado_ventana)

            elif modo == "acumulacion_gdd":
                resultado_gdd = EvaluarPlaga._evaluar_gdd(
                    datos_por_dia=datos_por_dia,
                    fecha_evaluacion=fecha_evaluacion,
                    ventana=ventana,
                    nivel_objetivo=nivel_objetivo,
                    plaga=plaga,
                    meteo_periodico=meteo_periodica
                )

                if resultado_gdd.nivel == nivel_objetivo and condiciones_evaluables:
                    todas_secundarias_ok = EvaluarPlaga._todas_condiciones_cumplidas(
                        condiciones=condiciones_evaluables,
                        datos_dia=datos_hoy,
                        meteo_dia=meteo_dia or {}
                    )
                    if todas_secundarias_ok:
                        resultado_ventana = resultado_gdd  # CRITICA: GDD + condiciones OK
                    else:
                        resultado_ventana = AlertaPlagaDTO(
                            mensaje=resultado_gdd.mensaje,
                            nivel=TipoAlerta.PREVENTIVA,
                            nombre_plaga=plaga['nombre'],
                            condiciones_cumplidas=resultado_gdd.condiciones_cumplidas,
                            condiciones_pendientes=resultado_gdd.condiciones_pendientes + [
                                {"variable": "temperatura_suelo", "estado": "pendiente_verificacion"}
                            ],
                            tipo_organismo=plaga['tipo'],
                            agente_causante=plaga['agente_causante'],
                            url_referencia=plaga.get('mas_info', ''),
                            recomendacion=""
                        )
                else:
                    # GDD aún no cumplido: añadir condiciones simples del día como contexto
                    resultado_ventana = AlertaPlagaDTO(
                        mensaje=resultado_gdd.mensaje,
                        nivel=resultado_gdd.nivel,
                        nombre_plaga=plaga['nombre'],
                        condiciones_cumplidas=resultado_gdd.condiciones_cumplidas + resultado_simple.condiciones_cumplidas,
                        condiciones_pendientes=resultado_gdd.condiciones_pendientes + resultado_simple.condiciones_pendientes,
                        tipo_organismo=plaga['tipo'],
                        agente_causante=plaga['agente_causante'],
                        url_referencia=plaga.get('mas_info', ''),
                        recomendacion=""
                    )   

                resultados_ventanas.append(resultado_ventana)

            if mejor_resultado is None or \
            EvaluarPlaga.NIVEL_PRIORIDAD.get(resultado_ventana.nivel.value, 0) > \
            EvaluarPlaga.NIVEL_PRIORIDAD.get(mejor_nivel.value, 0):
                mejor_nivel     = resultado_ventana.nivel
                mejor_resultado = resultado_ventana

        if not resultados_ventanas:
            return resultado_simple

        # Tomar el mejor nivel entre todas las ventanas
        mejor_resultado = max(
            resultados_ventanas,
            key=lambda r: EvaluarPlaga.NIVEL_PRIORIDAD.get(r.nivel.value, 0)
        )

        # Fusionar condiciones cumplidas y pendientes de TODAS las ventanas como contexto
        todas_cumplidas  = []
        todas_pendientes = []
        for r in resultados_ventanas:
            for c in r.condiciones_cumplidas:
                if c not in todas_cumplidas:
                    todas_cumplidas.append(c)
            for p in r.condiciones_pendientes:
                # Evitar que entren en pendientes items que ya están en cumplidas
                if p not in todas_pendientes and p not in todas_cumplidas:
                    todas_pendientes.append(p)

        return AlertaPlagaDTO(
            mensaje=mejor_resultado.mensaje,
            nivel=mejor_resultado.nivel,
            nombre_plaga=plaga['nombre'],
            condiciones_cumplidas=todas_cumplidas,
            condiciones_pendientes=todas_pendientes,
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
        
        # Contar días consecutivos hacia atrás
        for i in range(dias_requeridos):
            dia = fecha_evaluacion - timedelta(days=i)
            datos_dia = datos_por_dia.get(dia, {})
            # Si el día actual NO cumple, romper el bucle
            if not EvaluarPlaga._todas_condiciones_cumplidas(condiciones, datos_dia, meteo):
                continue
            dias_consecutivos += 1

        
        # Determinar nivel basado SOLO en días consecutivos
        if dias_consecutivos >= dias_requeridos:
            nivel = nivel_objetivo  # CRITICA
            condiciones_pendientes = []
            condiciones_cumplidas = [{"dias_consecutivos": dias_consecutivos}]
        elif dias_consecutivos > 0:
            nivel = TipoAlerta.PREVENTIVA
            condiciones_pendientes = [{
                "dias_consecutivos": dias_consecutivos, 
                "dias_requeridos": dias_requeridos
            }]
            condiciones_cumplidas = []
        else:
            nivel = TipoAlerta.SIN_RIESGO
            condiciones_pendientes = []
            condiciones_cumplidas = []
        
        return AlertaPlagaDTO(
            mensaje={"dias_consecutivos": dias_consecutivos, "dias_requeridos": dias_requeridos},
            nivel=nivel,
            nombre_plaga=plaga['nombre'],
            condiciones_cumplidas=condiciones_cumplidas,
            condiciones_pendientes=condiciones_pendientes,
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
            dia = fecha_evaluacion - timedelta(days=i) # Dia actual evaluable del periodo
            
            datos_dia      = datos_por_dia.get(dia, {}) if datos_por_dia else {} # Obtengo datos de sensor
            datos_dia_siar = datos_ventana.get(dia, {})  if usar_meteo_periodico else {} # Obtengo datos de SiAR

            # Prioridad: sensor → SiAR → None
            #print(f"DEBUG: datos dia sensores: {datos_dia} - dia: {dia}")
            #print(f"DEBUG: Datos dia siar: {datos_dia_siar}")
            t_max = datos_dia.get("temperatura_max") or datos_dia_siar.get("tempMax")
            t_min = datos_dia.get("temperatura_min") or datos_dia_siar.get("tempMin")
            #print(f"DEBUG: t_max: {t_max}")
            #print(f"DEBUG: t_min: {t_min}")
            if t_max is not None and t_min is not None:
                gdd_dia        = max(0.0, (t_max + t_min) / 2 - temperatura_base)
                gdd_acumulado += gdd_dia
                #print(f"DEBUG: gdd_dia: {gdd_dia} - dia: {dia} - t_max: {t_max} - t_min: {t_min} - gdd_acumulado: {gdd_acumulado}")

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