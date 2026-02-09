from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime, date
from enum import Enum

class NivelHelada(str, Enum):
    SIN_RIESGO = "sin_riesgo"
    DEBIL = "debil"
    MODERADA = "moderada"
    FUERTE = "fuerte"

class TipoDato(str, Enum):
    ACTUALES = "actuales"
    FUTUROS = "futuros"
    HISTORICOS = "historicos"

class TipoResultado(str, Enum):
    PREDICCION = "prediccion"
    ESTIMACION = "estimacion"

class TipoPrecision(str, Enum):
    ALTA = "alta"
    MEDIA = "media"
    BAJA = "baja"

class TipoAlerta(str, Enum):
    INFORMATIVA = "informativa"
    PREVENTIVA = "preventiva"
    CRITICA = "critica"

class TipoPrediccion(str, Enum):
    CURRENT = "hoy",
    TOMORROW = "manana",
    AFTERTOMORROW = "pasadomanana"

@dataclass
class AlertaDTO:
    mensaje : str
    recomendacion : str
    nivel : TipoAlerta

@dataclass
class RegistroTempMinDTO:
    dias_bajo_cero : int
    temperatura_minima_registrada : float
    fecha_temp_bajo_cero : list[datetime]

@dataclass
class UmbralesCultivoDTO:
    critico : float
    alto : float
    moderado : float
    bajo : float

@dataclass
class AnalisisCultivoDTO:
    cultivo : str
    nombre_cientifico : str
    etapa_fenologica : str
    temperatura_evaluada : str
    nivel_riesgo : str
    umbrales : UmbralesCultivoDTO
    alertas : list[AlertaDTO]

@dataclass
class ResumenCultivoDTO:
    total_cultivos_evaluados : int
    cultivos_en_riesgo_critico : int
    cultivos_en_riesgo_alto : int
    cultivos_en_riesgo_moderado : int
    cultivos_en_riesgo_debil : int
    cultivos_sin_riesgo : int
    evaluaciones : list[AnalisisCultivoDTO]


@dataclass
class RiesgoHeladaTipoDTO:
    humedad : float
    temperatura : float
    timestamp : datetime
    estacion_id_temp : int
    estacion_id_hum : list[int]

@dataclass
class ContextoCalculoDTO:
    tipos_datos : List[TipoDato]
    prediccion_o_estimacion : TipoResultado
    fuente : List[str]
    fecha_generacion : datetime

@dataclass
class RiesgoHeladaBaseDTO:
    nivel : NivelHelada
    comentarios : str
    alertas : list[AlertaDTO]
    contexto : ContextoCalculoDTO
    tipo_prediccion : TipoPrediccion
    evaluaciones_cultivo : Optional[ResumenCultivoDTO]

@dataclass
class RiesgoHeladaObservadaDTO(RiesgoHeladaBaseDTO):
    fecha_comiezo_registros : date
    fecha_fin_registros : date
    registro_temperatura_minima : RegistroTempMinDTO
    riesgos_heladas_blancas : list[RiesgoHeladaTipoDTO]
    riesgos_heladas_negras : list[RiesgoHeladaTipoDTO]
    
@dataclass
class RiesgoHeladaFuturaDTO(RiesgoHeladaBaseDTO):
    precision : TipoPrecision
