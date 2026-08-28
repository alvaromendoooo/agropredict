# DSL para definición de plagas y enfermedades

Sirva este documento como base técnica para comprender cómo se pueden realizar correctamente registros en el sistema Agro-Predict sobre plagas y 

enfermedades.

## Estructura base

```json
{
    /*Campos Obligatorios*/
    "public_id" : "string",
    "nombre" : "string",
    "agente_causante" : "string",
    "momento_critico" : "string",
    "tipo" : "string",
    "recursos" : ["string"],
    /*Recursos Opcionales*/
    "observaciones" : "string",
    "mas_info" : "string",
    "condiciones_evaluables" : [
        {"tipo" : "string", "valor" : float, "operador" : "string"},
    ],
    "ventana_temporal" : [
        {
            "modo" : "string",
            "dias_consecutivos_requeridos" : int,
            "temperatura_base" : int,
            "gdd_objetivo" : int,
            "dias_ventana" : int
            "nivel_si_cumple" : "string"
        }
    ],
    "algoritmo" : "str",
    "algoritmo_url" : "str",
}
```



## Campos de la estructura base

| NOMBRE                 | REQUERIDO | DESCRIPCION                                                                                                                                                          | Ejemplo                                                                                                                                                                |
|:----------------------:|:---------:|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------- |:----------------------------------------------------------------------------------------------------------------------------------------------------------------------:|
| public_id              | SÍ        | Identificador público con el que se registra la plaga o enfermedad en el sistema. Sigue el patrón `PLAGA-{CULTIVO}-{CODIGO}`.                                        | PLAGA-TOMATE-01                                                                                                                                                        |
| nombre                 | SÍ        | Nombre identificativo de la plaga a insertar.                                                                                                                        | Drosophila suzukii                                                                                                                                                     |
| agente_causante        | SÍ        | Descripción física de la plaga o enfermedad.                                                                                                                         | Mosca de alas manchadas de la familia DrosophilidaeNematodos formadores de agallas                                                                                     |
| momento_critico        | SÍ        | Descripción detallada de la estación del año donde se produce su prosperación. Adicionalmente se puede indicar valores específicos de condicionantes climáticos.     | Pre-cosecha con fruta sensible en el árbol y temperaturas medias entre 18-25°C con alta humedad relativa                                                               |
| observaciones          | NO        | Descripción de casuísticas específicas a tener en cuenta.                                                                                                            | Umbral térmico inferior de desarrollo estimado en 4.7°C. Requiere 934 grados-día para emergencia mediana. Máximo riesgo reproductivo con T media 18-25°C y HR > 70-80% |
| mas_info               | NO        | Enlace web para obtener más información sobre la plaga insertada.                                                                                                    | https://croplifela.org/es/plagas/listado-de-plagas/drosophila-suzukii-matsumura-mosca-de-las-alas-manchadas-una-plaga-cosmopolita-de-rapida-propagacion                |
| tipo                   | SÍ        | Clasificación taxonómica o genérica de la plaga o enfermedad. Ver tabla de valores válidos más abajo.                                                                | insecto                                                                                                                                                                |
| recursos               | SÍ        | Listado de variables climáticas requeridas para la predicción. Deben corresponderse con los nombres de la tabla de recursos disponibles. Mínimo 1 recurso.           | ["temperatura_media", "temperatura_max", "temperatura_min", "humedad_relativa"]                                                                                        |
| condiciones_evaluables | NO        | Condiciones que deben cumplirse en un día para elevar el riesgo a nivel preventivo. Cada condición referencia un recurso declarado. Mínimo 1 condición.              | [{ "tipo": "temperatura_media", "valor": 18, "operador": ">=" },{ "tipo": "humedad_relativa", "valor": 70, "operador": ">=" }],                                        |
| ventana_temporal       | NO        | Lista de ventanas temporales que definen condiciones acumulativas o consecutivas para elevar el riesgo a niveles superiores (normalmente crítico). Mínimo 1 ventana. | {"modo": "consecutivo", "dias_consecutivos_requeridos": 3, "nivel_si_cumple": "CRITICA"}                                                                               |
| algoritmo              | SÍ        | Indica el tipo de algoritmo que va a evaluar el nivel de riesgo para la plaga o enfermedad por el servicio predictor. Ver tabla de valores válidos más abajo.        | por_defecto                                                                                                                                                            |
| algoritmo_url          | NO        | Url de acceso sobre algoritmos **adhocs** para evaluar las predicciones. Si no se incluye la opción algorítmica `adhoc` se puede dejar vacío                         | http://host:puerto/path.dominio                                                                                                                                        |

## Valores válidos para campos enumerados

| CAMPO           | VALORES VÁLIDOS                                                     | NOTAS                                                                                                                                                     |
| --------------- | ------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| tipo            | acaro, nematodo, insecto, hongo,bacteria, virus, plaga, enfermedad. | Usar solo `plaga` o `enfermedad` si no se conoce el tipo específico.                                                                                      |
| operador        | >=, <=, <, >, !=, ==                                                | Aplicar en `condiciones_evaluables` y en `condiciones_evaluables_override`.                                                                               |
| modo            | consecutivo, acumulacion_gdd                                        | Define el tipo de evaluación temporal                                                                                                                     |
| nivel_si_cumple | PREVENTIVA, CRITICA                                                 | Nivel de alerta que se asigna al cumplirse condiciones de la ventana temporal o `condiciones_evaluables`.                                                 |
| algoritmo       | `por_defecto` o `adhoc`                                             | Si se indica el valor `adhoc` se debe proporcionar en el campo `algoritmo_url` la url donde se encuentra el algoritmo externo que evaluará la predicción. |





## Recursos disponibles

Con el objetivo de mantener una estructura más estable de predicción, los recursos asociados al campo requerido **recursos** para el registro de plagas o enfermedades debe contener el mismo formato de nombre de los indicados en la siguiente tabla.

| NOMBRE               | DESCRIPCION                                              |
| -------------------- | -------------------------------------------------------- |
| temperatura_aire     | Temperatura del aire ambiente (°C)                       |
| humedad_relativa     | Humedad relativa del aire (%)                            |
| precipitacion        | Precipitación acumulada (mm)                             |
| velocidad_viento     | Velocidad del viento (m/s)                               |
| direccion_viento     | Dirección del viento (°)                                 |
| radiacion_solar      | Radiación solar global (W/m²)                            |
| presion_atmosferica  | Presión atmosférica (hPa)                                |
| punto_rocio          | Temperatura de punto de rocío (°C)                       |
| evapotranspiracion   | Evapotranspiración de referencia ETo (mm/día)            |
| horas_frio           | Horas acumuladas por debajo de umbral térmico            |
| grados_dia           | Grados-día acumulados sobre umbral base                  |
| humedad_suelo        | Contenido volumétrico de agua en el suelo (%)            |
| temperatura_suelo    | Temperatura del suelo (°C)                               |
| ph_suelo             | pH del suelo                                             |
| humedad_hoja         | Humedad superficial de la hoja (mojadura foliar)         |
| ndvi                 | Índice de vegetación normalizado (salud del cultivo)     |
| compuestos_volatiles | COVs emitidos por la planta (detección precoz de plagas) |



## Campo `condiciones_evaluables`

Define las condiciones diarias que deben cumplirse para considerar que un día es de riesgo. Si se cumplen, el sistema asigna nivel **preventivo** por defecto.

| CAMPO    | REQUERIDO | TIPO   | DESCRIPCIÓN                                               |
| -------- | --------- | ------ | --------------------------------------------------------- |
| tipo     | SÍ        | string | Nombre del recursos climático.                            |
| valor    | SÍ        | float  | Valor umbral contral el que se compara.                   |
| operador | SÍ        | string | Operador de comprobación. Ver `tabla de valores válidos`. |



#### Ejemplo de uso

```json
"recursos": ["temperatura_media", "humedad_relativa", "temperatura_max"]
"condiciones_evaluables": [
    { "tipo": "temperatura_media", "valor": 18, "operador": ">=" },
    { "tipo": "humedad_relativa", "valor": 70, "operador": ">=" },
    { "tipo": "temperatura_max", "valor": 25, "operador": ">=", "tolerancia": 2 }
]
```



## Ventana Temporal

Los datos que se reflejan en la ventana temporal sirven para especificar condiciones **acumulativas** o **consecutivas** que se debe producir en el entorno climático para obtener un nivel de riesgo **critico** sobre la plaga o enfermedad a registrar.

Al depender algunas plagas de condiciones consecutivas y acumulativas, el campo **ventana_temporal** se ha configurado como lista para poder registrar estas dos casuísticas.

Actualmente, el algoritmo predictor solo soporta condiciones acumulativas de tipo **acumulacion_gdd**, a medida que se necesiten codificar más, se deberá incluir su lógica en el algoritmo interno del predictor.

##### Ejemplo de uso

```json
/*Primer ejemplo*/
"ventana_temporal" : [
    {
        "modo" : "consecutivo", // Indica periodicidad en el tiempo
        "dias_consecutivos_requeridos" : 3,
        "nivel_si_cumple" : "CRITICA"
    }
]
/*Segundo ejemplo*/
"ventana_temporal": [
    {
        "modo" : "acumulacion_gdd",
        "temperatura_base" : 4.7,
        "gdd_objetivo" : 834,
        "dias_ventana" : 28, // Indica el periodo de tiempo que se analizarán los datos para conseguir el objetivo final
        "nivel_si_cumple" : "CRITICA"
    }    
]
/*Tercer ejemplo*/
"ventana_temporal" : [
    {
        "modo" : "consecutivo", // Indica periodicidad en el tiempo
        "dias_consecutivos" : 3,
        "nivel_si_cumple" : "CRITICA"
    },
    {
        "modo" : "acumulacion_gdd",
        "temperatura_base" : 4.7,
        "gdd_objetivo" : 834,
        "dias_ventana" : 28, // Indica el periodo de tiempo que se analizarán los datos para conseguir el objetivo final
        "nivel_si_cumple" : "CRITICA"
    }   
]
```



#### Caso más específico de la ventana temporal

Debido a que en las condiciones acumulativas o consecutivas se pueden dar ocasiones en las que se especifiquen condiciones evaluables distintas a las definidas en el campo **condiciones_evaluables** y que se tengan que cumplir durante un periodo de tiempo, estas condiciones a definir en el campo **ventana_temporal** pueden incluir un campo **condiciones_evaluables_override** con una lista nueva de condiciones a evaluar. Su formato de definición es el mismo que el definido en el campo **condiciones_evaluables** en la tabla anterior.

##### Ejemplo

```json
"ventana_temporal": [
    {
      "modo": "consecutivo",
      "dias_consecutivos_requeridos": 3,
      "nivel_si_cumple": "PREVENTIVA"
    },
    {
      "modo": "consecutivo",
      "dias_consecutivos_requeridos": 3,
      "condiciones_evaluables_override": [
        { "tipo": "temperatura_media", "valor": 20, "operador": ">=" }
      ],
      "nivel_si_cumple": "CRITICA"
    }
  ]
```

## 

## Algoritmos ad-hocs

El servicio predictor de plagas cuenta con una característica internamente, dedicada al uso de algoritmos complementarios ad-hocs. De esta manera, se pueden evaluar condiciones complejas de las plagas mediante estos algoritmos especializados. Si el valor del campo `algoritmo` en el proceso de inserción de plagas en el sistema resulta tener el valor `por_defecto`, se utilizará en la evaluación el algoritmo genérico construido. Por otro lado, si se especifica el valor `adhoc` y su url en el campo `algoritmo_url`, se pasarán los datos requeridos en una petición HTTP POST al algoritmo ad-hoc.



La información que se le pasa a estos algoritmos externos como cuerpo de la petición son los siguientes:

```json
"plaga_id" : "string",
"fecha" : "YYYY-MM-DD",
"datos" : {
    "temperatura_aire" : float,
    "temperatura_media" : float,
    "temperatura_max" : float,
    "temperatura_min" : float,
    "temperatura_suelo" : float,
    "humedad_relativa" : float,
    "humedad_suelo" : float,
    "humedad_hoja" :  float,
}
```



Los resultados estructurados que deben devolver estos algoritmos tras realizar los calculos de procesamiento son los siguientes:

```json
{
    "mensaje" : "string" | null,
    "nivel_riesgo" : "string",
    "condiciones_cumplidas" : ["string",],
    "condiciones_pendientes" : ["string",],
    "recomendacion" : "string" | null
}
```



> Nota: El funcionamiento de algoritmos adhocs dependen de la información proporcionada en la creación de plagas o enfermedades, siguiendo la estructura de la plantilla DSL.



## Ejemplo completo de registro válido

```json
{
    "public_id": "PLAGA-CEREZO-01",
    "nombre": "Drosophila suzukii",
    "agente_causante": "Mosca de alas manchadas de la familia Drosophilidae",
    "momento_critico": "Pre-cosecha con fruta sensible en el árbol y temperaturas medias entre 18-25°C con alta humedad relativa",
    "observaciones": "Umbral térmico inferior de desarrollo estimado en 4.7°C. Requiere 934 grados-día para emergencia mediana. Máximo riesgo reproductivo con T media 18-25°C y HR > 70-80%",
    "mas_info": "https://croplifela.org/es/plagas/listado-de-plagas/drosophila-suzukii",
    "tipo": "insecto",
    "recursos": ["temperatura_media", "temperatura_max", "temperatura_min", "humedad_relativa"],
    "condiciones_evaluables": [
        { "tipo": "temperatura_media", "valor": 18, "operador": ">=" },
        { "tipo": "humedad_relativa", "valor": 70, "operador": ">=" }
    ],
    "ventana_temporal": [
        {
            "modo": "acumulacion_gdd",
            "temperatura_base": 4.7,
            "gdd_objetivo": 934,
            "dias_ventana": 365,
            "nivel_si_cumple": "PREVENTIVA"
        },
        {
            "modo": "consecutivo",
            "dias_consecutivos_requeridos": 3,
            "nivel_si_cumple": "CRITICA"
        }
    ],
    "algoritmo" : "por_defecto",
    "algoritmo_url" : null,
}
```


