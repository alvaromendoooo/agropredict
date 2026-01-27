import os
from dotenv import load_dotenv
import requests
from circuitbreaker import CircuitBreaker

load_dotenv()

class Config():
    DATA_SERVICE_HISTORIC_BASE_URL = os.getenv('DATA_SERVICE_HISTORIC_BASE_URL')
    DATA_SERVICE_FORECAST_BASE_URL = os.getenv('DATA_SERVICE_FORECAST_BASE_URL')

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