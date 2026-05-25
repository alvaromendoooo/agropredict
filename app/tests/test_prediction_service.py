import pytest
from datetime import date
from unittest.mock import patch, MagicMock

from ..prediction.prediction_service import PredictionService

# ===============
# dia_juliano
# ===============
# Este método convierte una fecha en el día del año agrícola (que empieza el 1 de octubre).

class TestDiaJliano:

    def test_primer_dia_anio_agricola(self):
        """El 1 de octubre debe de ser el día 1 del año agrícola"""
        fecha = date(2025, 10, 1)
        assert PredictionService.dia_juliano(fecha) == 1
    
    def test_segundo_dia_anio_agricola(self):
        """El 2 de octubre debe ser el dia 2 del año agrícola"""
        fecha = date(2025, 10, 2)
        assert PredictionService.dia_juliano(fecha) == 2

    def test_fecha_en_enero_mismo_anio_agricola(self):
        """
        Enero de 2026 debe de pertenecer al año agrícola que comenzó el 1 de octubre 2025
        Del 1 de octubre al 1 de enero hay 92 días -> 93 días
        """
        fecha = date(2026, 1, 1)
        dias_esperados = (fecha - date(2025, 10, 1)).days + 1
        assert PredictionService.dia_juliano(fecha) == dias_esperados

    def test_fecha_antes_de_octbre_usa_anio_anterior(self):
        """
        Una fecha de 10 junio 2025 pertenece al año agrícola 2024
        """
        fecha = date(2025, 6, 1)
        inicio_esperado = date(2024, 10, 1)
        dias_esperados = (fecha - inicio_esperado).days + 1
        assert PredictionService.dia_juliano(fecha) == dias_esperados

    def test_ultimo_dia_anio_agricola(self):
        """El 30 de septiembre debe de ser el último día del calendario"""
        fecha = date(2025, 9, 30)
        inicio_esperado = date(2024, 10, 1)
        dias_esperados = (fecha - inicio_esperado).days + 1
        assert PredictionService.dia_juliano(fecha) == dias_esperados


# ==============================================================================
# prob_helada_posterior
# ==============================================================================
# Calcula la probabilidad de helada posterior a un día dado usando la
# distribución normal. Comprobamos rangos y casos extremos.

class TestProbHeladaPosterior:

    def test_prob_es_float(self):
        prob = PredictionService.prob_helada_posterior(dia = 100, media = 120, desviacion = 20)
        assert isinstance(prob, float)
        assert 0.0 <= prob <= 1.0

    def test_dia_igual_a_media_de_prob_050(self):
        """
        Si la media es igual al dia de evaluación, la probabilida de helada posterior 
        debe ser exactamente 0.5
        """
        prob = PredictionService.prob_helada_posterior(dia = 120, media = 120, desviacion = 20)
        assert abs(prob - 0.5) < 1e-9

    def test_dia_anterior_media(self):
        prob = PredictionService.prob_helada_posterior(dia = 50, media = 150, desviacion = 20)
        assert prob >= 0.8

    def test_dia_posterior_media(self):
        prob = PredictionService.prob_helada_posterior(dia = 250, media = 150, desviacion = 20)
        assert prob <= 0.2

# ==============================================================================
# calcular_nivel_riesgo_porcentaje
# ==============================================================================
# Esta es la función más importante del predictor: combina temperatura,
# humedad, viento y probabilidad histórica en un porcentaje de riesgo.
# Testeamos cada factor por separado y luego en combinación.
 
class TestCalcularNivelRiesgoPorcentaje:
 
    # --- Casos límite del resultado ---
 
    def test_resultado_entre_0_y_100(self):
        """El resultado nunca debe salirse del rango 0-100."""
        resultado = PredictionService.calcular_nivel_riesgo_porcentaje(
            temperatura=-10.0, humedad=100, viento=0, prob_heladas=1.0
        )
        assert 0 <= resultado <= 100
 
    def test_temperatura_bajo_cero_da_nivel_alto(self):
        """Temperatura <= 0 aporta 60 puntos base — el máximo del factor temperatura."""
        resultado = PredictionService.calcular_nivel_riesgo_porcentaje(
            temperatura=0.0, humedad=None, viento=None, prob_heladas=None
        )
        assert resultado == 60
 
    def test_temperatura_alta_da_nivel_bajo(self):
        """Con temperatura > 5 solo se suman 5 puntos base."""
        resultado = PredictionService.calcular_nivel_riesgo_porcentaje(
            temperatura=10.0, humedad=None, viento=None, prob_heladas=None
        )
        assert resultado == 5
 
    # --- Factor temperatura por rangos ---
 
    def test_temperatura_entre_0_y_1_6(self):
        resultado = PredictionService.calcular_nivel_riesgo_porcentaje(
            temperatura=1.0, humedad=None, viento=None, prob_heladas=None
        )
        assert resultado == 40
 
    def test_temperatura_entre_1_6_y_3(self):
        resultado = PredictionService.calcular_nivel_riesgo_porcentaje(
            temperatura=2.5, humedad=None, viento=None, prob_heladas=None
        )
        assert resultado == 20
 
    def test_temperatura_entre_3_y_5(self):
        resultado = PredictionService.calcular_nivel_riesgo_porcentaje(
            temperatura=4.0, humedad=None, viento=None, prob_heladas=None
        )
        assert resultado == 10
 
    # --- Factor humedad ---
 
    def test_humedad_alta_suma_10_puntos(self):
        """Humedad >= 80 añade 10 puntos al nivel base."""
        sin_humedad = PredictionService.calcular_nivel_riesgo_porcentaje(
            temperatura=10.0, humedad=None, viento=None, prob_heladas=None
        )
        con_humedad = PredictionService.calcular_nivel_riesgo_porcentaje(
            temperatura=10.0, humedad=85, viento=None, prob_heladas=None
        )
        assert con_humedad - sin_humedad == 10
 
    def test_humedad_media_suma_5_puntos(self):
        """Humedad entre 60 y 79 añade 5 puntos."""
        sin_humedad = PredictionService.calcular_nivel_riesgo_porcentaje(
            temperatura=10.0, humedad=None, viento=None, prob_heladas=None
        )
        con_humedad = PredictionService.calcular_nivel_riesgo_porcentaje(
            temperatura=10.0, humedad=70, viento=None, prob_heladas=None
        )
        assert con_humedad - sin_humedad == 5
 
    # --- Factor viento ---
 
    def test_poco_viento_aumenta_riesgo(self):
        """Viento < 5 km/h aumenta el riesgo en 5 puntos."""
        sin_viento = PredictionService.calcular_nivel_riesgo_porcentaje(
            temperatura=10.0, humedad=None, viento=None, prob_heladas=None
        )
        con_poco_viento = PredictionService.calcular_nivel_riesgo_porcentaje(
            temperatura=10.0, humedad=None, viento=2, prob_heladas=None
        )
        assert con_poco_viento - sin_viento == 5
 
    def test_mucho_viento_reduce_riesgo(self):
        """Viento > 15 km/h reduce el riesgo en 5 puntos."""
        sin_viento = PredictionService.calcular_nivel_riesgo_porcentaje(
            temperatura=10.0, humedad=None, viento=None, prob_heladas=None
        )
        con_mucho_viento = PredictionService.calcular_nivel_riesgo_porcentaje(
            temperatura=10.0, humedad=None, viento=20, prob_heladas=None
        )
        assert con_mucho_viento - sin_viento == -5
 
    # --- Factor probabilidad histórica ---
 
    def test_prob_heladas_suma_porcentaje_correcto(self):
        """prob_heladas=1.0 añade 30 puntos (100% del peso del factor)."""
        sin_prob = PredictionService.calcular_nivel_riesgo_porcentaje(
            temperatura=10.0, humedad=None, viento=None, prob_heladas=None
        )
        con_prob = PredictionService.calcular_nivel_riesgo_porcentaje(
            temperatura=10.0, humedad=None, viento=None, prob_heladas=1.0
        )
        assert con_prob - sin_prob == 30
 
    # --- Caso combinado realista ---
 
    def test_caso_critico_combinado(self):
        """
        Temperatura bajo cero + alta humedad + poco viento + alta probabilidad
        histórica debería dar un riesgo muy alto (cercano a 100).
        """
        resultado = PredictionService.calcular_nivel_riesgo_porcentaje(
            temperatura=-2.0,    # +60 puntos
            humedad=90,        # +10 puntos
            viento=1,          # +5 puntos
            prob_heladas=0.8   # +24 puntos → total = 99
        )
        assert resultado >= 90
 
    def test_caso_sin_riesgo_combinado(self):
        """
        Temperatura alta + baja humedad + viento fuerte + baja probabilidad
        histórica debería dar un riesgo mínimo.
        """
        resultado = PredictionService.calcular_nivel_riesgo_porcentaje(
            temperatura=15.0,
            humedad=30,
            viento=20,
            prob_heladas=0.05
        )
        assert resultado < 10
 
 
# ==============================================================================
# _recuento_riesgos
# ==============================================================================
# Función auxiliar simple pero importante: verifica que el contador de
# riesgos se inicializa correctamente con todos los niveles a 0.
 
class TestRecuentoRiesgos:
 
    def test_devuelve_todos_los_niveles(self):
        """El diccionario debe tener exactamente los 5 niveles de riesgo."""
        recuento = PredictionService._recuento_riesgos()
        niveles_esperados = {"critico", "alto", "moderado", "debil", "sin_riesgo"}
        assert set(recuento.keys()) == niveles_esperados
 
    def test_todos_los_valores_son_cero(self):
        """Todos los contadores deben empezar en 0."""
        recuento = PredictionService._recuento_riesgos()
        assert all(v == 0 for v in recuento.values())
 
    def test_devuelve_nueva_instancia_cada_vez(self):
        """Cada llamada debe devolver un diccionario nuevo, no el mismo objeto."""
        recuento1 = PredictionService._recuento_riesgos()
        recuento2 = PredictionService._recuento_riesgos()
        recuento1["critico"] = 99
        assert recuento2["critico"] == 0  # no deben compartir estado
 
 
# ==============================================================================
# _temperatura_minima_futuros_calculada
# ==============================================================================
 
class TestTemperaturaMinimaFuturosCalculada:
 
    def test_devuelve_la_minima_correcta(self):
        """Debe devolver la temperatura mínima entre todas las localidades."""
        localidades = [
            {"temperatura_minima": 3.0},
            {"temperatura_minima": -1.5},
            {"temperatura_minima": 2.0},
        ]
        resultado = PredictionService._temperatura_minima_futuros_calculada(localidades)
        assert resultado == -1.5
 
    def test_una_sola_localidad(self):
        """Con una sola localidad, devuelve su temperatura."""
        localidades = [{"temperatura_minima": 4.5}]
        resultado = PredictionService._temperatura_minima_futuros_calculada(localidades)
        assert resultado == 4.5
 
    def test_temperaturas_negativas(self):
        """Debe funcionar correctamente cuando todas las temperaturas son negativas."""
        localidades = [
            {"temperatura_minima": -3.0},
            {"temperatura_minima": -5.5},
            {"temperatura_minima": -1.0},
        ]
        resultado = PredictionService._temperatura_minima_futuros_calculada(localidades)
        assert resultado == -5.5