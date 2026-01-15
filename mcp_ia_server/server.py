from fastmcp import FastMCP

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
    Extrae los siguientes datos en JSON del siguiente texto:

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