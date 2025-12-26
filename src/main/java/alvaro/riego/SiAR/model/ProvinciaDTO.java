package alvaro.riego.SiAR.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;
import org.springframework.stereotype.Component;

@Data
@Component
public class ProvinciaDTO {
    @JsonProperty("Provincia")
    private String provincia;

    @JsonProperty("Codigo")
    private String codigo;

    @JsonProperty("Codigo_CCAA")
    private String codigo_ccaa;
}
