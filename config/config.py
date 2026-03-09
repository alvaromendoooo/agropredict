import os
from dotenv import load_dotenv
import requests
from circuitbreaker import CircuitBreaker

load_dotenv()

class Config():
    DATA_SERVICE_HISTORIC_BASE_URL = os.getenv('DATA_SERVICE_HISTORIC_BASE_URL')
    DATA_SERVICE_FORECAST_BASE_URL = os.getenv('DATA_SERVICE_FORECAST_BASE_URL')
    DATA_SERVICE_CROP_BASE_URL = os.getenv('DATA_SERVICE_CROP_BASE_URL')
    DATA_SERVICE_SENSORES_BASE_URL = os.getenv('DATA_SERVICE_SENSORES_BASE_URL')
    DATA_SERVICE_CULTIVOS_BASE_URL = os.getenv('DATA_SERVICE_CULTIVOS_BASE_URL')

    """
        Debido a que el sistema se encuentra en un entorno de desarrollo 
        y no dispone todavía de un histórico climatológico suficientemente amplio, 
        los parámetros de la distribución normal (media y desviación típica) se han 
        definido de forma parametrizada a partir de valores de referencia extraídos 
        de estudios climatológicos generales. Estos parámetros se han diseñado como 
        configurables, de forma que puedan recalcularse automáticamente en futuras 
        versiones del sistema cuando se disponga de datos históricos suficientes 
        por zona.

        Si tuviera datos >= 10 o 15 años, debería de obtener sus últimos días de 
        helada y almacenarlos en una lista, con estos datos puedo obtener la 
        media y desviación típica real
    """


    MEDIA_ULTIMA_HELADA = 120   # configurable  # Año agrícola 1 octubre empieza
    DESVIACION_HELADA = 20     # configurable

class CircuitBreakerPersonalizado(CircuitBreaker):
    FAILURE_THRESHOLD = 7
    RECOVERY_TIMEOUT = 60
    EXPECTED_EXCEPTION = requests.exceptions.RequestException

class DevelopementConfig(Config):
    """DEVELOPEMENT CONFIG"""
    DEBUG = True
    TESTING = False

class TestingConfig(Config):
    """TESTING CONFIG"""
    DEBUG = False
    TESTING = True
    SQLALCHEMY_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")

class ProductionConfig(Config):
    """PRODUCTION CONFIG"""
    DEGUB = False
    TESTING = False

config = {
    'development': DevelopementConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopementConfig
}