package alvaro.riego.SiAR.utils;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;
/*
 * CLASE: ResponseWrapper<T>
 *
 * PATRÓN: Data Transfer Object (DTO) genérico para estructura de respuesta SIAR
 * PROPÓSITO: Abstraction Layer para deserialización JSON → Objetos Java
 *
 * ARQUITECTURA:
 * ┌─────────────────────────────────────────────────────────────┐
 * │                    ResponseWrapper<T>                       │
 * │-------------------------------------------------------------│
 * │  - datos: List<T>              // Contenedor de entidades   │
 * │  - mensajeRespuesta: String    // Metadatos de respuesta    │
 * │-------------------------------------------------------------│
 * │  + getDatos(): List<T>                                      │
 * │  + setDatos(List<T>): void                                  │
 * │  + getMensajeRespuesta(): String                            │
 * │  + setMensajeRespuesta(String): void                        │
 * └─────────────────────────────────────────────────────────────┘
 *
 */
@JsonInclude(JsonInclude.Include.NON_NULL)
@JsonIgnoreProperties(ignoreUnknown = true) // Ignoramos campos que no nos interesan
public class ResponseWrapper<T> {
    @JsonProperty("Datos") // Mapeo del json al DTO
    // Lista de objectos T
    private List<T> datos;

    @JsonProperty("MensajeRespuesta")
    // Mensaje de respuesta
    private String mensajeRespuesta;

    public List<T> getDatos() {
        return datos;
    }

    public void setDatos(List<T> datos) {
        this.datos = datos;
    }

    public String getMensajeRespuesta() {
        return mensajeRespuesta;
    }

    public void setMensajeRespuesta(String mensajeRespuesta) {
        this.mensajeRespuesta = mensajeRespuesta;
    }
}
