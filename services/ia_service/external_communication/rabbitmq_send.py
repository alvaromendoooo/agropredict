from rabbitmq_amqp_python_client import (
    Message, 
    OutcomeState, 
    Connection, 
    Environment
)
from typing import List
import pickle


class RabbitMQPublisher():
    def create_publish(
        obj : tuple[Connection, Environment, List[str]], 
        texto : str
    ):
        # Creación del publisher
        publisher = obj[0].publisher(obj[2][1])

        print(f"Nombre de la cola a enviar: {obj[2][1]}", flush=True)

        # Creamos el mensaje que vamos a enviar por la cola
        bytes_texto = pickle.dumps(texto) # Se envía un diccionario, no se puede usar encode, solo vale para string, se debe usar pickle para serializar todo tipo de objeto
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