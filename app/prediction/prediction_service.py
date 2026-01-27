from clients.data_service_client import DataServiceClient 
from .prediction_dto import *
from typing import Optional
from datetime import date

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
        return fecha.timetuple().tm_yday

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

        for d in data:
            # Obtenemos la temperatura mínima que nos devuelve el cliente
            temp_min = d.get('tempMin')
            # Obtenemos la fecha en la que se produjo esa temp_min
            fec_temp_min = d.get('horMinTempMin')


    @staticmethod
    def obtener_predicciones_helada(
        province_code : Optional[str],
        estacion_code : Optional[str],
        type : str,
        start_date : date,
        end_date : date
    ):
        datos = DataServiceClient.get_historic_data(
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

