from .plague_evaluate import EvaluarPlaga
from .prediction_dto import DatosSensorDTO, PrediccionMeteorologicaPlagas, RiesgoPlagaDTO, AlertaPlagaDTO
from datetime import datetime
from typing import Optional
import json

class PredictorPlagas:

    # Mapa de grupos de cultivo con evaluaciones de plagas
    PLAGAS_POR_GRUPO : dict[str, list] = {
        'hortaliza_fruto' : [
            EvaluarPlaga._evaluar_tomate_001,
        ],
        'arbol_frutal' : []
    }

    @staticmethod
    def _resumen_condiciones(
        sensores: list[DatosSensorDTO],
        meteo: PrediccionMeteorologicaPlagas,
    ) -> dict:
        hr_media = (
            round(sum(s.humedad_foliar for s in sensores) / len(sensores), 1)
            if sensores else None
        )
        t_hoja_media = (
            round(sum(s.temperatura_hojas for s in sensores) / len(sensores), 1)
            if sensores else None
        )
        return {
            "temp_max_aemet":   meteo.temperatura_maxima,
            "temp_min_aemet":   meteo.temperatura_minima,
            "precipitaciones":  meteo.precipitaciones,
            "estado_cielo":     meteo.estado_cielo,
            "hr_foliar_media":  hr_media,
            "t_hoja_media":     t_hoja_media,
            "n_lecturas_sensor": len(sensores),
        }
    
    @staticmethod
    def _build_prediccion_meteorologica(
        datos : dict
    ) -> Optional[PrediccionMeteorologicaPlagas]:
        try:
            if not datos:
                return
            
            calculo_temperatura_max = max(
                temp_loc.get('temperatura_maxima', 0) 
                for temp_loc in datos['datos'].get('temperatura_localidades', [])
            )

            calculo_temperatura_minima = min(
                temp_loc.get('temperatura_minima', 0)
                for temp_loc in datos['datos'].get('temperatura_localidades', [])
            )

            meteo_predict = PrediccionMeteorologicaPlagas(
                estado_cielo = datos['datos'].get('estado_cielo', ''),
                tendencia_temp_general = datos['datos'].get('tendencia_temp_general', ''),
                tendencia_temp_maxima = datos['datos'].get('tendencia_temp_max', ''),
                temperatura_minima = calculo_temperatura_minima,
                rachas_viento = datos['datos'].get('rachas_viento', ''),
                precipitaciones = datos['datos'].get('precipitaciones', ''),
                cotas_nieve = datos['datos'].get('cotas_nieve', ''),
                existencia_heladas = datos['datos'].get('existencia_heladas', ''),
                temperatura_maxima = calculo_temperatura_max,
                tendencia_temp_minima = calculo_temperatura_minima
            )

            if not meteo_predict:
                return 
            
            return meteo_predict

        except Exception as e:
            print(f"Error construyendo DTO de PrediccionMeteorologicaPlagas : {e}")
            return
        
    @staticmethod
    def _build_sensores(
        data
    ) -> Optional[list[DatosSensorDTO]]:
        """
        Genera DTOs cargados de DatosSensorDTO sobre los datos pasados por parámetros
        """

        if not data:
            return None
        
        lista_dto = []
        for sensor in data:
            dto = DatosSensorDTO(
                humedad_foliar = sensor['humedad_foliar'],
                temperatura_DS18B20 = sensor['temperatura_DS18B20'],
                temperatura_hojas = sensor['temperatura_hojas'],
                timestamp = sensor['timestamp']
            )

            if not dto:
                return None
            
            lista_dto.append(dto)

        return lista_dto

    @staticmethod
    def prediccion_plagas_predecibles(
        cultivos : list[dict],
        sensores_por_eui : dict[str, list[DatosSensorDTO]],
        prediccion_meteorologica : PrediccionMeteorologicaPlagas
    ) -> list[RiesgoPlagaDTO]:
        """
        Genera predicciones de plagas por cultivos sin calendario de riesgo externo
        (es decir, los que no son ni cereales ni leguminosos).

        :param cultivos: Lista de cultivos a analizar
        :type cultivos : list[dict]
        :param sensores_por_eui: Datos de sensores asociados al identificador eui del sensor
        :type sensores_por_eui : dict[str, list[DatosSensoresDTO]]
        :param prediccion_meteorologica : Datos climaticos obtenidos de AEMET
        :type prediccion_meteorologica : PrediccionMeteorologicaPlagas
        """
        predicciones : list[PrediccionMeteorologicaPlagas] = []
        fecha_evaluacion = datetime.now()

        for cultivo in cultivos:
            grupo = cultivo.get('grupo', '')
            evaluadores = PredictorPlagas.PLAGAS_POR_GRUPO.get(grupo, [])

            if not evaluadores:
                continue # El cultivo a analizar no tiene evaluadores asociados

            # Obtener la lecturas de sensores relacionados con el cultivo a evaluar
            eui = cultivo.get('sensor', '')
            sensores : list[DatosSensorDTO] = []
            if eui and eui in sensores_por_eui:
                sensores = sensores_por_eui[eui]

            # Cogemos los datos de los sensores de la última semana
            #sensores = sensores[-7:]
            #print(len(sensores))

            # Convierto el diccionario meteorológico de entrada en un DTO
            meteo_predict = PredictorPlagas._build_prediccion_meteorologica(prediccion_meteorologica)
            sensores = PredictorPlagas._build_sensores(sensores)

            resumen = PredictorPlagas._resumen_condiciones(
                sensores = sensores,
                meteo = meteo_predict
            )

            alertas = []

            for evaluador in evaluadores:
                try:
                    alerta = evaluador(
                        sensores, 
                        meteo_predict
                    )
                    alertas.append(alerta)
                except Exception as e:
                    print(f"Error evaluando la plaga del cultivo {cultivo['nombre']} : {e}")
                    continue 
                
            predicciones.append(
                RiesgoPlagaDTO(
                    nombre_cultivo = cultivo['nombre'],
                    fecha_evaluacion = fecha_evaluacion,
                    alertas = alertas,
                    resumen_condiciones = resumen
                )
            )

        return predicciones    
        

