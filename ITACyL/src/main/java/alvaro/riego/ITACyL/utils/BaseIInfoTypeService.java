package alvaro.riego.ITACyL.utils;

import alvaro.riego.ITACyL.model.ItemsDTO;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.HttpServerErrorException;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.util.UriComponentsBuilder;

import java.util.Collections;
import java.util.List;

import java.util.Arrays;
import java.util.Map;

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
            if (crop == null && group == null) {
                return ApiResponse.error(
                        "Se debe de incluir el valor de al menos 1 parámetro: 'crop' o 'group'",
                        HttpStatus.BAD_REQUEST  // Cambiado de 404 a 400
                );
            }

            // Construir URL correctamente
            UriComponentsBuilder builder = UriComponentsBuilder.fromHttpUrl(baseUrl);

            if (crop != null) {
                builder.queryParam("crop", crop);
            }

            if (group != null) {
                // Convertir Enum a String apropiado para la API
                String groupValue = convertGroupToString(group);
                builder.queryParam("group", groupValue);
            }

            String urlCompleta = builder.toUriString();

            // Creación de Headers
            HttpHeaders headers = new HttpHeaders();
            headers.set("apikey", itacyl_api); // para incluir el token
            headers.setContentType(MediaType.APPLICATION_JSON);
            headers.setAccept(Collections.singletonList(MediaType.APPLICATION_JSON));

            // Crear HTTPEntity con headers
            HttpEntity<String> entity = new HttpEntity<>(headers);

            ResponseEntity<List<T>> response = restTemplate.exchange(
                    urlCompleta,
                    HttpMethod.GET,
                    entity,
                    new ParameterizedTypeReference<List<T>>() {}
            );
            System.out.println("Response: " + response);
            if (response.getStatusCode().is2xxSuccessful()) {
                List<T> data = response.getBody();
                return ApiResponse.success(getSuccessMessage(), data);
            } else {
                return ApiResponse.error(getErrorMessage(), response.getStatusCode());
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

    private String convertGroupToString(EnumParameter group) {
        if (group == null) return null;

        return group.name();
    }
}
