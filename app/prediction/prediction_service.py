from ..clients.data_service_client import DataServiceClient 
from config.config import Config
from .prediction_dto import *
from typing import Optional
from datetime import date
from math import erf, sqrt
from flask import current_app

class HeladaPredictionService():

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
    def prob_helada_posterior(dia, media, desviacion):
        z = (dia - media) / desviacion
        print(f"z : {z}")
        # P (X > z)
        # Probabilidad de que la helada ocurra después del día dado
        return 0.5*(1 - erf(z / sqrt(2)))

    @staticmethod
    def _build_predictions(
        data            
    ) -> RiesgoHeladaDTO:
        """
        Construye los DTOs de predicciones de heladas
        
        :param data: Datos obtenidos de data_service
        :return: DTO cargado
        :rtype: RiesgoHeladaDTO
        """

        predicciones = []
        alertas = []

        for d in data:
            # Obtenemos la temperatura mínima que nos devuelve el cliente
            temp_min = d.get('tempMin')
            # Obtenemos la fecha en la que se produjo esa temp_min
            fec_temp_min = datetime.fromisoformat(d.get('horMinTempMin').get('timestamp')).date()
            # 1. Primer caso de uso, comprobar si han ocurrido precipitaciones o si el suelo se encontraba húmedo
            precipitaciones = d.get('precipitacion')
            humedad_min = d.get('humedadMin')

            if precipitaciones >= 50 or humedad_min >= 50: # Si llueve, evita riesgo de heladas
                nivel = NivelHelada.SIN_RIESGO
            else:
                # 2. Segundo caso de uso, riesgo inmediato por temperaturas minimas
                if temp_min <= 0:
                    nivel = NivelHelada.FUERTE
                    alerta = AlertaDTO(
                        mensaje = f"Se ha percibido temperaturas minimas bajo cero el dia {fec_temp_min}",
                        recomendacion = "Riesgo alto de congelación en brotes de arboles frutales, asegurarlos con cubiertas o mallas protectoras",
                        nivel = TipoAlerta.CRITICA
                    ) 
                    alertas.append(alerta)
                elif temp_min <= 2:
                    nivel = NivelHelada.MODERADA
                    alerta = AlertaDTO(
                        mensaje = f"Se ha percibido temperaturas minimas moderadas sin riesgo para la explotación el dia {fec_temp_min}",
                        recomendacion = "Prevenir heladas asegurando brotes en arboles frutales con agua y recubrimiento termico",
                        nivel = TipoAlerta.PREVENTIVA
                    )
                else:
                    nivel = NivelHelada.SIN_RIESGO
                    alertas = []
            
            # Pasamos la fecha a dia juliano para trabajar mejor con ella
            fecha_min = HeladaPredictionService.dia_juliano(fec_temp_min)
            print(f"Fecha juliana : {fecha_min}")
            prob = HeladaPredictionService.prob_helada_posterior(
                dia = fecha_min, 
                media = Config.MEDIA_ULTIMA_HELADA,
                desviacion = Config.DESVIACION_HELADA
            ) * 100 # Para obtener el porcentaje

            comentarios = (
                f"Prediccion realizada el {datetime.now()}. "
                f"Temperatura minima registrada: {temp_min} C. "
                f"Riesgo estadistico de heladas tardias: {prob:.2f}%."
            )

            contexto_de_calculo = ContextoCalculoDTO(
                tipos_datos = [TipoDato.HISTORICOS],
                prediccion_o_estimacion = TipoResultado.ESTIMACION,
                fuente = ["SiAR"],
                fecha_generacion = datetime.now()
            )
            
            # No incluyo predicción alta porque no tengo muchos datos
            predicciones.append(
                RiesgoHeladaDTO(
                    nivel = nivel,
                    temperatura_minima_estimada = temp_min,
                    comentarios = comentarios,
                    alertas = alertas,
                    contexto = contexto_de_calculo,
                    precision = TipoPrecision.MEDIA if prob >= 30 else TipoPrecision.BAJA
                )
            )

            # Limpio las alertas para no afectar a la siguiente iteracion
            alertas = []

        return predicciones

    @staticmethod
    def obtener_predicciones_helada(
        province_code : Optional[str],
        estacion_code : Optional[str],
        type : str,
        start_date : date,
        end_date : date
    ):
        client = DataServiceClient(app = current_app)
        datos = client.get_historic_data(
            province_code = province_code,
            estacion_code = estacion_code,
            type = type,
            start_date = start_date,
            end_date = end_date
        )

        if datos:
            predicciones = HeladaPredictionService._build_predictions(
                data = datos.get('datos')
            )

        return predicciones