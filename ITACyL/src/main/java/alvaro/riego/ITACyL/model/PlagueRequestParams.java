package alvaro.riego.ITACyL.model;

import alvaro.riego.ITACyL.utils.AtLeastOneNotNull;
import alvaro.riego.ITACyL.utils.EnumParameter;
import lombok.Data;

@Data
@AtLeastOneNotNull(fieldNames = {"crop", "group"},
        message = "Se debe proporcionar al menos uno de los parámetros: 'crop' o 'group'")
public class PlagueRequestParams {
    private Integer crop;
    private EnumParameter group;

    public Integer getCrop(){
        return crop;
    }

    public EnumParameter getGroup() {
        return group;
    }
}
