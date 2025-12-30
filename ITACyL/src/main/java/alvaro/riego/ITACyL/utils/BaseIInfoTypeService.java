package alvaro.riego.ITACyL.utils;

import alvaro.riego.ITACyL.model.ItemsDTO;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatusCode;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.HttpServerErrorException;
import org.springframework.web.client.RestTemplate;
import java.util.List;

import java.util.Arrays;

@Service
public abstract class BaseIInfoTypeService<T> {
    @Value("${app.api.key}")
    protected String itacyl_api;

    @Value("${itacyl.api.base.url}")
    protected String baseUrl;

    protected final RestTemplate restTemplate;

    public BaseIInfoTypeService(RestTemplateBuilder restTemplateBuilder) {
        this.restTemplate = restTemplateBuilder.build();
    }

    protected ApiResponse<List<T>> obtenerDatos (
            Integer crop,
            EnumParameter group
    ) {
        try {
            String urlCompleta = null;

            if (crop == null && group == null) {
                return ApiResponse.error("Se debe de incluir el valor de al menos 1 parámetro", HttpStatusCode.valueOf(404));
            } else if (crop == null) {
                urlCompleta = this.baseUrl + "?group=" + group;
            } else if (group == null) {
                urlCompleta = this.baseUrl + "?crop=" + crop;
            }

            ResponseEntity<List<T>> response = restTemplate.exchange(
                    urlCompleta,
                    HttpMethod.GET,
                    null,
                    new ParameterizedTypeReference<List<T>>() {}
            );

            if (response.getStatusCode().is2xxSuccessful()) {
                List<T> data = response.getBody();
                return ApiResponse.success(getSuccessMessage(), data);
            } else {
                return ApiResponse.error(getErrorMessage());
            }
        } catch (HttpClientErrorException e){
            return ApiResponse.error("Error de autenticación o de clave API", e.getStatusCode());
        } catch (HttpServerErrorException e){
            return ApiResponse.error("Error en el servidor de SiAR", e.getStatusCode());
        } catch (Exception e){
            return ApiResponse.error("Error de conexion: " + e.getMessage());
        }
    }
    protected abstract String getSuccessMessage();
    protected abstract String getErrorMessage();
}
