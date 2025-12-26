package alvaro.riego.SiAR.controller;

import alvaro.riego.SiAR.model.DiaDTO;
import alvaro.riego.SiAR.model.HoraDTO;
import alvaro.riego.SiAR.model.SemanaDTO;
import alvaro.riego.SiAR.service.DiaService;
import alvaro.riego.SiAR.service.HoraService;
import alvaro.riego.SiAR.service.SemanaService;
import alvaro.riego.SiAR.utils.ApiResponse;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import java.util.List;

@RestController
@RequestMapping("/riego/siar/v1/Datos")
public class SiARDataController {

    private final DiaService siarDiaService;
    private final HoraService siarHoraService;

    private final SemanaService siarSemanaService;

    public SiARDataController(DiaService siarDiaService, HoraService siarHoraService, SemanaService siarSemanaService){
        this.siarDiaService = siarDiaService;
        this.siarHoraService = siarHoraService;
        this.siarSemanaService = siarSemanaService;
    }

    @GetMapping("Dia/provincias")
    public ResponseEntity<ApiResponse<List<DiaDTO>>> getDatosDiarioProvincias(
            @RequestParam String id,
            @RequestParam String fechaInicial,
            @RequestParam String fechaFinal,
            @RequestParam(required = false) String fechaUltModificacion
    ){


        ApiResponse<List<DiaDTO>> response = siarDiaService.obtenerDatosDiaProvincia(
                id, fechaInicial, fechaFinal, fechaUltModificacion);

        HttpStatus status = response.isSuccess() ? HttpStatus.OK : HttpStatus.SERVICE_UNAVAILABLE;

        return ResponseEntity.status(status).body(response);

    }

    @GetMapping("Dia/estaciones")
    public ResponseEntity<ApiResponse<List<DiaDTO>>> getDatosDiariosEstaciones(
            @RequestParam String id,
            @RequestParam String fechaInicial,
            @RequestParam String fechaFinal
    ) {
        ApiResponse<List<DiaDTO>> response = siarDiaService.obtenerDatosDiaEstacion(id, fechaInicial, fechaFinal);

        HttpStatus status = response.isSuccess() ? HttpStatus.OK : HttpStatus.SERVICE_UNAVAILABLE;

        return ResponseEntity.status(status).body(response);
    }

    @GetMapping("Hora/provincias")
    public ResponseEntity<ApiResponse<List<HoraDTO>>> getDatosHoraProvincias(
            @RequestParam String id,
            @RequestParam String fechaInicial,
            @RequestParam String fechaFinal,
            @RequestParam(required = false) String fechaUltModificacion
    ) {
        ApiResponse<List<HoraDTO>> response = siarHoraService.obtenerDatosHorariosProvincias(id, fechaInicial, fechaFinal, fechaUltModificacion);

        HttpStatus status = response.isSuccess() ? HttpStatus.OK : HttpStatus.SERVICE_UNAVAILABLE;

        return ResponseEntity.status(status).body(response);
    }

    @GetMapping("Hora/estaciones")
    public ResponseEntity<ApiResponse<List<HoraDTO>>> getDatosHoraEstaciones(
            @RequestParam String id,
            @RequestParam String fechaInicial,
            @RequestParam String fechaFinal
    ) {
        ApiResponse<List<HoraDTO>> response = siarHoraService.obtenerDatosHoratiosEstacion(id, fechaInicial, fechaFinal);

        HttpStatus status = response.isSuccess() ? HttpStatus.OK : HttpStatus.SERVICE_UNAVAILABLE;

        return ResponseEntity.status(status).body(response);
    }

    @GetMapping("Semana/provincias")
    public ResponseEntity<ApiResponse<List<SemanaDTO>>> getDatosSemanaProvincias(
            @RequestParam String id,
            @RequestParam String fechaInicial,
            @RequestParam String fechaFinal,
            @RequestParam(required = false) String fechaUltModificacion
    ) {
        ApiResponse<List<SemanaDTO>> response = siarSemanaService.obtenerDatosSemanalesProvincias(id, fechaInicial, fechaFinal, fechaUltModificacion);

        HttpStatus status = response.isSuccess() ? HttpStatus.OK : HttpStatus.SERVICE_UNAVAILABLE;

        return ResponseEntity.status(status).body(response);
    }

    @GetMapping("Semana/estaciones")
    public ResponseEntity<ApiResponse<List<SemanaDTO>>> getDatosSemanaEstaciones(
            @RequestParam String id,
            @RequestParam String fechaInicial,
            @RequestParam String fechaFinal
    ) {
        ApiResponse<List<SemanaDTO>> response = siarSemanaService.obtenerDatosSemanalesEstacion(id, fechaInicial, fechaFinal);

        HttpStatus status = response.isSuccess() ? HttpStatus.OK : HttpStatus.SERVICE_UNAVAILABLE;

        return ResponseEntity.status(status).body(response);
    }
}
