from .base_client import BaseClient
from circuitbreaker import circuit
from config.config import CircuitBreakerPersonalizado
from flask import Flask
from typing import Optional
from datetime import date
import requests
import logging

logger = logging.getLogger(__name__)

class DataServiceClient(BaseClient):
    def __init__(self, app : Flask):
        super().__init__(app, service_name = "data_service")
        self.base_historical_url = app.config.get('DATA_SERVICE_HISTORIC_BASE_URL')
        self.base_forecast_url = app.config.get('DATA_SERVICE_FORECAST_BASE_URL')

    @circuit(cls = CircuitBreakerPersonalizado)
    def get_historic_data(
        self,
        province_code : Optional[str],
        estacion_code : Optional[str],
        type : str,
        start_date : date,
        end_date : date
    ): 
        print(f"Provincia: {province_code}")
        try:
            # Precondicion
            if province_code and estacion_code:
                logger.error("No se pueden indicar a la vez el codigo de provincia y el codigo de estacion, solo uno de ellos")
                return None
            
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