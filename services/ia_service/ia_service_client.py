# Obtiene los prompts del consumidor para generar la respuesta da la IA y la envía al broker
import logging
import asyncio
from fastmcp import Client as client_fastmcp
from mcp.types import PromptMessage, TextContent, CallToolResult

import json
import os

from external_communication.rabbitmq_config import RabbitMQConfig
from external_communication.rabbitmq_receive import RabbitMQConsumer
from external_communication.rabbitmq_send import RabbitMQPublisher
from external_communication.redis_cache import RedisCache

from ollama import Client
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

client = client_fastmcp(config)

ollama_client = Client(host = os.getenv('OLLAMA_HOST', 'http://localhost:11434'))
print("Cliente ollama creado", flush = True)

# Configuracion base de la caché Redis.
cache = RedisCache(
    host = os.getenv('REDIS_HOST'),
    port = os.getenv('REDIS_PORT'),
    password = os.getenv('REDIS_PASSWORD'),
    default_ttl = 3600
)

async def main():
    async with client:
        # Basic server interaction
        await client.ping()

        logger.info("========== RABBITMQ COMMUNICATION ==========")
        
        # Se deben establecer conexiones diferentes para trabajar con varias queue, no se puede reutilizar una misma conexion
        conexion_receptora = RabbitMQConfig.init_config()
        conexion_send = RabbitMQConfig.init_config()
        print("Conexion con el broker establecida", flush = True)
        
        message = RabbitMQConsumer.receive_content(conexion_receptora)
        print(f"Se ha recibido el texto de la cola aemet.raw: {message}")

        logger.info("===  VERIFICAR CACHE ===")
        cached_result = cache.obtener(message)

        if cached_result:
            print("Respuesta de la IA obtenida de Caché")
            result_structured = cached_result['resultado_procesado']

            RabbitMQPublisher.create_publish(conexion_send, result_structured)

            return
        
        else: # Si no se encuentra la respuesta de la IA guardada en caché
            # Obtención del prompt para enviarlo a la IA
            logger.info("=== OBTENCIÓN DEL PROMPT DESDE MCP ===")
            prompt = await process_with_official_client(message)

            # Llamada al Agente AI y retorno de su respuesta
            logger.info("=== OBTENCIÓN RESPUESTA AGENTE AI ===")
            response = await obtener_respuesta_ia(prompt.messages)
            response_ia = response.message.content
            print(f"Respuesta de deepseek-r1: {response_ia}")
            print("=== Validación y formateo de respuesta ===")
            result = await client.call_tool("procesar_respuesta_ia", {"respuesta_ia" : response.message.content})

            print(f"Resultado final: {result.structured_content}")

            cache.guardar(
                texto = message,
                respuesta_ia = response_ia,
                resultado_procesado = result.structured_content,
                ttl = 7200 # Lo almacenamos 2 horas
            )

            RabbitMQPublisher.create_publish(conexion_send, result)


@staticmethod
async def process_with_official_client(text : str):
    
    prompt_a_usar = await client.get_prompt(
        "clasificacion-climatica", 
        {"texto" : text}
    )

    return prompt_a_usar


@staticmethod
async def obtener_respuesta_ia(prompt_messages : List[PromptMessage]):

    # Convertir los PromptMessages al formato que chat() de ollama espera

    messages = []

    for message in prompt_messages:
        
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
    response : ChatResponse = ollama_client.chat(
        model = os.getenv('OLLAMA_MODEL'), 
        messages = messages,
        options = {
            'num_ctx': 4096, # Tamaño del contexto
            'temperature': 0.1, # Grado de precision para la respuests
            'num_predict': int(os.getenv('OLLAMA_NUM_PREDICT')),
            'top_k': 10,
            'top_p': 0.9,
            'repeat_penalty': 1.1,
            'num_thread': 8,
            'num_gpu': 1 if os.getenv('CUDA_VISIBLE_DEVICES') else 0
        },
        keep_alive='30m'  # Mantener 30 minutos en memoria
    )
    
    return response

if __name__ == "__main__":
    asyncio.run(main())