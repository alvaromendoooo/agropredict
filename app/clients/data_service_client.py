from .base_client import BaseClient
from circuitbreaker import circuit
from config.config import CircuitBreakerPersonalizado
from flask import Flask
from typing import Optional
from datetime import date, timedelta
import requests
import logging
import time

logger = logging.getLogger(__name__)

class DataServiceClient(BaseClient):
    def __init__(self, app : Flask):
        super().__init__(app, service_name = "data_service")
        self.base_historical_url = app.config.get('DATA_SERVICE_HISTORIC_BASE_URL')
        self.base_forecast_url = app.config.get('DATA_SERVICE_FORECAST_BASE_URL')

    @circuit(cls = CircuitBreakerPersonalizado)
    def get_historic_data_day(
        self,
        province_code : Optional[str],
        estacion_code : Optional[str],
        type : str,
        start_date : date,
        end_date : date
    ): 
        print(f"Provincia: {province_code}")
        try:
            
            if province_code:
                url = f"{self.base_historical_url}/provincias?provinceCode={province_code}&type={type}&startDate={start_date}&endDate={end_date}"
            elif estacion_code:
                url = f"{self.base_historical_url}/estacion?estacionCode={estacion_code}&type={type}&startDate={start_date}&endDate={end_date}"

            response = self._make_request(
                method = 'GET',
                url = url
            )

            if response.status_code == 404:
                logger.error("No se han encontrado datos para los parámetros indicados")
                return None
            if response.status_code >= 500:
                logger.error("Ha ocurrido un problema con el servidor al que te comunicas")
                return None
            
            response.raise_for_status()

            return response.json()
        
        except requests.RequestException as e:
            logger.error(f"Algo falló en la comunicación con data_service: {e}")
            return None
    
    def get_historic_data(
        self,
        province_code : Optional[str],
        estacion_code : Optional[str],
        type : str,
        start_date : date,
        end_date : date
    ):
        if province_code and estacion_code:
            logger.error("No se pueden indicar a la vez el codigo de provincia y el codigo de estacion, solo uno de ellos")
            return None
        
        datos = self.get_historic_data_day(
            province_code = province_code,
            estacion_code = estacion_code,
            type = type,
            start_date = start_date,
            end_date = end_date
        )

        # Para ingesta de data inexistente
        """
        resultado = []
        fecha = start_date
        while fecha <= end_date:
            fecha_aux = fecha
            fecha += timedelta(days=1)
            try:
                # Dejo tiempo para que dataservice procese la anterior consulta
                #time.sleep(20)
                # Llamada a la peticion de datos
                dato = self.get_historic_data_day(
                    province_code = province_code,
                    estacion_code = estacion_code,
                    type = type,
                    start_date = fecha_aux,
                    end_date = fecha
                )

                if not dato:
                    raise ValueError("No se ha recibido datos del cliente, posible error")
                
                # Control de errores producidos en el servicio al que me comunico
                if dato['status'] == 'FAILED':
                    logger.warning(f"Fallo obteniendo datos para la fecha {fecha} : {e}")
                    time.sleep(90) # Espera recomendada por SiAR

                resultado.append(dato)

            except Exception as e:
                # No quiero que se pare la ejecución del bucle, debido a que será un límite de consumo de SiAR
                logger.warning(f"Fallo obteniendo datos para la fecha {fecha} : {e}")
                # Esperamos el tiempo estipulado por SiAR hasta la siguiente petición
                # Una vez estén todos los datos en la BD, esto no nos preocupará
                time.sleep(90)
        
        if not resultado:
            return None
        """
        return datos
        
    @circuit(cls = CircuitBreakerPersonalizado)
    def get_future_data(
        self,
        province_code : Optional[str],
        ccaa_code : Optional[str],
        zona : str,
        prediccion : str
    ):
        try:
            if province_code and ccaa_code:
                logger.error("No se pueden indicar a la vez el codigo de provincia y el codigo de estacion, solo uno de ellos")
                return None

            if province_code:
                url = f"{self.base_forecast_url}/{zona}/{prediccion}?provinciaId={province_code}"
            elif ccaa_code:
                url = f"{self.base_forecast_url}/{zona}/{prediccion}?provinciaId={ccaa_code}"
            else: # nacional
                url = f"{self.base_forecast_url}/{zona}/{prediccion}"

            response = self._make_request(
                method = 'GET',
                url = url
            )

            return response.json()
        except Exception as e:
            logger.error(f"Algo fallo en la comunicación con el servicio : {e}")
            return None