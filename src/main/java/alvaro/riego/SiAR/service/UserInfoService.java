package alvaro.riego.SiAR.service;

import alvaro.riego.SiAR.model.ProvinciaDTO;
import alvaro.riego.SiAR.model.SiARUserInfoDTO;
import alvaro.riego.SiAR.utils.ApiResponse;
import alvaro.riego.SiAR.utils.BaseInfoTypeService;
import alvaro.riego.SiAR.utils.ResponseWrapper;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.HttpServerErrorException;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.client.HttpClientErrorException;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

@Service
public class UserInfoService extends BaseInfoTypeService<SiARUserInfoDTO> {

    @Value("${app.api.key}")
    private String siar_api;

    @Value("${siar.api.base.url}")
    private String baseUrl;

    public UserInfoService(RestTemplateBuilder restTemplateBuilder){
        super(restTemplateBuilder);
    }

    /*
    * Obtener información de acceso sobre el usuario para la API
    * */
    public ApiResponse<List<SiARUserInfoDTO>> obtenerInformacionAcceso(){
        return obtenerSiARInfo(getTypeReference(), "Info/Accesos", Optional.empty());
    }

    /*
    * Verifica si quedan accesos disponibles
     */
    public ApiResponse<Map<String, Object>> verificarDisponibilidad(){
        try{
            ApiResponse<List<SiARUserInfoDTO>> accesoResponse = this.obtenerInformacionAcceso();

            if(!accesoResponse.isSuccess() || accesoResponse.getData() == null){
                return ApiResponse.error("No se pudo verificar la disponibilidad");
            }

            SiARUserInfoDTO userInfo = accesoResponse.getData().getFirst();

            if (userInfo.getRegistrosAcumuladosMinutos() == null ||
                    userInfo.getMaxRegistrosMinuto() == null ||
                    userInfo.getRegistrosAcumuladosDia() == 0 ||
                    userInfo.getMaxAccesosDia() == 0) {
                return ApiResponse.error("Datos incompletos en la respuesta del API SiAR");
            }

            Map<String, Object> disponibilidad = new HashMap<>();

            boolean hayAccesoMinuto = userInfo.getRegistrosAcumuladosMinutos() < userInfo.getMaxRegistrosMinuto();
            boolean hayAccesoDia = userInfo.getRegistrosAcumuladosDia() < userInfo.getMaxAccesosDia();

            boolean disponible = hayAccesoDia && hayAccesoMinuto;

            if ( disponible ){
                disponibilidad.put("accesos minuto actual",userInfo.getRegistrosAcumuladosMinutos());
                disponibilidad.put("max accesos minuto", userInfo.getMaxAccesosMinuto());
                disponibilidad.put("accesos dia actual", userInfo.getNumAccesosDiaActual());
                disponibilidad.put("max accesos dia", userInfo.getMaxAccesosDia());
                disponibilidad.put("registros acumulados minuto", userInfo.getRegistrosAcumuladosMinutos());
                disponibilidad.put("max registros minutos", userInfo.getMaxRegistrosMinuto());
                disponibilidad.put("registros acumulados dia", userInfo.getRegistrosAcumuladosDia());
                disponibilidad.put("max registros dia", userInfo.getMaxRegistrosDia());
            }

            String mensaje = disponible ? "Hay acceso disponible" : "Has agotado los accesos diarios o por minuto";

            return ApiResponse.success(mensaje, disponibilidad);

        } catch(Error e){
            return ApiResponse.error("Error al verificar la disponibilidad: " + e.getMessage());
        }
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
    protected ParameterizedTypeReference<ResponseWrapper<SiARUserInfoDTO>> getTypeReference(){
        return new ParameterizedTypeReference<ResponseWrapper<SiARUserInfoDTO>>() {};
    }


    public String getSiarApi(){
        return siar_api;
    }
}
