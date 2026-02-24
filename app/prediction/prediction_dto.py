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
    variedad : str
    nombre_cientifico : str
    etapa_fenologica : str
    temperatura_evaluada : str
    porcentaje_riesgo : float
    nivel_riesgo : str
    umbrales : UmbralesCultivoDTO
    alertas : list[AlertaDTO]

@dataclass
class CotaNieveDTO:
    cota_minima : int
    cota_maxima : int
    hay_descenso : bool
    texto_original : str

@dataclass
class AnalisisLocalidadDTO:
    localidad : str
    provincia : str
    altitud_metros : int
    temperatura_minima : Optional[int]
    temperatura_maxima : Optional[int]
    nivel_riesgo : str
    resumen : str
    recomendaciones : list[str]
    porcentaje_riesgo : float
    cota_nieve : Optional[CotaNieveDTO]

@dataclass
class ResumenCultivoDTO:
    total_variedades_evaluados : int
    variedades_en_riesgo_critico : int
    variedades_en_riesgo_alto : int
    variedades_en_riesgo_moderado : int
    variedades_en_riesgo_debil : int
    variedades_sin_riesgo : int
    evaluaciones : list[AnalisisCultivoDTO]

@dataclass
class ResumenEvaluacionLocalidadDTO:
    total_localidades_evaluadas : int
    localidades_riesgo_critico : int
    localidades_riesgo_alto : int
    localidades_riesgo_moderado : int
    localidades_riesgo_bajo : int
    localidades_sin_riesgo : int
    evaluaciones : List[AnalisisLocalidadDTO]

@dataclass
class DatoAEMETDTO:
    estado_cielo : Optional[str]
    tendencia_temp_general : Optional[str]
    tendencia_temp_maxima : Optional[str]
    tendencia_temp_minima : Optional[str]
    rachas_viento : Optional[str]
    precipitaciones : Optional[str]
    cotas_nieve : Optional[str]
    existencia_heladas : Optional[str]
    zona_heladas = Optional[str]
    aparicion_nieblas = Optional[str]

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
    evaluaciones_variedades : Optional[ResumenCultivoDTO]
    riesgos_heladas_blancas : list[RiesgoHeladaTipoDTO]
    riesgos_heladas_negras : list[RiesgoHeladaTipoDTO]

@dataclass
class RiesgoHeladaObservadaDTO(RiesgoHeladaBaseDTO):
    fecha_comiezo_registros : date
    fecha_fin_registros : date
    registro_temperatura_minima : RegistroTempMinDTO
    
@dataclass
class RiesgoHeladaFuturaDTO(RiesgoHeladaBaseDTO):
    precision : TipoPrecision
    datos_meteorologicos : DatoAEMETDTO
    evaluacion_localidades : Optional[ResumenEvaluacionLocalidadDTO]
