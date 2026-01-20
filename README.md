# Servicio de consulta de Plagas y Enfermedades (ITACyL)

Este proyecto implementa un **servicio REST en Spring Boot** que actúa como intermediario entre una aplicación cliente y la **API pública de ITACyL (Sativum)** para la consulta del calendario de plagas y enfermedades asociadas a cultivos agrícolas.

El servicio permite filtrar los datos por **cultivo concreto** o por **grupo de cultivos**, facilitando su integración en sistemas de apoyo a la toma de decisiones en agricultura.

## Funcionalidad principal

- Consulta del calendario de plagas y enfermedades.
- Filtro por:
  - Código de cultivo (`crop`)
  - Grupo de cultivos (`group`)
- Consumo de API externa con **autenticación mediante API Key**.
- Manejo de errores y validación de parámetros de entrada.
- Respuesta estandarizada mediante un wrapper `ApiResponse`.

## Tecnologías Aplicadas

- **Java**
- **Spring Boot**
- **Spring Web (RestTemplate)**
- **OpenAPI / Swagger**
- **Maven**
- **API REST externa ITACyL (Sativum)**

## Autenticación

La API de ITACyL utiliza **API Key** enviada en el header HTTP

## Endpoints expuestos
### Obtener Calendario de Plagas y Enfermedades
| Parámetro | Tipo    | Obligatorio | Descripción |
|----------|---------|-------------|-------------|
| crop     | Integer | Opcional*   | Código del cultivo |
| group    | Enum    | Opcional*   | Grupo de cultivos (ej. CEREALES, LEGUMINOSAS) |

\* Es obligatorio indicar **al menos uno** de los dos parámetros.

### Ejemplo de uso
GET http://localhost:8087/plagas/itacyl/v1/Datos?crop=1&group=CEREALES
