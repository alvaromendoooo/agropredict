# Obtiene los prompts del consumidor para generar la respuesta da la IA y la envía al broker
import logging
import os
import asyncio
from fastmcp import Client
import requests
import json

from external_communication.rabbitmq_config import RabbitMQConfig
from external_communication.rabbitmq_receive import RabbitMQConsumer

from ollama import chat
from ollama import ChatResponse

from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()

config = {
    "mcpServers": {
        "local_server": {
            "url": "http://localhost:9001/mcp"
        }
    }
}

client = Client(config)

async def main():
    async with client:
        # Basic server interaction
        await client.ping()

        # List available operations
        tools = await client.list_tools()

        for tool in tools:
            print(tool)

        prompts = await client.list_prompts()
        print("=== PROMPTS ===", flush = True)
        for prompt in prompts:
            print(prompt)

        logger.info("========== RABBITMQ COMMUNICATION ==========")
        
        conexion = RabbitMQConfig.init_config()
        print("Conexion con el broker establecida", flush = True)
        
        message = RabbitMQConsumer.receive_content(conexion)
        print(f"Se ha recibido el texto de la cola aemet.raw: {message}")

        # Obtención del prompt para enviarlo a la IA
        logger.info("=== OBTENCIÓN DEL PROMPT DESDE MCP ===")
        prompt = await process_with_official_client(message)
        parsed_response = json.loads(prompt[0].text)
        print(f"Prompt recogido de MCP: {parsed_response}")

        # Llamada al Agente AI y retorno de su respuesta
        logger.info("=== OBTENCIÓN RESPUESTA AGENTE AI ===")
        response = await obtener_respuesta_ia(prompt.messages)
        print(f"Respuesta de deepseek-r1: {response.message.content}")

        # Execute operations
        #result = await client.call_tool("add_numbers", {"num1": 2, "num2": 6})
        #parsed_response = json.loads(result[0].text)
        #print(parsed_response)

@staticmethod
async def process_with_official_client(text : str):
    
    prompt_a_usar = client.get_prompt("clasificacion-climatica", {"texto" : text})

    return prompt_a_usar


@staticmethod
async def obtener_respuesta_ia(prompt_messages):
    response : ChatResponse = chat(model = 'deepseek-r1', messages = prompt_messages)
    return response



"""class ClientAI():

    @staticmethod
    async def process_with_official_client(text : str):
        try:
            url = os.getenv("MCP_SERVER_URL", "http://127.0.0.1:9001/mcp")
            
            # Headers requeridos por el servidor MCP
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream"
            }
            
            # Inicializar sesión primero
            session_payload = {
                "jsonrpc": "2.0",
                "id": "init",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "ia-service-client",
                        "version": "1.0.0"
                    }
                }
            }
            
            response = requests.post(url, json=session_payload, headers=headers, timeout=30)
            init_result = response.json()
            logger.info(f"Sesión iniciada: {init_result}")
            
            # Obtener lista de prompts
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "prompts/list",
                "params": {}
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            result = response.json()
            
            logger.info(f"Prompts disponibles: {result}")
            
            # Obtener el prompt específico
            payload = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "prompts/get",
                "params": {
                    "name": "clasificacion-climatica",
                    "arguments": {"texto": text}
                }
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            result = response.json()
            print(f"Resultado: {result}", flush = True)
            
            if "error" in result:
                logger.error(f"Error del servidor MCP: {result['error']}")
                raise Exception(f"MCP Error: {result['error']}")
            
            # Simular la estructura del prompt para compatibilidad
            class MockPrompt:
                def __init__(self, messages):
                    self.messages = messages
            
            messages = result.get("result", {}).get("messages", [])
            print(f"Messages extraídos: {messages}", flush=True)
            return MockPrompt(messages)
                    
        except Exception as e:
            logger.error(f"Error en process_with_official_client: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
            
    @staticmethod
    async def obtener_respuesta_ia(prompt_messages):
        response : ChatResponse = chat(model = 'deepseek-r1', messages = prompt_messages)
        return response

    @staticmethod
    async def run():
        logger.info("========== RABBITMQ COMMUNICATION ==========")
        
        conexion = RabbitMQConfig.init_config()
        print("Conexion con el broker establecida", flush = True)
        
        message = RabbitMQConsumer.receive_content(conexion)
        print(f"Se ha recibido el texto de la cola aemet.raw: {message}")

        # Obtención del prompt para enviarlo a la IA
        logger.info("=== OBTENCIÓN DEL PROMPT DESDE MCP ===")
        prompt = await ClientAI.process_with_official_client(message)
        print(f"Prompt recogido de MCP: {prompt}")

        # Llamada al Agente AI y retorno de su respuesta
        logger.info("=== OBTENCIÓN RESPUESTA AGENTE AI ===")
        response = await ClientAI.obtener_respuesta_ia(prompt.messages)
        print(f"Respuesta de deepseek-r1: {response.message.content}")"""

if __name__ == "__main__":
    asyncio.run(main())