package alvaro.riego.SiAR.utils;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Component;
import org.springframework.stereotype.Service;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.HttpServerErrorException;
import org.springframework.web.client.RestTemplate;

import java.util.List;

@Component
public abstract class BaseInfoStringService<T> {
    @Value("${SIAR_API_KEY}")
    protected String siar_api;

    @Value("${siar.api.base.url}")
    protected String baseUrl;

    protected final RestTemplate restTemplate;

    public BaseInfoStringService(RestTemplateBuilder restTemplateBuilder){
        this.restTemplate = restTemplateBuilder.build();
    }

    protected ApiResponse<String> obtenerSiARInfo(String urlFilter){
        try {
            String apiUrl = baseUrl + "Info/" + urlFilter + "?ClaveAPI=" + siar_api;

             ResponseEntity<String> response = restTemplate.getForEntity(apiUrl, String.class);
             System.out.println("Respuesta REAL del SIAR:");
             System.out.println("Status: " + response.getStatusCode());
             System.out.println("Body: " + response.getBody());

            return ApiResponse.success("Info conseguida correctamente", response.getBody());

        } catch (HttpClientErrorException e){
            return ApiResponse.error("Error de autenticación o de clave API", e.getStatusCode());
        } catch (HttpServerErrorException e){
            return ApiResponse.error("Error en el servidor de SiAR", e.getStatusCode());
        } catch (Exception e){
            return ApiResponse.error("Error de conexion: " + e.getMessage());
        }
    }
}
