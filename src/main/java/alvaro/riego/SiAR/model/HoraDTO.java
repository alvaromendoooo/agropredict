package alvaro.riego.SiAR.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;
import org.springframework.stereotype.Component;

import java.util.Date;

@Data
@Component
public class HoraDTO {
    @JsonProperty("HoraMin")
    private Short horaMin;

    @JsonProperty("TempMedia")
    private Float tempMedia;

    @JsonProperty("HumedadMedia")
    private Float humedadMedia;

    @JsonProperty("VelViento")
    private Float velViento;

    @JsonProperty("DirViento")
    private Float dirViento;

    @JsonProperty("Radiacion")
    private Float radiacion;

    @JsonProperty("Precipitacion")
    private Float precipitacion;

    @JsonProperty("TempSuelo1")
    private Float tempSuelo1;

    @JsonProperty("Estacion")
    private String estacion;

    @JsonProperty("Fecha")
    private Date fecha;
}
