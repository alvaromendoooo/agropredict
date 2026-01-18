from fastmcp import FastMCP
from ollama import ChatResponse
from typing import Dict, Optional, Any
import json

def main():
    # CONFIGURACIÓN DEL SERVIDOR #

    ## Intancia del servidor FastMCP
    mcp = FastMCP(
        name="Agro-Predict's MCP Server",
    )

    print("Objeto del servidor creado.")

    # HERRAMIENTAS

    ## Las herramientas son funciones expuestas al cliente


    ## Herramientas para obtener datos del data-service
    @mcp.tool()
    def obtener_texto(texto : str):
        """
        Recibe un texto de AEMET y lo encapsula
        """
        return {"texto" : texto}

    ## Herramienta para validar la respuesta de la IA
    @mcp.tool()
    def procesar_respuesta_ia(respuesta_ia: str) -> Dict[str, Any]:
        """
        Procesa y valida la respuesta JSON de la IA
        
        Args:
            respuesta_ia: Respuesta de la IA como string (puede contener JSON o markdown)
        
        Returns:
            Diccionario con los datos climáticos procesados
        """
        if not respuesta_ia:
            return {"error": "Respuesta vacía", "procesado": False}
        
        # Limpiar la respuesta
        respuesta_limpia = respuesta_ia.strip()
        
        # Eliminar bloques de código markdown
        if respuesta_limpia.startswith('```json'):
            respuesta_limpia = respuesta_limpia[7:].strip()
        if respuesta_limpia.startswith('```'):
            respuesta_limpia = respuesta_limpia[3:].strip()
        if respuesta_limpia.endswith('```'):
            respuesta_limpia = respuesta_limpia[:-3].strip()
        
        try:
            # Parsear JSON
            respuesta_json = json.loads(respuesta_limpia)
            
            if not isinstance(respuesta_json, dict):
                return {
                    "error": "La respuesta no es un objeto JSON válido",
                    "contenido": str(respuesta_json)[:200],
                    "procesado": False
                }
            
            # Lista de campos requeridos
            campos_requeridos = [
                "estado_del_cielo",
                "aparicion_de_nieblas",
                "tendencia_de_temperaturas_maximas",
                "tendencias_de_temperaturas_minimas",
                "tendencias_de_temperatura_general",
                "rachas_de_viento",
                "precipitaciones",
                "existencias_de_heladas",
                "zonas_de_heladas",
                "cotas_de_nieve"
            ]
            
            # Asegurar que todos los campos existan
            resultado = {}
            for campo in campos_requeridos:
                # Intentar con diferentes nombres de campo
                if campo in respuesta_json:
                    resultado[campo] = respuesta_json[campo]
                else:
                    # Buscar variaciones del nombre
                    campo_sin_guiones = campo.replace('_', ' ')
                    if campo_sin_guiones in respuesta_json:
                        resultado[campo] = respuesta_json[campo_sin_guiones]
                    else:
                        resultado[campo] = None
            
            resultado["procesado"] = True
            resultado["valido"] = True
            
            return resultado
            
        except json.JSONDecodeError as e:
            return {
                "error": f"Error decodificando JSON: {str(e)}",
                "respuesta_original": respuesta_ia[:500],
                "procesado": False
            }
        except Exception as e:
            return {
                "error": f"Error inesperado: {str(e)}",
                "procesado": False
            }

    # PATRONES DE INTERACCION REUTILIZABLES
    @mcp.prompt("clasificacion-climatica")
    async def clasificacion_prompt(texto : str):
        """
        Genera un prompt para obtener datos necesarios para data-service, 
        sobre los textos que AEMET genera.
        """
        return [
            {"role" : "system", "content" : "Eres un clasificador de datos climáticos"},
            {"role": "user", "content": f"""
    Extrae SOLO los siguientes datos en formato JSON del texto proporcionado.
    Response únicamente con el JSON, sin explicaciones ni texto adicional.
             
    Campos requeridos:
    - estado del cielo
    - aparicion de nieblas
    - tendencia de temperaturas máximas
    - tendencias de temperaturas mínimas
    - tendencias de temperatura general
    - rachas de viento
    - precipitaciones
    - existencias de heladas
    - zonas de heladas
    - cotas de nieve

    Si alguno de los datos relacioandos a estos campos no se mencionan, usa null.
    Para el campo rachas de viento, me gustaría que almacenases también, las zonas en las que se produce si se especifica en el texto.
        
    TEXTO:
    {texto}
    """}
        ]

    print("Prompt 'clasificacion-climatica' agregado.")

    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=9001,
        log_level="DEBUG"
    )

if __name__ == '__main__':
    main()