package alvaro.riego.SiAR.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;
import org.springframework.stereotype.Component;

@Data
@Component
public class SiAREstacionesInfoDTO {

    @JsonProperty("Estacion")
    private String estacion;

    @JsonProperty("Codigo")
    private String codigo;

    @JsonProperty("Termino")
    private String termino;

    @JsonProperty("Longitud")
    private String longitud;

    @JsonProperty("Latitud")
    private String latitud;

    @JsonProperty("Altitud")
    private Integer altitud;

    @JsonProperty("XUTM")
    private Double xutm;

    @JsonProperty("YUTM")
    private Double yutm;

    @JsonProperty("Huso")
    private Integer huso;

    @JsonProperty("Fecha_Instalacion")
    private String fechaInstalacion;

    @JsonProperty("Fecha_Baja")
    private String fechaBaja;
}
