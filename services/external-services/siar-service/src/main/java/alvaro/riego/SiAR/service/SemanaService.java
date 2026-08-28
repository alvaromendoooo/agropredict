package alvaro.riego.SiAR.service;

import alvaro.riego.SiAR.model.HoraDTO;
import alvaro.riego.SiAR.model.SemanaDTO;
import alvaro.riego.SiAR.utils.ApiResponse;
import alvaro.riego.SiAR.utils.BaseInfoTypeService;
import alvaro.riego.SiAR.utils.ResponseWrapper;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class SemanaService extends BaseInfoTypeService<SemanaDTO> {
    public SemanaService(RestTemplateBuilder restTemplateBuilder){
        super(restTemplateBuilder);
    }

    public ApiResponse<List<SemanaDTO>> obtenerDatosSemanalesProvincias(
            String provinciaId,
            String fechaInicial,
            String fechaFinal,
            String fechaUltModificacion,
            String datosCalculados
    ){
        return obtenerData("Datos/Semanales/PROVINCIA?", provinciaId, fechaInicial, fechaFinal, datosCalculados);
    }

    public ApiResponse<List<SemanaDTO>> obtenerDatosSemanalesEstacion(
        String estacionId,
        String fechaInicial,
        String fechaFinal,
        String datosCalculados
    ){
        return obtenerData("Datos/Semanales/ESTACION?", estacionId, fechaInicial, fechaFinal, datosCalculados);
    }

    @Override
    protected String getSuccessMessage() {
        return "Datos recurperados correctamente";
    }

    @Override
    protected String getErrorMessage() {
        return "No se han recuperado datos";
    }

    @Override
    protected ParameterizedTypeReference<ResponseWrapper<SemanaDTO>> getTypeReference(){
        return new ParameterizedTypeReference<ResponseWrapper<SemanaDTO>>() {};
    }
}
