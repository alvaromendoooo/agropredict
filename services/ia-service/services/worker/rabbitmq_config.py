# rabbitmq_config_pika.py
from dotenv import load_dotenv
import pika
import os

load_dotenv()

class RabbitMQConfig:
    @staticmethod
    def init_config():
        """
        Inicializa la conexión y devuelve:
        - connection: pika.BlockingConnection
        - channel: pika.Channel
        - queues: dict con las colas
        """

        # Configuración de credenciales sobre el broker
        credentials = pika.PlainCredentials(
            username = os.getenv('RABBITMQ_USER'),
            password = os.getenv('RABBITMQ_PASS'),
            erase_on_connect = False
        )

        params = pika.ConnectionParameters(
            host = os.getenv('RABBITMQ_HOST'),
            port = 5672,
            credentials = credentials,
            heartbeat = 60,
            blocked_connection_timeout = 300
        )

        connection = pika.BlockingConnection(params)
        channel = connection.channel()

        # Declaro las colas para asegurar que existen
        queue_raw = os.getenv('QUEUE_IN_NAME')
        queue_processed = os.getenv('QUEUE_OUT_NAME')

        channel.queue_declare(queue=queue_raw, durable=True)
        channel.queue_declare(queue=queue_processed, durable=True)

        queues = {
            "raw": queue_raw,
            "processed": queue_processed
        }

        return connection, channel, queues
