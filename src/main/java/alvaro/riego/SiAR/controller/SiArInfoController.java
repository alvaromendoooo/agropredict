package alvaro.riego.SiAR.controller;


import alvaro.riego.SiAR.model.ProvinciaDTO;
import alvaro.riego.SiAR.model.SiAREstacionesInfoDTO;
import alvaro.riego.SiAR.model.SiARUserInfoDTO;
import alvaro.riego.SiAR.service.EstacionesInfoService;
import alvaro.riego.SiAR.service.ProvinciaService;
import alvaro.riego.SiAR.service.UserInfoService;
import alvaro.riego.SiAR.utils.ApiResponse;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/riego/siar/v1/Info")
public class SiArInfoController {

    private final UserInfoService siARUserInfoService;
    private final EstacionesInfoService siAREstacionesInfoService;
    private final ProvinciaService siARProvinciaService;

    public SiArInfoController(UserInfoService siARUserInfoService, EstacionesInfoService siAREstacionesInfoService, ProvinciaService siARProvinciaService){
        this.siARUserInfoService = siARUserInfoService;
        this.siAREstacionesInfoService = siAREstacionesInfoService;
        this.siARProvinciaService = siARProvinciaService;
    }

    @GetMapping("/userInfo")
    public ResponseEntity<ApiResponse<List<SiARUserInfoDTO>>> obtenerInfoUser(){
        ApiResponse<List<SiARUserInfoDTO>> response = siARUserInfoService.obtenerInformacionAcceso();

        HttpStatus status = response.isSuccess() ? HttpStatus.OK : HttpStatus.SERVICE_UNAVAILABLE;

        return ResponseEntity.status(status).body(response);
    }

    @GetMapping("/disponibilidad")
    public ResponseEntity<ApiResponse<Map<String, Object>>> verificarDisponibilidad(){
        ApiResponse<Map<String, Object>> response = siARUserInfoService.verificarDisponibilidad();

        HttpStatus status = response.isSuccess() ? HttpStatus.OK : HttpStatus.SERVICE_UNAVAILABLE;

        return ResponseEntity.status(status).body(response);
    }

    @GetMapping("/estacionesInfo")
    public ResponseEntity<ApiResponse<List<SiAREstacionesInfoDTO>>> obtenerEstacionesInfo(){
        ApiResponse<List<SiAREstacionesInfoDTO>> response = siAREstacionesInfoService.obtenerInformacionEstaciones();

        System.out.println("=== ANTES DE RESPONDER ===");
        System.out.println("Success: " + response.isSuccess());
        System.out.println("Message: " + response.getMessage());
        System.out.println("Data: " + response.getData());
        if (response.getData() != null && !response.getData().isEmpty()) {
            System.out.println("Primera estación en data:");
            SiAREstacionesInfoDTO primera = response.getData().getFirst();
            System.out.println("  - Estacion: " + primera.getEstacion());
            System.out.println("  - Codigo: " + primera.getCodigo());
            System.out.println("  - Termino: " + primera.getTermino());
        }
        System.out.println("==========================");

        HttpStatus status = response.isSuccess() ? HttpStatus.OK : HttpStatus.SERVICE_UNAVAILABLE;

        return ResponseEntity.status(status).body(response);
    }

    @GetMapping("/provinciasInfo")
    public ResponseEntity<ApiResponse<List<ProvinciaDTO>>> obtenerProvinciasInfo(){
        ApiResponse<List<ProvinciaDTO>> response = siARProvinciaService.obtenerInformacionProvincias();

        HttpStatus status = response.isSuccess() ? HttpStatus.OK : HttpStatus.SERVICE_UNAVAILABLE;

        return ResponseEntity.status(status).body(response);
    }
}
