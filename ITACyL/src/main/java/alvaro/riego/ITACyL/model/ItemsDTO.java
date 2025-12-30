package alvaro.riego.ITACyL.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;
import org.springframework.stereotype.Component;

@Data
@Component
public class ItemsDTO {
    @JsonProperty("id")
    // Id único de la plaga/enfermedad
    private Integer id;
    @JsonProperty("name")
    // Nombre de la plaga/enfermedad
    private String name;
    @JsonProperty("causalAgent")
    // Agente causante de la plaga/enfermedad
    private String causalAgent;
    @JsonProperty("criticalMoment")
    // Momento crítico de aparición de la plaga/enfermedad
    private String criticalMoment;
    @JsonProperty("observations")
    // Observaciones
    private String observations;
    @JsonProperty("link")
    // Enlace a informacion más detallada sobre la plaga/enfermedad
    private String link;
    @JsonProperty("type")
    // Indica si es plaga o enfermedad
    private String type;
    @JsonProperty("productCalendar")
    // Calendario de afectación de la plaga/enfermedad en el cultivo seleccionado
    private ProductCalendarDTO[] productCalendar;
}
