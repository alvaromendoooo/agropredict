package alvaro.riego.ITACyL.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;
import org.springframework.stereotype.Component;

@Data
@Component
public class ProductCalendarDTO {
    @JsonProperty("productId")
    // ID único del cultivo al que afecta
    private Integer productId;
    @JsonProperty("group")
    // Grupo de cultivo al que pertenece
    private String group;
    @JsonProperty("calendar")
    // Listado de semanas del año con su nivel de afectación de la plaga/enfermedad en el cultivo
    private CalendarDTO[] calendar;
}
