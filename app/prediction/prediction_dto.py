from dataclasses import dataclass
from typing import List
from datetime import datetime
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

@dataclass
class AlertaDTO:
    mensaje : str
    recomendacion : str
    nivel : TipoAlerta

@dataclass
class ContextoCalculoDTO:
    tipos_datos : List[TipoDato]
    prediccion_o_estimacion : TipoResultado
    fuente : List[str]
    fecha_generacion : datetime

@dataclass
class RiesgoHeladaDTO:
    nivel : NivelHelada
    temperatura_minima_estimada : float
    comentarios : str
    alertas : List[AlertaDTO]
    contexto : ContextoCalculoDTO
    precision : TipoPrecision
