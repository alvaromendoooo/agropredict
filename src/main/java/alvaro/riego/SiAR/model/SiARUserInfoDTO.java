package alvaro.riego.SiAR.model;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;
import org.springframework.stereotype.Component;
@Data
@Component
public class SiARUserInfoDTO {

    @JsonProperty("NumAccesosMinutoActual")
    // Registro actual del numero de accesos realizados cada minuto
    private Integer numAccesosMinutoActual;
    @JsonProperty("MaxAccesosMinuto")
    // Registro del numero maximo de accesos por minuto
    private double maxAccesosMinuto;
    @JsonProperty("NumAccesosDiaActual")
    // Registro actual del numero de accesos realizados por dia
    private Integer numAccesosDiaActual;
    @JsonProperty("MaxAccesosDia")
    // Registro del numero máximo de accesos por dia
    private double maxAccesosDia;
    @JsonProperty("RegistrosAcumuladosMinutos")
    // Registro del numero de registros acumulados por minuto
    private Integer registrosAcumuladosMinutos;
    @JsonProperty("MaxRegistrosMinuto")
    // Registro del numero máximo de registros por minuto
    private Integer maxRegistrosMinuto;
    @JsonProperty("RegistrosAcumuladosDia")
    // Registro del numero de registros acumulados por dia
    private double registrosAcumuladosDia;
    @JsonProperty("MaxRegistrosDia")
    // Registro del numero maximo de registros acumulados por dia
    private double maxRegistrosDia;
}
