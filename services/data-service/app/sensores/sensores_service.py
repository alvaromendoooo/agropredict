from .sensores_dao import SensoresDAO
from .sensores_dto import SensoresDTO, GloablSensorDTO, TempLimitesDTO
from typing import Optional
from datetime import date
from helpers.ApiExceptions import APIException
import logging

logger = logging.getLogger(__name__)

class SensoresService():

    @staticmethod
    def _build_sensores_dto(data: list) -> Optional[list]:
        if not data:
            return None

        agrupado = {}  # {eui: GloablSensorDTO}

        for d in data:
            for sensor in d:
                eui = sensor['sensor_id']
                resultado = SensoresDTO(
                    timestamp=sensor.get('timestamp'),
                    campo=sensor.get('campo'),
                    valor=sensor.get('valor'),
                )

                if eui not in agrupado:
                    agrupado[eui] = GloablSensorDTO(eui=eui, resultados=[])
                
                agrupado[eui].resultados.append(resultado)

        return list(agrupado.values())[0] if len(agrupado) == 1 else list(agrupado.values())

    @staticmethod
    def get_sensor_data(
        euis : list[str],
        fecha_inicio : date,
        fecha_fin : date,
        nombre_predictor : str,
    ):
        """
        Obtiene los datos de sensor almacenados en la base de datos
        en base a los valores de parámetros pasados

        :param euis: Lista de identificadores públicos del sensor que obtiene los datos
        :type euis: list[str]
        :param fecha_inicio: Fecha comienzo de recogida de datos
        :type fecha_inicio: date
        :param fecha_fin: Fecha fin de recogida de datos
        :type fecha_fin: date
        :param nombre_predictor: Nombre del campo de medición asociado a los datos consultados
        :type nombre_predictor: str
        """
        sensores_existentes = []
        for eui in euis:
            existe_sensor = SensoresDAO.existe_sensor(
                eui = eui
            )

            if existe_sensor:
                sensores_existentes.append(eui)

        if not sensores_existentes:
            raise APIException(
                status = 404,
                message = f"No existe ningún sensor registrado con los euis indicados: {euis}",
                error = "Data Not Found"
            )

        # Obtengo los datos de los sensores almacenados en la base de datos
        datos_resultantes = []
        for eui in sensores_existentes:
            datos = SensoresDAO.consultar_datos_sensores(eui, fecha_inicio, fecha_fin)
            if datos:
                datos_resultantes.append(datos)

        if not datos_resultantes:
            raise APIException(
                status = 404,
                message = "No se han encontrado datos de sensores para los parámetros indicados",
                error = "Data Not Found"
            )

        dto_cargado = SensoresService._build_sensores_dto(
            data = datos_resultantes
        )

        return dto_cargado