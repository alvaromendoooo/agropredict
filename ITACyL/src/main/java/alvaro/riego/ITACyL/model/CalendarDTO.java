package alvaro.riego.ITACyL.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;
import org.springframework.stereotype.Component;

@Data
@Component
public class CalendarDTO {
    @JsonProperty("alertLevel")
    // Nivel de alerta de la plaga/enfermedad
    private Number alertLevel;
    @JsonProperty("week")
    // Número de semana del año
    private Integer week;
}
