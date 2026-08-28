from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class SensoresDTO():
    timestamp : datetime
    campo : str
    valor : float

@dataclass
class TempLimitesDTO():
    max_valor: Optional[float]
    max_time: Optional[datetime]
    min_valor: Optional[float]
    min_time: Optional[datetime]

@dataclass
class GloablSensorDTO():
    eui : str
    resultados : Optional[list[SensoresDTO]]
    temp_limites : Optional[TempLimitesDTO] = None