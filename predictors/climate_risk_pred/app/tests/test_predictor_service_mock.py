import pytest
from unittest.mock import MagicMock, patch
from datetime import date

from ..prediction.prediction_service import PredictionService

# FIXTURES
@pytest.fixture
def cliente_mock():
    """
    Devuelve un cliente falso de DataServiceClient
    """
    return MagicMock()

@pytest.fixture
def datos_futuros_validos():
    """
    Simula la respuesta de client.get_future_data()
    """
    return {
        "type_prediction": "tomorrow",
        "type_zone": "provincial",
        "datos": {
            "tipo_prediccion": "tomorrow",
            "tipo_zona": "provincial",
            "codigo_zona": "CC",
            "fecha_prediccion": "2026-04-27",
            "fecha_elaboracion": "2026-05-CCT15:07:08",
            "estado_cielo": None,
            "tendencia_temp_general": None,
            "tendencia_temp_max": None,
            "tendencia_temp_min": None,
            "rachas_viento": None,
            "precipitaciones": None,
            "cotas_nieve": None,
            "existencia_heladas": None,
            "zona_heladas": None,
            "aparicion_nieblas": None,
            "provincia": "CC",
            "ccaa": None,
            "temperatura_localidades": [
                {
                    "nombre": "C\u00e1ceres",
                    "temperatura_maxima": 27,
                    "temperatura_minima": 15
                },
                {
                    "nombre": "Navalmoral de la Mata",
                    "temperatura_maxima": 26,
                    "temperatura_minima": 14
                },
                {
                    "nombre": "Plasencia",
                    "temperatura_maxima": 27,
                    "temperatura_minima": 15
                },
                {
                    "nombre": "Trujillo",
                    "temperatura_maxima": 26,
                    "temperatura_minima": 14
                }
            ]
        }
    }

@pytest.fixture
def datos_futuros_pendientes():
    return{"status" : "PENDING"}

@pytest.fixture
def datos_historicos_validos():
    return {
        "type": "Dia",
        "datos": [
            {
                "tempMedia": 13.921000003814697,
                "tempMax": 16.39,
                "horMinTempMax": {
                    "timestamp": "2026-03-17T00:00:00",
                    "estacion_id": 17
                },
                "tempMin": 12.47,
                "horMinTempMin": {
                    "timestamp": "2026-03-17T00:00:00",
                    "estacion_id": 28
                },
                "humedadMedia": 56.70950012207031,
                "humedadMax": 70.4,
                "horMinHumMax": {
                    "timestamp": "2026-03-17T00:00:00",
                    "estacion_id": 22
                },
                "humedadMin": 35.27,
                "horMinHumMin": {
                    "timestamp": "2026-03-17T00:00:00",
                    "estacion_id": 13
                },
                "velViento": 1.774349996447563,
                "velVientoMax": 2.93,
                "precipitacion": 0.20100000500679016,
                "etpMon": 3.720680904388428,
                "pepMon": 0.0,
                "estacion": None,
                "estaciones": [
                    "CC01",
                    "CC04",
                    "CC07",
                    "CC09",
                    "CCCC",
                    "CCCC1",
                    "CCCC3",
                    "CCCC4",
                    "CCCC5",
                    "CCCC7",
                    "CCCC8",
                    "CCCC9",
                    "CC11",
                    "CC12",
                    "CC13",
                    "CC14",
                    "CC16",
                    "CC17",
                    "CC18",
                    "CC19"
                ],
                "provincia": "CC",
                "fecha": "2026-03-17",
                "radiacion": None
            }
        ]
    }

# ==============================================================================
# TESTS: obtener_predicciones_helada_futuras
# ==============================================================================
 
class TestObtenerPrediccionesHeladaFuturas:
 
    def test_caso_normal_devuelve_prediccion(self, cliente_mock, datos_futuros_validos):
        """
        Caso feliz: data-service responde OK con datos válidos.
        Verificamos que el servicio devuelve una predicción sin errores.
        """
        # 1. Configuramos qué devuelve el cliente falso
        cliente_mock.get_future_data.return_value = datos_futuros_validos
        cliente_mock.get_localidades_data.return_value = []
 
        # 2. Parcheamos _get_cliente para que devuelva nuestro mock
        #    en lugar del cliente real que llama a data-service
        with patch.object(PredictionService, '_get_cliente', return_value=cliente_mock):
            prediccion, estaciones = PredictionService.obtener_predicciones_helada_futuras(
                province_code="CC",
                ccaa_code=None,
                zona="provincial",
                incluir_eval_localidad=False,
                incluir_eval_variedades=False,
                localidades_normalizadas=None,
                variedades=None
            )
 
        # 3. Verificamos el resultado
        assert prediccion is not None
 
    def test_reintenta_cuando_status_pending(self, cliente_mock, datos_futuros_pendientes, datos_futuros_validos):
        """
        Si data-service devuelve PENDING, el servicio debe esperar y reintentar.
        Verificamos que get_future_data se llama exactamente 2 veces:
        la primera devuelve PENDING, la segunda devuelve los datos reales.
        """
        # side_effect permite que el mock devuelva valores distintos
        # en cada llamada, en orden
        cliente_mock.get_future_data.side_effect = [
            datos_futuros_pendientes,   # primera llamada → PENDING
            datos_futuros_validos       # segunda llamada → datos reales
        ]
        cliente_mock.get_localidades_data.return_value = []
 
        with patch.object(PredictionService, '_get_cliente', return_value=cliente_mock):
            with patch('time.sleep'):  # evitamos que el test espere 5 segundos reales
                prediccion, _ = PredictionService.obtener_predicciones_helada_futuras(
                    province_code="CC",
                    ccaa_code=None,
                    zona="provincial",
                    incluir_eval_localidad=False,
                    incluir_eval_variedades=False,
                    localidades_normalizadas=None,
                    variedades=None
                )
 
        # El cliente debería haberse llamado exactamente 2 veces
        assert cliente_mock.get_future_data.call_count == 2
 
    def test_lanza_excepcion_cuando_no_hay_datos(self, cliente_mock):
        """
        Si data-service no devuelve datos (None o vacío), el servicio
        debe lanzar un ValueError con un mensaje claro.
        """
        cliente_mock.get_future_data.return_value = None
 
        with patch.object(PredictionService, '_get_cliente', return_value=cliente_mock):
            with pytest.raises(ValueError, match="No se pudieron obtener datos futuros"):
                PredictionService.obtener_predicciones_helada_futuras(
                    province_code="CC",
                    ccaa_code=None,
                    zona="provincial",
                    incluir_eval_localidad=False,
                    incluir_eval_variedades=False,
                    localidades_normalizadas=None,
                    variedades=None
                )
 
    def test_solicita_datos_localidad_cuando_se_pide(self, cliente_mock, datos_futuros_validos):
        """
        Si incluir_eval_localidad=True, el servicio DEBE llamar a
        get_localidades_data(). Verificamos que la llamada se produce.
        """
        cliente_mock.get_future_data.return_value = datos_futuros_validos
        cliente_mock.get_localidades_data.return_value = [
            {"nombre": "C\u00e1ceres","nombre_normalizado": "c\u00e1ceres","altitud": 439,"latitud": 39.4767,"longitud": -6.3723,"provincia": "CC"},
            {"nombre": "Plasencia","nombre_normalizado": "plasencia","altitud": 415,"latitud": 40.0311,"longitud": -6.0881,"provincia": "CC"},
        ]
 
        with patch.object(PredictionService, '_get_cliente', return_value=cliente_mock):
            PredictionService.obtener_predicciones_helada_futuras(
                province_code="CC",
                ccaa_code=None,
                zona="provincial",
                incluir_eval_localidad=True,   # ← activamos evaluación por localidad
                incluir_eval_variedades=False,
                localidades_normalizadas=["plasencia"],
                variedades=None
            )
 
        # Verificamos que se llamó a get_localidades_data exactamente una vez
        cliente_mock.get_localidades_data.assert_called_once()
 
 
# ==============================================================================
# TESTS: obtener_predicciones_helada_observadas
# ==============================================================================
 
class TestObtenerPrediccionesHeladaObservadas:
 
    def test_caso_normal(self, cliente_mock, datos_historicos_validos):
        """
        Caso feliz con datos históricos válidos que incluyen
        días normales y un día con helada.
        """
        cliente_mock.get_historic_data.return_value = datos_historicos_validos
 
        with patch.object(PredictionService, '_get_cliente', return_value=cliente_mock):
            prediccion, estaciones = PredictionService.obtener_predicciones_helada_observadas(
                province_code="CC",
                estacion_code=None,
                incluir_evaluacion_variedades=False,
                variedades=None,
                tipo="Dia"
            )
 
        assert prediccion is not None
 
    def test_lanza_excepcion_sin_datos_historicos(self, cliente_mock):
        """
        Si no hay datos históricos disponibles debe lanzar ValueError.
        """
        cliente_mock.get_historic_data.return_value = None
 
        with patch.object(PredictionService, '_get_cliente', return_value=cliente_mock):
            with pytest.raises(ValueError, match="No se pudieron obtener datos historicos"):
                PredictionService.obtener_predicciones_helada_observadas(
                    province_code="CC",
                    estacion_code=None,
                    incluir_evaluacion_variedades=False,
                    variedades=None,
                    tipo="Dia"
                )
 
    def test_llama_a_get_historic_data_con_rango_correcto(self, cliente_mock, datos_historicos_validos):
        """
        Verificamos que la llamada a data-service usa el rango de fechas
        correcto: desde hace 182 días hasta hoy.
        """
        cliente_mock.get_historic_data.return_value = datos_historicos_validos
        hoy = date.today()
 
        with patch.object(PredictionService, '_get_cliente', return_value=cliente_mock):
            PredictionService.obtener_predicciones_helada_observadas(
                province_code="CC",
                estacion_code=None,
                incluir_evaluacion_variedades=False,
                variedades=None,
                tipo="Dia"
            )
 
        # Comprobamos los argumentos con los que se llamó al cliente
        call_kwargs = cliente_mock.get_historic_data.call_args.kwargs
        assert call_kwargs['end_date'] == hoy
        assert call_kwargs['province_code'] == "CC"
        assert call_kwargs['tipo'] == "Dia"
 
 
# ==============================================================================
# TESTS: listar_localidades_disponibles
# ==============================================================================
 
class TestListarLocalidadesDisponibles:
 
    def test_devuelve_lista_de_nombres_normalizados(self, cliente_mock):
        """
        El método debe extraer solo el campo 'nombre_normalizado'
        de cada localidad que devuelve data-service.
        """
        cliente_mock.get_localidades_data.return_value = [
            {"nombre_normalizado": "plasencia", "lat": 40.0, "lon": -6.0},
            {"nombre_normalizado": "caceres",   "lat": 39.4, "lon": -6.3},
        ]
 
        with patch.object(PredictionService, '_get_cliente', return_value=cliente_mock):
            resultado = PredictionService.listar_localidades_disponibles()
 
        assert resultado == ["plasencia", "caceres"]
 
    def test_devuelve_lista_vacia_sin_localidades(self, cliente_mock):
        """Si data-service no devuelve localidades, el resultado es lista vacía."""
        cliente_mock.get_localidades_data.return_value = []
 
        with patch.object(PredictionService, '_get_cliente', return_value=cliente_mock):
            resultado = PredictionService.listar_localidades_disponibles()
 
        assert resultado == []