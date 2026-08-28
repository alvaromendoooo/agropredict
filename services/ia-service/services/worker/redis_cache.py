import logging
from typing import Optional, Any
from datetime import timedelta
import redis
import hashlib
import json

logger = logging.getLogger(__name__)

class RedisCache:
    """
    Gestor de caches para respuestas de la IA
    """

    def __init__(
        self,
        host : str = '127.0.0.1',
        port : int = 6379,
        password : Optional[str] = None,
        default_ttl : int = 3600
    ):
        """
        Inicialización de configuración Redis
        
        :param host: Host de Redis
        :type host: string
        :param port: Puerto de Redis
        :type port: int
        :param password: Contraseña para acceder a Redis
        :type password: Optional[str]
        :param default_ttl: Tiempo de vida por defecto en segundos (1h)
        :type default_ttl: int
        """

        self.redis_client = redis.Redis(
            host=host,
            port=port,
            db=0,
            password=password,
            decode_responses=True,
            socket_connect_timeout=5
        )

        self.default_ttl = default_ttl

        # Verificacion de conexion exitosa con Redis
        try:
            self.redis_client.ping()
            logger.info("=== Conexión con Redis establecida ===")
        except redis.ConnectionError as e:
            logger.error("Ha surgido un problema al conectar la base de datos Redis: {e}")
            raise
            
    def _generar_clave(
        self,
        texto: str,
        prefijo : str = "ia_cache"
    ) -> str:
        """
        Genera una clave hash unica basada en el texto
        
        :param texto: Texto que recibe de data-service
        :type texto: str
        :param prefijo: Prefijo para la clave
        :type prefijo: str
        :return: Clave hash única
        :rtype: str
        """

        # Normalizar el texto
        texto_normalizado = ' '.join(texto.lower().split())

        # Generar hash SHA256
        hash_obj = hashlib.sha256(texto_normalizado.encode('utf-8'))
        hash_hex = hash_obj.hexdigest()

        return f"{prefijo}:{hash_hex}"
    
    def obtener(
        self,
        texto : str
    ) -> Optional[dict]:
        """
        Obtiene respuesta cacheada si existe
        
        :param texto: Texto que recibo de data-service
        :type texto: str
        :return: Contenido de la clave cacheada, si existe
        :rtype: dict | None
        """

        # Genero la clave del texto recibido
        clave = self._generar_clave(texto = texto)

        try:
            valor = self.redis_client.get(clave)
            if valor:
                logger.info("=== Se ha recuperado correctamente el valor del texto cacheado ===")
                return json.loads(valor)
            else:
                logger.info("=== No existen datos cacheados para el texto recibido ===")
                return None
        except (redis.RedisError, json.JSONDecodeError) as e:
            logger.error(f"Error al obtener datos de caché: {e}")
            return None
        
    def guardar(
        self,
        texto : str,
        respuesta_ia : str,
        resultado_procesado : Any,
        ttl : Optional[int] = None
    ) -> bool:
        """
        Guarda una respuesta en caché
        
        :param texto: Texto que recibo de data-service
        :type texto: str
        :param respuesta_ia: Respuesta cruda de la IA
        :type respuesta_ia: str
        :param resultado_procesado: Respuesta procesada por la tool de mcp server
        :type resultado_procesado: Any
        :param ttl: Tiempo de vida
        :type ttl: Optional[int]
        :return: Se ha guardado o no
        :rtype: bool
        """

        clave = self._generar_clave(texto)
        tiempo_vida = ttl or self.default_ttl

        datos = {
            "texto_original" : texto,
            "respuesta_ia" : respuesta_ia,
            "resultado_procesado" : resultado_procesado
        }

        try:
            self.redis_client.setex(
                name = clave,
                time = timedelta(seconds = tiempo_vida),
                value = json.dumps(datos, ensure_ascii = True)
            )
            logger.info("=== Se han almacenado los datos correctamente ===")
            return True
        except redis.RedisError as e:
            logger.error("Ha ocurrido un error al guardar en Redis: {e}")
            return False
        
    def limpiar_todo(
        self
    ) -> bool:
        """
        Limpia todo lo que tenga almacenado Redis en caché
        """
        try:
            self.redis_client.flushdb()
            logger.warning("Se ha limpiado todo el caché")
            return True
        except redis.RedisError as e:
            logger.error("Ha surgido un problema limpiando todo el caché")
            return False
