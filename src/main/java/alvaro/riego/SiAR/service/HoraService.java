package alvaro.riego.SiAR.service;

import alvaro.riego.SiAR.model.DiaDTO;
import alvaro.riego.SiAR.model.HoraDTO;
import alvaro.riego.SiAR.utils.ApiResponse;
import alvaro.riego.SiAR.utils.BaseInfoTypeService;
import alvaro.riego.SiAR.utils.ResponseWrapper;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.stereotype.Service;
import java.util.*;

@Service
public class HoraService extends BaseInfoTypeService<HoraDTO> {
    public HoraService(RestTemplateBuilder restTemplateBuilder){
        super(restTemplateBuilder);
    }

    public ApiResponse<List<HoraDTO>> obtenerDatosHorariosProvincias (
            String provinciId,
            String fechaInicial,
            String fechaFinal,
            String fechaUltModificacion
    ){
        return obtenerData("Datos/Horarios/Provincia?", provinciId, fechaInicial, fechaFinal, fechaUltModificacion);
    }

    public ApiResponse<List<HoraDTO>> obtenerDatosHoratiosEstacion(
            String estacionId,
            String fechaInicial,
            String fechaFinal
    ){
        return obtenerData("Datos/Horarios/Estacion?", estacionId, fechaInicial, fechaFinal, null);
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
    protected ParameterizedTypeReference<ResponseWrapper<HoraDTO>> getTypeReference(){
        return new ParameterizedTypeReference<ResponseWrapper<HoraDTO>>() {};
    }
}
