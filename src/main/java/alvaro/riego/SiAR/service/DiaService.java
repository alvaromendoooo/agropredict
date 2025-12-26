package alvaro.riego.SiAR.service;


import alvaro.riego.SiAR.model.DiaDTO;
import alvaro.riego.SiAR.model.SiAREstacionesInfoDTO;
import alvaro.riego.SiAR.utils.ApiResponse;
import alvaro.riego.SiAR.utils.BaseInfoTypeService;
import alvaro.riego.SiAR.utils.ResponseWrapper;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

@Service
public class DiaService extends BaseInfoTypeService<DiaDTO> {

    public DiaService(RestTemplateBuilder restTemplateBuilder){
        super(restTemplateBuilder);
    }

    public ApiResponse<List<DiaDTO>> obtenerDatosDiaProvincia (
            String provinciaId,
            String fechaInicial,
            String fechaFinal,
            String fechaUltModificacion
    ){

        return obtenerData("Datos/Diarios/Provincia?", provinciaId, fechaInicial, fechaFinal, fechaUltModificacion);
    }


    public ApiResponse<List<DiaDTO>> obtenerDatosDiaEstacion (
            String estacionId,
            String fechaInicial,
            String fechaFinal
    ) {

        return obtenerData("Datos/Diarios/Estacion?", estacionId, fechaInicial, fechaFinal);
    }

    @Override
    protected String getSuccessMessage() {
        return "Datos recuperados correctamente";
    }

    @Override
    protected String getErrorMessage(){
        return "No se han recuperado los datos";
    }

    @Override
    protected ParameterizedTypeReference<ResponseWrapper<DiaDTO>> getTypeReference(){
        return new ParameterizedTypeReference<ResponseWrapper<DiaDTO>>() {};
    }
}
