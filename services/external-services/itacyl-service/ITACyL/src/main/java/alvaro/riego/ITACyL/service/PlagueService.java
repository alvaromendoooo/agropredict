package alvaro.riego.ITACyL.service;

import alvaro.riego.ITACyL.model.ItemsDTO;
import alvaro.riego.ITACyL.utils.ApiResponse;
import alvaro.riego.ITACyL.utils.BaseIInfoTypeService;
import alvaro.riego.ITACyL.utils.EnumParameter;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.stereotype.Service;
import java.util.List;

@Service
public class PlagueService extends BaseIInfoTypeService<ItemsDTO> {

    public PlagueService(RestTemplateBuilder restTemplateBuilder) { super(restTemplateBuilder);}

    public ApiResponse<List<ItemsDTO>> obtenerDatosPlagas (
            Integer crop,
            EnumParameter group
    ) {
        return obtenerDatos(crop, group);
    }

    @Override
    protected String getSuccessMessage() {
        return "Datos recuperados correctamente";
    }

    @Override
    protected String getErrorMessage() {
        return "Error al obtener datos";
    }
}
