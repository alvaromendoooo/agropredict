package alvaro.riego.SiAR.utils;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.HttpServerErrorException;
import org.springframework.web.client.RestTemplate;

import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

/*
 * CLASE: BaseInfoTypeService<T>
 *
 * PATRÓN: Service genérico para los tipos de dato T
 * PROPÓSITO: Esqueleto para procesamiento de datos en Service
 *
 * ARQUITECTURA:
 * ┌─────────────────────────────────────────────────────────────┐
 * │                    BaseInfoTypeService<T>                   │
 * │-------------------------------------------------------------│
 * │  - siar_api: String              // API de SIAR             │
 * │  - baseUrl: String    // Url común para solicitar datos     │
 * │-------------------------------------------------------------│
 * │  + obtenerSiARInfo(ParameterizedTypeReference<ResponseWrapper<T>> typeRef, String urlFilter): ApiResponse<List<T>>
 * │  + getErrorMessage(): String                                │
 * │  + getTypeReference(): ParameterizedTypeReference<ResponseWrapper<T>│
 * └─────────────────────────────────────────────────────────────┘
 *
 */
@Service
public abstract class BaseInfoTypeService<T> {
    @Value("${SIAR_API_KEY}")
    protected String siar_api;

    @Value("${siar.api.base.url}")
    protected String baseUrl;

    protected final RestTemplate restTemplate;

    public BaseInfoTypeService(RestTemplateBuilder restTemplateBuilder){
        this.restTemplate = restTemplateBuilder.build();
    }

    protected ApiResponse<List<T>> obtenerSiARInfo(
            ParameterizedTypeReference<ResponseWrapper<T>> typeRef,
            String urlFilter,
            Optional<Map<String, String>> parametros){

        try{
            String urlCompleta;
            String baseUrlSinParametros = this.baseUrl + urlFilter;

            if(parametros.isEmpty()){ // Caso en el que buscamos info de usuario privada
                urlCompleta = this.baseUrl + urlFilter + "?ClaveAPI=" + siar_api;
            } else { // Caso en el que buscamos info publica
                urlCompleta = this.crearFiltrosAnidados(baseUrlSinParametros, parametros);
            }
            System.out.println("======URL COMPLETA=======");
            System.out.println(urlCompleta);
            System.out.println("=========================");

            // DEBUG 1: Verificar que la URL es accesible
            System.out.println("=== PRUEBA CONEXIÓN BÁSICA ===");
            try {
                ResponseEntity<String> testResponse = restTemplate.getForEntity(urlCompleta, String.class);
                System.out.println("Status: " + testResponse.getStatusCode());
                System.out.println("Body: " + testResponse.getBody());
            } catch (HttpClientErrorException e) {
                System.out.println("Error Cliente: " + e.getStatusCode() + " - " + e.getResponseBodyAsString());
                return ApiResponse.error("Error SIAR: " + e.getStatusCode() + " - " + e.getResponseBodyAsString());
            } catch (HttpServerErrorException e) {
                System.out.println("Error Servidor: " + e.getStatusCode() + " - " + e.getResponseBodyAsString());
                return ApiResponse.error("Error servidor SIAR: " + e.getStatusCode());
            } catch (Exception e) {
                System.out.println("Error general: " + e.getClass().getSimpleName() + " - " + e.getMessage());
                e.printStackTrace();
                return ApiResponse.error("Error conexión: " + e.getMessage());
            }

            ResponseEntity<ResponseWrapper<T>> response = restTemplate.exchange(urlCompleta, HttpMethod.GET, null, typeRef);

            if (response.getStatusCode().is2xxSuccessful()){
                List<T> data = response.getBody().getDatos();
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

    private String crearFiltrosAnidados(String baseUrl, Optional<Map<String, String>>parametros){

        StringBuilder urlBuilder = new StringBuilder(baseUrl);
        urlBuilder.append("ClaveAPI=").append(siar_api).append("&");

        boolean primerParam = true;
        if (parametros != null && !parametros.isEmpty()) {
            for (Map.Entry<String, String> entry : parametros.get().entrySet()) {
                if (entry.getKey() != null && entry.getValue() != null) {
                    if (primerParam) {
                        urlBuilder.append(entry.getKey())
                                .append("=")
                                .append(URLEncoder.encode(entry.getValue(), StandardCharsets.UTF_8));
                        primerParam = false;
                    } else {
                        urlBuilder.append("&")
                                .append(entry.getKey())
                                .append("=")
                                .append(URLEncoder.encode(entry.getValue(), StandardCharsets.UTF_8));
                    }
                }
            }
        }

        return urlBuilder.toString();
    }

    protected ApiResponse<List<T>> obtenerData(
            String url,
            String id,
            String fechaInicial,
            String fechaFinal,
            String fechaUltimaModificacion
    ) {
        logParametros(id, fechaInicial, fechaFinal, fechaUltimaModificacion);

        Optional<Map<String, String>> parametros = Optional.of(new HashMap<>());
        parametros.get().put("Id", id);
        parametros.get().put("FechaInicial", fechaInicial);
        parametros.get().put("FechaFinal", fechaFinal);

        if(fechaUltimaModificacion != null && !fechaUltimaModificacion.trim().isEmpty()){
            parametros.get().put("FechaUltModificacion", fechaUltimaModificacion);
        }

        return obtenerSiARInfo(getTypeReference(), url, parametros);
    }

    protected ApiResponse<List<T>> obtenerData(
            String url,
            String id,
            String fechaInicial,
            String fechaFinal

    ) {
        logParametros(id, fechaInicial, fechaFinal, null);

        Optional<Map<String, String>> parametros = Optional.of(new HashMap<>());
        parametros.get().put("Id", id);
        parametros.get().put("FechaInicial", fechaInicial);
        parametros.get().put("FechaFinal", fechaFinal);

        return obtenerSiARInfo(getTypeReference(), url, parametros);
    }

    private void logParametros(
            String id,
            String fechaInicial,
            String fechaFinal,
            String fechaUltModificacion
    ) {
        System.out.println("=== PARÁMETROS RECIBIDOS ===");
        System.out.println("ProvinciaId: " + id);
        System.out.println("FechaInicial: " + fechaInicial);
        System.out.println("FechaFinal: " + fechaFinal);
        System.out.println("FechaUltModificacion: " + fechaUltModificacion);
    }


    // Métodos abstractos para personalizar para cada servicio
    protected abstract String getSuccessMessage();
    protected abstract String getErrorMessage();
    protected abstract ParameterizedTypeReference<ResponseWrapper<T>> getTypeReference();
}
