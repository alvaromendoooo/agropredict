package alvaro.riego.SiAR.service;

import alvaro.riego.SiAR.model.SiAREstacionesInfoDTO;
import alvaro.riego.SiAR.utils.BaseInfoTypeService;
import alvaro.riego.SiAR.utils.ResponseWrapper;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.stereotype.Service;
import alvaro.riego.SiAR.utils.ApiResponse;
import java.util.List;
import java.util.Optional;

@Service
public class EstacionesInfoService extends BaseInfoTypeService<SiAREstacionesInfoDTO> {

    public EstacionesInfoService(RestTemplateBuilder restTemplateBuilder){
        super(restTemplateBuilder);
    }

    public ApiResponse<List<SiAREstacionesInfoDTO>> obtenerInformacionEstaciones(){
        return obtenerSiARInfo(getTypeReference(), "Info/ESTACIONES", Optional.empty());
    }

    @Override
    protected String getSuccessMessage(){
        return "Información de estaciones recogida";
    }

    @Override
    protected String getErrorMessage(){
        return "No se ha podido obtener la información de las estaciones disponibles";
    }

    @Override
    protected ParameterizedTypeReference<ResponseWrapper<SiAREstacionesInfoDTO>> getTypeReference(){
        return new ParameterizedTypeReference<ResponseWrapper<SiAREstacionesInfoDTO>>() {};
    }
}
