from flask import current_app
from datetime import date
from helpers.ApiExceptions import APIException
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

class DTAgroService:
    _cliente = None

    @classmethod
    def _get_cliente(cls):
        """Lazy initialization: crea el cliente solo cuando se necesita"""
        if cls._cliente is None:
            from ..clients.sensor_client import DTAgroClient
            cls._cliente = DTAgroClient(app=current_app)
        return cls._cliente
    
    @classmethod
    def get_dtagro_datos(
        cls,
        euis: list[str],
        fecha_inicio: list[date] | date,
        fecha_fin: date,
        nombre_dtagro: str,
        nombre_predictor: str
    ):
        cliente = cls._get_cliente()
        lista_resultados = []
        for iter, eui in enumerate(euis):
            fec_init = fecha_inicio if isinstance(fecha_inicio, date) else fecha_inicio[iter]

            if nombre_predictor in ['temperatura_max', 'temperatura_min']:
                lista_datos = []
                cursor = fecha_inicio
                while cursor <= fecha_fin:
                    try:
                        datos_por_eui = cliente.get_dtagro_temp_max_min_sensor(
                            eui           = eui,
                            fec_init      = cursor,
                            fec_fin       = cursor + timedelta(days = 1), # Si hago la consulta 2026-05-05 | 2026-05-05 me devuelve null, la fecha final debe diferir un dia con la fecha inicial
                            nombre_dtagro = nombre_dtagro
                        )
                    except APIException as e:
                        logger.warning(f"Fallo API DTAgro {eui} {cursor}: {e}")
                        datos_por_eui = None

                    if not datos_por_eui: # No quiero que se pare la ejecución si para un día no obtengo datos
                        lista_datos.append({
                            "timestamp": cursor,
                            nombre_predictor: None
                        })
                        cursor += timedelta(days=1)
                        continue

                    tipo = "max" if nombre_predictor == "temperatura_max" else "min"

                    lista_datos.append({
                        "timestamp": datos_por_eui[tipo].get("time", None),
                        nombre_predictor: datos_por_eui[tipo].get("value", None),
                    })
                    cursor += timedelta(days = 1)
        
            else:
                datos_por_eui = cliente.get_dtagro_data(
                    eui          = eui,
                    fecha_inicio = fec_init,
                    fecha_fin    = fecha_fin
                )
                lista_datos = [
                    {
                        "timestamp": dato['time'],
                        f"{nombre_predictor}": dato['measurements'].get(nombre_dtagro)
                    }
                    for dato in datos_por_eui
                ]

            lista_resultados.append({'eui': eui, 'resultados': lista_datos})

        return lista_resultados
