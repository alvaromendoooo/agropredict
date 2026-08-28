"""
Configuración de umbrales para diversos cultivos y estados fenologicos
"""
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Optional

class EtapaFenologica(str, Enum):
    """
    Etapas fenologicas por las que pasa un cultivo
    """
    DORMANCIA = "dormancia" # Empieza en otoño, se detiene el crecimiento de la yema
    BROTANCIA = "brotancia" # Primeros brotes
    FLORACION = "floracion" # Apertura de los brotes generando flores
    CUAJADO = "cuajado" # Formacion del fruto
    ENGORDE = "engorde" # Crecimiento del fruto
    MADURACION = "maduracion" # Maduracion del fruto en la planta
    COSECHA = "cosecha" # Epoca de cosecha

@dataclass
class UmbralTemperatura:
    """
    Definicion de umbrales de temperatura para cultivos en etapas específicas
    """
    critico : float
    alto : float
    moderado : float
    bajo : float

    def clasificar_temperatura(
        self,
        temp : float
    ) -> tuple[str, str]:
        """
        Clasificacion de temperatura segun los umbrales definidos
        
        :param temp: Temperatura a clasificar
        :type temp: float
        :return: Tupla (nivel_riesgo, descripcion)
        :rtype: tuple[str, str]
        """
        if temp <= self.critico:
            return ("fuerte", "Riesgo crítico de daño severo")
        elif temp <= self.alto:
            return ("moderada", "Alto riesgo de daño significativo")
        elif temp <= self.moderado:
            return ("debil", "Riego bajo de daño, pero tomar precauciones futuras")
        elif temp <= self.bajo:
            return ("sin_riesgo", "No existen riesgos de daño")
        else:
            return ("sin_riesgo", "No existen riesgos de daño")
        
@dataclass
class ConfiguracionCultivo:
    """
    Configuracion completa de un cultivo con sus umbrales por etapa
    """
    nombre : str
    nombre_cientifico : str
    umbrales_por_etapa : Dict[EtapaFenologica, UmbralTemperatura]
    descripcion : Optional[str] = None

    def get_umbral(
        self, 
        etapa : EtapaFenologica
    ) -> UmbralTemperatura:
        """
        Obtiene el umbral de temperatura en base a la etapa fenologica del cultivo
        """
        return self.umbrales_por_etapa.get(etapa)
    
    def get_etapa_por_fecha(
        self,
        mes : int
    ) -> EtapaFenologica:
        """
        Obtiene la etapa fenologica del cultivo en base al mes.
        Esto es a modo general, se podría poner específico a cada cultivo
        """
        mapeo_etapas = {
            1 : EtapaFenologica.DORMANCIA,
            2 : EtapaFenologica.DORMANCIA,
            3 : EtapaFenologica.BROTANCIA,
            4 : EtapaFenologica.FLORACION,
            5: EtapaFenologica.CUAJADO,
            6: EtapaFenologica.ENGORDE,
            7: EtapaFenologica.ENGORDE,
            8: EtapaFenologica.MADURACION,
            9: EtapaFenologica.COSECHA,
            10: EtapaFenologica.COSECHA,
            11: EtapaFenologica.DORMANCIA,
            12: EtapaFenologica.DORMANCIA,
        }
        return mapeo_etapas.get(mes, EtapaFenologica.DORMANCIA)

# === Configuracion base de cada cultivo ===
# ==========================================
CONFIG_CULTIVOS = {
    # --- Frutales de hueso ---
    "almendro" : ConfiguracionCultivo(
        nombre = "Almendro",
        nombre_cientifico = "Prunus dulcis",
        umbrales_por_etapa = {
            EtapaFenologica.DORMANCIA : UmbralTemperatura(
                critico = -20.0,
                alto = -15.0,
                moderado = -5.0,
                bajo = 0.0
            ),
            EtapaFenologica.BROTANCIA : UmbralTemperatura(
                critico = -3.0,
                alto = 0.0,
                moderado = 5.0,
                bajo = 7.0
            ),
            EtapaFenologica.FLORACION : UmbralTemperatura(
                critico = -2.0,
                alto = 0.0,
                moderado = 10.0,
                bajo = 15.0
            ),
            EtapaFenologica.CUAJADO : UmbralTemperatura(
                critico = -3.0,
                alto = -1.0,
                moderado = 5.0,
                bajo = 10.0
            ),
            EtapaFenologica.ENGORDE : UmbralTemperatura(
                critico = -1.0,
                alto = 0.0,
                moderado = 5.0,
                bajo = 7.0
            ),
            EtapaFenologica.MADURACION : UmbralTemperatura(
                critico = 0.0,
                alto = 2.0,
                moderado = 20.0,
                bajo = 30.0
            ),
            EtapaFenologica.COSECHA : UmbralTemperatura(
                critico = 0.0,
                alto = 2.0,
                moderado = 20.0,
                bajo = 30.0
            )
        },
        descripcion = "Arbol frutal de hueso capaz de soportar temperaturas bajo cero en ciertas etapas fenologicas, tener cuidado con heladas o bajadas de temperatura en los meses Marzo - Abril"
    ),
    "cerezo" : ConfiguracionCultivo(
        nombre = "Cerezo",
        nombre_cientifico = "Prunus avium",
        umbrales_por_etapa = {
            EtapaFenologica.DORMANCIA : UmbralTemperatura(
                critico = -10.0,
                alto = -5.0,
                moderado = 3.0,
                bajo = 7.0
            ),
            EtapaFenologica.BROTANCIA : UmbralTemperatura(
                critico = -3.0,
                alto = 0.0,
                moderado = 5.0,
                bajo = 7.0
            ),
            EtapaFenologica.FLORACION : UmbralTemperatura(
                critico = 0.0,
                alto = 7.0,
                moderado = 15.0,
                bajo = 20.0
            ),
            EtapaFenologica.CUAJADO : UmbralTemperatura(
                critico = 0.0,
                alto = 7.0,
                moderado = 15.0,
                bajo = 20.0
            ),
            EtapaFenologica.ENGORDE : UmbralTemperatura(
                critico = 0.0,
                alto = 7.0,
                moderado = 15.0,
                bajo = 20.0
            ),
            EtapaFenologica.MADURACION : UmbralTemperatura(
                critico = 0.0,
                alto = 7.0,
                moderado = 15.0,
                bajo = 20.0
            ),
            EtapaFenologica.COSECHA : UmbralTemperatura(
                critico = 0.0,
                alto = 7.0,
                moderado = 15.0,
                bajo = 20.0
            )
        },
        descripcion = "Arbol frutal de hueso muy sensible en su etapa de floracion y cuajado a bajadas en picado de temperaturas"
    ),
    "melocotonero": ConfiguracionCultivo(
        nombre="Melocotonero",
        nombre_cientifico="Prunus persica",
        umbrales_por_etapa={
            EtapaFenologica.DORMANCIA: UmbralTemperatura(
                critico = -18.0, 
                alto = -12.0, 
                moderado = -8.0, 
                bajo = -4.0
            ),
            EtapaFenologica.BROTANCIA: UmbralTemperatura(
                critico = -3.5, 
                alto = -2.0, 
                moderado = -0.5, 
                bajo = 1.5
            ),
            EtapaFenologica.FLORACION: UmbralTemperatura(
                critico = -3.0, 
                alto = -2.0, 
                moderado = 5.0, 
                bajo = 18.0
            ),
            EtapaFenologica.CUAJADO: UmbralTemperatura(
                critico = -1.0, 
                alto = 5.0, 
                moderado = 10.0, 
                bajo = 20.0
            ),
            EtapaFenologica.ENGORDE: UmbralTemperatura(
                critico = -1.0, 
                alto = 5.0, 
                moderado = 10.0, 
                bajo = 20.0
            ),
            EtapaFenologica.MADURACION : UmbralTemperatura(
                critico = 0.0,
                alto = 7.0,
                moderado = 15.0,
                bajo = 20.0
            ),
            EtapaFenologica.COSECHA : UmbralTemperatura(
                critico = 0.0,
                alto = 7.0,
                moderado = 15.0,
                bajo = 20.0
            )
        },
        descripcion="Sensible en todas las etapas activas",
    ),
}

# === Funciones de Utilidad ===
# =============================
def get_cultivo(
    nombre_cultivo : str
) -> Optional[ConfiguracionCultivo]:
    """
    Obtiene la informacion de cultivo en funcion de su nombre
    
    :param nombre_cultivo: Nombre del cultivo solicitado
    :type nombre_cultivo: str
    :return: Posible información del cultivo si se encuentra registrado
    :rtype: ConfiguracionCultivo | None
    """
    return CONFIG_CULTIVOS.get(nombre_cultivo)

def listar_cultivo() -> list[str]:
    """
    Retorna la lista de cultivos disponibles
    
    :return: Lista de cultivos disponibles
    :rtype: list[str]
    """

    return list(CONFIG_CULTIVOS.keys())

def evaluar_riesgo_cultivo(
    nombre : str,
    temperatura : float,
    mes : int,
    etapa : Optional[EtapaFenologica] = None
) -> Dict:
    """
    Evalua el riesgo de heladas sobre el cultivo solicitado e informacion clave
    
    :param nombre: Nombre del cultivo
    :type nombre: str
    :param temperatura: Temperatura media a considerar
    :type temperatura: float
    :param mes: Mes del año que se quiere evaluar (1-12)
    :type mes: int
    :param etapa: Etapa fenologica del cultivo que se quiere evaluar, no es necesario si se indica el mes
    :type etapa: Optional[EtapaFenologica]
    :return: Diccionario con información importante evaluada
    :rtype: Dict
    """
    cultivo = get_cultivo(
        nombre_cultivo = nombre
    )

    if not cultivo:
        return {
            "error" : f"Cultivo {nombre} no encontrado",
            "cultivos_disponibles" : listar_cultivo()
        }

    if etapa:
        etapa_fenologica = etapa
    else:
        if mes:
            etapa_fenologica = cultivo.get_etapa_por_fecha(
                mes = mes
            )
            if not etapa_fenologica:
                return {
                    "error" : f"Has indicado un mes: {mes} que no existe",
                }
        else:
            raise ValueError("Si no se indica la etapa fenologica, al menos se debe indicar el mes del año que se quiere analizar")

    # Obtengo el umbral de temperatura por la etapa_fenologica
    umbral = cultivo.get_umbral(
        etapa = etapa_fenologica
    )
    if not umbral:
        return {
            "error" : f"No hay umbrales disponibles para {cultivo.nombre} para la etapa {etapa.value}"
        }
    
    # Clasifico la temperatura
    nivel_riesgo, descripcion = umbral.clasificar_temperatura(
        temp = temperatura
    )

    return {
        "cultivo" : cultivo.nombre,
        "nombre_cientifico" : cultivo.nombre_cientifico,
        "etapa_fenologica" : etapa_fenologica.value,
        "temperatura" : temperatura,
        "nivel_riesgo" : nivel_riesgo,
        "descripcion" : descripcion,
        "umbrales" : {
            "critico" : umbral.critico,
            "alto" : umbral.alto,
            "moderado" : umbral.moderado,
            "bajo" : umbral.bajo
        }
    }

def evaluar_riesgo_varios_cultivos(
    temperatura : float,
    mes : int,
    cultivos : list[str]
) -> list[Dict]:
    """
    Evalua el riesgo de heladas sobre cultivos solicitados e informacion clave
    
    :param temperatura: Temperatura media a considerar
    :type temperatura: float
    :param mes: Mes del año (1-12)
    :type mes: int
    :param cultivos: Lista de cultivos a analizar
    :type cultivos: list[str]
    :return: Lista con la información importante de cada cultivo en la lista pasada
    :rtype: list[Dict]
    """
    if cultivos is None:
        return {
            "error" : f"Cultivos no encontrados",
            "cultivos_disponibles" : listar_cultivo()
        }
    
    resultados_analisis = []
    for cultivo in cultivos:
        resultado = evaluar_riesgo_cultivo(
                nombre = cultivo,
                temperatura = temperatura,
                mes = mes
            )
        
        if "error" not in resultado:
            resultados_analisis.append(resultado)
    
    return resultados_analisis
