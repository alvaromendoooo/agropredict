import sys
import os

# 1. Ruta actual: frost_predictor/app/tests
ruta_actual = os.path.dirname(os.path.abspath(__file__))

# 2. Ruta app: frost_predictor/app
ruta_app = os.path.abspath(os.path.join(ruta_actual, '..')) 

# 3. Ruta raíz: frost_predictor
ruta_raiz = os.path.abspath(os.path.join(ruta_app, '..'))

# AÑADIMOS SOLO LA RAÍZ DEL PROYECTO
if ruta_raiz not in sys.path:
    sys.path.insert(0, ruta_raiz)

import unittest
from datetime import datetime, date
from app.prediction.prediction_service import PredictionService
from app.prediction.plague_evaluate import EvaluarPlaga

# Clases DTO simuladas (solo para que el test corra aquí si no tienes los imports)
class SensoresDTO:
    def __init__(self, humedad_foliar, temperatura_DS18B20, temperatura_hojas, timestamp):
        self.humedad_foliar = humedad_foliar
        self.temperatura_DS18B20 = temperatura_DS18B20
        self.temperatura_hojas = temperatura_hojas
        self.timestamp = timestamp

class GloablSensorDTO:
    def __init__(self, eui, resultados):
        self.eui = eui
        self.resultados = resultados

class TestPredictorPlagas(unittest.TestCase):

    def setUp(self):
        # Este método se ejecuta antes de cada test. Preparamos datos falsos.
        self.dia_prueba = date(2026, 4, 17)
        
        # Simulamos 2 lecturas el día 17 y 1 lectura el día 18
        self.datos_falsos = [
            GloablSensorDTO(
                eui="sensor-1",
                resultados=[
                    SensoresDTO(humedad_foliar=80.0, temperatura_DS18B20=10.0, temperatura_hojas=11.0, timestamp=datetime(2026, 4, 17, 10, 0)),
                    SensoresDTO(humedad_foliar=90.0, temperatura_DS18B20=20.0, temperatura_hojas=21.0, timestamp=datetime(2026, 4, 17, 16, 0)),
                    SensoresDTO(humedad_foliar=50.0, temperatura_DS18B20=25.0, temperatura_hojas=26.0, timestamp=datetime(2026, 4, 18, 10, 0)) # Otro día
                ]
            )
        ]

        self.cultivo_asociado_plaga = [
        {
                "cultivo": {
                    "nombre": "Berenjena",
                    "nombre_cientifico": "Solanum melongena",
                    "descripcion": "Prueba",
                    "grupo": "hortaliza_fruto"
                },
                "plaga": [
                    {
                        "public_id": "PLAGA-PRUEBA-01",
                        "nombre": "Mildiu",
                        "agente_causante": "microorganismos de la clase Oomicetos (falsos hongos)",
                        "momento_critico": "Brotación y primeros brotes (Primavera): Con pámpanos de al menos 10 cm, lluvias superiores a 10 mm y temperaturas medias superiores a 10 °C (la regla de los tres dieces), las oosporas invernales germinan, provocando las infecciones primarias.",
                        "observaciones": "",
                        "mas_info": "https://www.juntadeandalucia.es/agriculturapescaaguaydesarrollorural/raif/sintomatologia-y-medidas-preventivas-del-mildiu-en-el-cultivo-de-la-vid/",
                        "tipo": "hongo",
                        "grupo": "hortaliza_fruto",
                        "condiciones_evaluables": [
                            {
                                "tipo": "temperatura_media",
                                "valor": 10,
                                "operador": ">="
                            },
                            {
                                "tipo": "precipitacion",
                                "valor": 10,
                                "operador": ">="
                            },
                            {
                                "tipo": "estado_fenologico",
                                "valor": "brotacion"
                            }
                        ],
                        "calendario": []
                    }
                ],
                "recursos": [
                    {
                        "nombre": "humedad_hoja",
                        "descripcion": "Humedad superficial de la hoja (mojadura foliar)"
                    },
                    {
                        "nombre": "radiacion_solar",
                        "descripcion": "Radiación solar global (W/m²)"
                    },
                    {
                        "nombre": "velocidad_viento",
                        "descripcion": "Velocidad del viento (m/s)"
                    },
                    {
                        "nombre": "precipitacion",
                        "descripcion": "Precipitación acumulada (mm)"
                    },
                    {
                        "nombre": "humedad_relativa",
                        "descripcion": "Humedad relativa del aire (%)"
                    },
                    {
                        "nombre": "temperatura_aire",
                        "descripcion": "Temperatura del aire ambiente (°C)"
                    }
                ]
            }
        ]

        self.condiciones_mildiu = self.cultivo_asociado_plaga['plaga'][0]['condiciones_evaluables']

    def test_filtrar_y_agregar_datos(self):
        """Prueba que los datos se filtren por día y se haga bien la media"""
        resultado = PredictionService._filtrar_y_agregar_datos_por_dia(self.datos_falsos, self.dia_prueba)

        # Verificamos que ignoró el día 18 y calculó bien las medias del día 17
        # Temperatura: (10 + 20) / 2 = 15.0
        # Humedad: (80 + 90) / 2 = 85.0
        self.assertEqual(resultado["temperatura_media"], 15.0)
        self.assertEqual(resultado["humedad_foliar"], 85.0)

    def test_evaluar_plaga_generica_cumple_todo(self):
        """Prueba que el evaluador devuelve nivel CRITICO si se cumple todo"""
        datos_del_dia = {
            "temperatura_media": 15.0, # Cumple (>= 10)
            "humedad_foliar": 85.0     # Cumple (>= 85)
        }

        alerta = EvaluarPlaga.evaluar_plaga_generica(self.condiciones_mildiu, datos_del_dia)

        # Asumiendo que TipoAlerta.CRITICA es 2 o el string "CRITICA", adáptalo a tu Enum
        self.assertEqual(len(alerta.condiciones_cumplidas), 2)
        self.assertEqual(len(alerta.condiciones_pendientes), 0)

    def test_evaluar_plaga_generica_cumple_parcial(self):
        """Prueba que el evaluador detecta qué falla y ajusta el nivel"""
        datos_del_dia = {
            "temperatura_media": 8.0,  # Falla (< 10)
            "humedad_foliar": 90.0     # Cumple (>= 85)
        }

        alerta = EvaluarPlaga.evaluar_plaga_generica(self.condiciones_mildiu, datos_del_dia)

        self.assertEqual(len(alerta.condiciones_cumplidas), 1)
        self.assertEqual(len(alerta.condiciones_pendientes), 1)
        self.assertTrue("temperatura_media insuficiente" in alerta.condiciones_pendientes[0])

if __name__ == '__main__':
    unittest.main()