# Servicio de Prevención ante Riesgos Climáticos

Microservicio orientado a la detección y notificación temprana de riesgos climáticos que puedan afectar a explotaciones agrarias, especialmente riesgos de **heladas** y **plagas** asociadas a condiciones meteorológicas adversas.

El servicio consume datos procedentes de estaciones meteorológicas y sensores IoT proporcionados por el servicio `data-service`, integrando información en tiempo real para generar evaluaciones de riesgos.

## Objetivo
Permite al usuario consultar riesgos climáticos en función de:
* Provincia
* Localidad
* Comunidad Autónoma
* Nación

Las ubicaciones válidas son aqullas previamente registradas en la base de datos de la organización.

## Enfoque Predicción
El sistema no emplea modelos probabilísticos ni algoritmos de inteligencia artificial.  
Las predicciones se basan en:
* Datos meteorológicos actuales y previstos
* Umbrales técnicos definidos por el programador
* Información climática contrastada procedente de fuentes oficiales.

Las variedades principales utilizadas en el cálculo:
* Temperatura mínima y máxima.
* Humedad relevante.
* Presencia de niebla
* Condiciones atmosféricas relevantes

Debido a la disponibilidad limitada de datos por parte de las estaciones meteorológicas, el sistema solo genera predicciones para:
* El dia actual
* El dia siguiente
  
Extender la condición temporal reduciría la fiabilidad de la probabilidad.

## Prevención de Riesgo de Heladas
Uno de los factores críticos considerados es el cálculo de horas-frío acumuladas por variedad de cultivo.

Muchas variedades agrícolas requieren un número mínimo de horas dentro de un determinado rango térmico para completar correctamente su desarrollo fenológico. La acumulación insuficiente o excesiva puede generar vulnerabilidad frente a heladas.

El sistema:

1. Evalúa la temperatura media en los rangos definidos.

2. Calcula la acumulación de horas-frío.

3. Contrasta los valores con los umbrales configurados para cada variedad.

4. Determina el nivel de riesgo asociado.

La información necesaria para este cálculo es proporcionada por el `data-service`.

## Salida del Servicio
El microservicio genera:

* Nivel de riesgo (débil, moderado, alto, etc.)

* Alertas específicas

* Recomendaciones predefinidas para el agricultor

* Comentarios explicativos de la predicción

Además, el sistema mantiene un fichero de log con el historial de predicciones realizadas.
Este registro permite generar informes resumen internos que facilitan el seguimiento de eventos climáticos y la trazabilidad de decisiones.
