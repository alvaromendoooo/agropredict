import pika
import json


class RabbitMQPublisher():
    def create_publish(
        channel: pika.adapters.blocking_connection.BlockingChannel,
        queue_name: str,
        payload: str
    ):
        if hasattr(payload, "structured_content"):
            payload = payload.structured_content

        if not isinstance(payload, dict):
            raise TypeError(f"Payload no serializable: {type(payload)}")
        
        # Creación del publisher
        channel.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=json.dumps(payload, ensure_ascii = False).encode("utf-8"),
            properties=pika.BasicProperties(
                delivery_mode=2  # Mensaje persistente
            )
        )
        print(f"Mensaje enviado a la cola '{queue_name}'")