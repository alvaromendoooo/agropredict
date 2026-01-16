# Obtiene los prompts del consumidor para generar la respuesta da la IA y la envía al broker
import logging
import asyncio
from fastmcp import Client
from mcp.types import PromptMessage, TextContent

import json

from external_communication.rabbitmq_config import RabbitMQConfig
from external_communication.rabbitmq_receive import RabbitMQConsumer

from ollama import chat
from ollama import ChatResponse

from dotenv import load_dotenv
from typing import List

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
        #parsed_response = json.loads(prompt[0].text)
        #print(f"Prompt recogido de MCP: {prompt}")
        
        #print(f"Mensajes del prompt: {prompt.messages}", flush = True)

        # Llamada al Agente AI y retorno de su respuesta
        logger.info("=== OBTENCIÓN RESPUESTA AGENTE AI ===")
        response = await obtener_respuesta_ia(prompt.messages)
        print(f"Respuesta de deepseek-r1: {response.message.content}")
        print("=== Validación y formateo de respuesta ===")
        result = await client.call_tool("procesar_respuesta_ia", {"respuesta_ia" : response.message.content})
        print(f"Resultado final: {result}")

        # Execute operations
        #result = await client.call_tool("add_numbers", {"num1": 2, "num2": 6})
        #parsed_response = json.loads(result[0].text)
        #print(parsed_response)

@staticmethod
async def process_with_official_client(text : str):
    
    prompt_a_usar = await client.get_prompt("clasificacion-climatica", {"texto" : text})

    return prompt_a_usar


@staticmethod
async def obtener_respuesta_ia(prompt_messages : List[PromptMessage]):

    # Convertir los PromptMessages al formato que chat() de ollama espera

    messages = []

    for message in prompt_messages:
        print(f"Message a decodificar: {message}")
        # Extraigo el contenido de TextContent, contiene la información embevida en formato json que tiene que usar la IA
        if isinstance (message.content, TextContent):
            content_str = str(message.content.text)
            print(f"==Texto extraido : {content_str}")
            # Parseo el json que está dentro del text
            try:
                message_dict = json.loads(content_str)

                # Creo el nuevo formato de mensaje con el contenido de message_dict
                message_ia = {
                    "role" : message_dict.get("role", message.role),
                    "content" : message_dict.get("content", "")
                }

                messages.append(message_ia)

            except json.JSONDecodeError : 
                # Si el JSON no es válido, uso el texto directamente
                message_ia = {
                    "role" : message.role,
                    "content" : content_str
                }

                messages.append(message_ia)

    # Llamo a la función chat() de ollama para aplicar al modelo los mensajes decodificados y obtener respuesta
    response : ChatResponse = chat(
        model = 'deepseek-r1', 
        messages = messages,
        think = True,
        logprobs = True
    )
    
    return response

if __name__ == "__main__":
    asyncio.run(main())