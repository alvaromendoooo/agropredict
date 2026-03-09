from .prediction_dto import PrediccionMeteorologicaPlagas, AlertaPlagaDTO, DatosSensorDTO, TipoAlerta
from datetime import datetime, timedelta

class EvaluarPlaga:
    """
    Contiene la lógica del umbral para cada plaga.
    Cuando se incorpore una nueva plaga a evaluar, se debe incoporar un nuevo método _evaluar()
    """

    # ---- MÉTODOS GENÉRICOS----#
    @staticmethod
    def _comprobar_requisito_dias_humedad_bajo_rango(
        dias : int,
        lecturas_bajo_rango : list
    ) -> bool:
        """
        Dado los datos pasados por parámetros, indica si se cumple la restricción de días
        sobre esa plaga o no.
        """

        dias_acumulados = 0
        
        dias_registrados = {
            datetime.fromisoformat(lectura.timestamp.replace('Z', '+00:00')).date()
            for lectura in lecturas_bajo_rango
        } # Almacena en el conjunto los días diferentes de las lecturas cuya humedad foliar <= 30.0

        dias_ordenados = sorted(dias_registrados)

        dia_iterado = None
        for dia in dias_ordenados:
            if dia_iterado == None:
                dia_iterado = dia
            elif timedelta(days=1) <= (dia - dia_iterado) <= timedelta(days=2):
                dia_iterado = dia
                dias_acumulados += 1
            else:
                dia_iterado = dia


        if dias_acumulados == dias: # Cumple con la restricción
            return True
        else:
            return False
        
    @staticmethod
    def _definir_nivel_riesgo(
        condiciones_cumplidas : int,
        condiciones_totales : int
    ):
        if condiciones_cumplidas == condiciones_totales:
            return TipoAlerta.CRITICA
        elif condiciones_cumplidas > 0:
            return TipoAlerta.PREVENTIVA
        else:
            return TipoAlerta.SIN_RIESGO
        

    # ----TOMATE---- #
    @staticmethod
    def _evaluar_tomate_001(
        datos_sensores : list[DatosSensorDTO],
        datos_meteorologicos : PrediccionMeteorologicaPlagas
    ) -> AlertaPlagaDTO:
        """
        Nombre :  Aculops lycopersici
        Umbral : Primavera-verano. Alerta activa tras 6-7 dias consecutivos con temperatura maxima en torno a 27C y 
        humedad relativa igual o inferior al 30%. Ciclo completo en ~7 dias bajo condiciones optimas.
        """
        TMAX_UMBRAL = 27.0
        HUM_UMBRAL = 30.0
        DIAS_CONSECUTIVOS = 6
        NOMBRE_PLAGA = "Acaro del bronceado del tomate"

        # Definición de recomendaciones en base a riesgo
        recomendaciones = {
            'critica' : 'Usar mallas (mínimo 10*20 kilos/cm2) durante el cultivo en las aberturas laterales, cenitales y puertas, que coincidan con los vientos dominantes siempre y cuando la temperatura ambiente no sea demasiado elevada. Además, hay que vigilar que no se produzcan roturas en los plásticos.',
            'preventiva' : 'Eliminar las malas hierbas y restos de cultivos, ya que pueden actuar como reservorio de la planta. Eliminar plantas que estén muy afectadas.',
        }

        # Almacena las restricciones cumplidas y pendientes
        cumplidas = []
        pendientes = []

        # TEMPERATURA MÁXIMA
        if datos_meteorologicos.temperatura_maxima >= TMAX_UMBRAL:
            cumplidas.append(
                f"Temperatura máxima {datos_meteorologicos.temperatura_maxima} ºC >= {TMAX_UMBRAL} ºC"
            )
        else:
            pendientes.append(
                f"Temperatura maxima {datos_meteorologicos.temperatura_maxima} ºC < {TMAX_UMBRAL} ºC requerido"
            )

        # HUMEDAD FOLIAR (sensores)
        lecturas_bajo_rango = [s for s in datos_sensores if s.humedad_foliar <= HUM_UMBRAL]

        if len(lecturas_bajo_rango) is not 0:
            cumplidas.append(
                f"Registradas {len(lecturas_bajo_rango)} lecturas cuya humedad foliar <= {HUM_UMBRAL}"
            )
        else:
            pendientes.append(
                f"No se han registrado lecturas cuya humedad foliar <= {HUM_UMBRAL}"
            )
        # HUMEDAD FOLIAR DIA CONSECUTIVO
        if EvaluarPlaga._comprobar_requisito_dias_humedad_bajo_rango(DIAS_CONSECUTIVOS, lecturas_bajo_rango):
            cumplidas.append(
                f"Registrados {DIAS_CONSECUTIVOS} días consecutivos con humedad <= {HUM_UMBRAL}"
            )
        else:
            pendientes.append(
                f"No se han registrado {DIAS_CONSECUTIVOS} días consecutivos con humedad <= {HUM_UMBRAL}"
            )

        nivel_riesgo = EvaluarPlaga._definir_nivel_riesgo(
            condiciones_cumplidas = len(cumplidas),
            condiciones_totales = 3
        )

        return AlertaPlagaDTO(
            mensaje = f"Evaluación de riesgos aplicando umbrales sobre la plaga {NOMBRE_PLAGA}",
            recomendacion = recomendaciones[nivel_riesgo] if nivel_riesgo != TipoAlerta.SIN_RIESGO else None,
            nivel =  nivel_riesgo,
            nombre_plaga = "Acaro del bronceado del tomate",
            agente_causante = "Phytophthora spp. (de Bary, 1876)",
            condiciones_cumplidas = cumplidas,
            condiciones_pendientes = pendientes,
            url_referencia = "https://www.infoagro.com/proteccion_cultivos/phytophthora.htm",
            tipo_organismo = "acaro"
        )
        
