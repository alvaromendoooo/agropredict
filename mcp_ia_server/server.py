from fastmcp import FastMCP
from ollama import ChatResponse
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
    @mcp.tool("procesar_respuesta_ia")
    def procesar_respuesta_ia(respuesta_ia : ChatResponse):
        """
        Procesa y valida la respuesta JSON de la IA
        """

        if not respuesta_ia:
            return None
        
        # Extraer solo el JSON de la respuesta porque viene en formato markdown
        respuesta_limpia = respuesta_ia.message.content.strip()

        # Elimino sentencias de codigo de formato markdown
        if respuesta_limpia.startswith('```json'):
            respuesta_limpia = respuesta_limpia[7:-3].strip()
        elif respuesta_limpia.startswith('```'):
            respuesta_limpia = respuesta_limpia[3:-3].strip()
        
        try:

            respuesta_json = json.loads(respuesta_limpia)

            comprobar_campos = [
                "estado_del_cielo",
                "aparicion_de_nieblas"
                "tendencia_de_temperaturas_maximas"
                "tendencias_de_temperaturas_minimas"
                "tendencias_de_temperatura_general",
                "rachas_de_viento",
                "precipitaciones",
                "existencias_de_heladas",
                "zonas_de_heladas"
                "cotas_de_nieve"
            ]

            # Verificar que el json de la respuesta contiene los campos de comprobar_campos
            for campo in comprobar_campos:
                if campo not in respuesta_json:
                    respuesta_json[campo] = None

            return respuesta_json
        
        except json.JSONDecodeError as e:
            print("Error decodificando el json de la respuesta IA: {e}")
            return None

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
        host="127.0.0.1",
        port=9001,
        log_level="DEBUG"
    )

if __name__ == '__main__':
    main()