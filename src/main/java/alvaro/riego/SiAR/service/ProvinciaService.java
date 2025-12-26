package alvaro.riego.SiAR.service;

import alvaro.riego.SiAR.model.ProvinciaDTO;
import alvaro.riego.SiAR.model.SiAREstacionesInfoDTO;
import alvaro.riego.SiAR.utils.ApiResponse;
import alvaro.riego.SiAR.utils.BaseInfoTypeService;
import alvaro.riego.SiAR.utils.ResponseWrapper;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Optional;

@Service
public class ProvinciaService extends BaseInfoTypeService<ProvinciaDTO> {

    public ProvinciaService(RestTemplateBuilder restTemplateBuilder){
        super(restTemplateBuilder);
    }

    public ApiResponse<List<ProvinciaDTO>> obtenerInformacionProvincias(){
        return obtenerSiARInfo(getTypeReference(),"Info/Provincias", Optional.empty());
    }

    @Override
    protected String getSuccessMessage(){
        return "Información de provincias recogida";
    }

    @Override
    protected String getErrorMessage(){
        return "No se ha podido obtener la información de las provincias disponibles";
    }

    @Override
    protected ParameterizedTypeReference<ResponseWrapper<ProvinciaDTO>> getTypeReference(){
        return new ParameterizedTypeReference<ResponseWrapper<ProvinciaDTO>>() {};
    }
}
