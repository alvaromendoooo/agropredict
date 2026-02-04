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
        params = pika.URLParameters(os.getenv('RABBITMQ_CONNECTION'))
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
