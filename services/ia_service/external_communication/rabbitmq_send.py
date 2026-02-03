from rabbitmq_amqp_python_client import (
    Message, 
    OutcomeState, 
    Connection, 
    Environment
)
from typing import List
import json


class RabbitMQPublisher():
    def create_publish(
        obj : tuple[Connection, Environment, List[str]], 
        payload : dict
    ):
        if hasattr(payload, "structured_content"):
            payload = payload.structured_content

        if not isinstance(payload, dict):
            raise TypeError(f"Payload no serializable: {type(payload)}")
        
        # Creación del publisher
        publisher = obj[0].publisher(obj[2][1])

        print(f"Nombre de la cola a enviar: {obj[2][1]}", flush=True)

        # Creamos el mensaje que vamos a enviar por la cola
        bytes_texto = json.dumps(payload).encode("utf-8")
        message = Message(body = bytes_texto)

        # Enviamos el mensaje y comprobamos su estado
        status = publisher.publish(message)

        # Control del estado del mensaje en la cola del broker
        match status.remote_state:
            case OutcomeState.ACCEPTED:
                print("Mensaje aceptado")
            case OutcomeState.REJECTED:
                print("Mensaje rechazado")
            case OutcomeState.RELEASED:
                print("Mensaje enviado")
        
        # Liberacion de memoria, cerrando el publisher
        publisher.close()