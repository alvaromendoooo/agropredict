# rabbitmq_receive_pika.py
import pika
import json

class MessageHandler:
    """
    Handler para recibir mensajes de una cola con pika
    """
    def __init__(self):
        self.last_message = None
        self.message_received = False

    def callback(self, ch, method, properties, body):
        """
        Callback que pika llama cuando llega un mensaje
        """
        try:
            # Convertimos a string UTF-8
            if isinstance(body, (bytes, bytearray)):
                self.last_message = body.decode('utf-8')
            else:
                self.last_message = str(body)

            # ACK del mensaje (eliminamos de la cola)
            ch.basic_ack(delivery_tag=method.delivery_tag)

            self.message_received = True

            # Detenemos el consumo después del primer mensaje
            ch.stop_consuming()

        except Exception as e:
            # NACK y requeue si hay error
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            print(f"Error al procesar mensaje: {e}")

class RabbitMQConsumer:
    @staticmethod
    def receive_content(
        channel: pika.adapters.blocking_connection.BlockingChannel,
        queue_name: str
    ) -> str:
        """
        Recibe un mensaje de la cola y lo devuelve como string
        """
        handler = MessageHandler()

        # Registramos el callback en la cola
        channel.basic_consume(
            queue=queue_name,
            on_message_callback=handler.callback
        )

        # Arrancamos el loop de consumo (bloqueante)
        channel.start_consuming()

        return handler.last_message
