package alvaro.riego.ITACyL.controller;

import alvaro.riego.ITACyL.model.ItemsDTO;
import alvaro.riego.ITACyL.model.PlagueRequestParams;
import alvaro.riego.ITACyL.service.PlagueService;
import alvaro.riego.ITACyL.utils.ApiResponse;
import alvaro.riego.ITACyL.utils.EnumParameter;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/plagas/itacyl/v1/Datos")
@Validated
public class PlagueController {
    private final PlagueService plagueService;

    public PlagueController(PlagueService service) {
        this.plagueService = service;
    }

    @GetMapping("")
    public ResponseEntity<ApiResponse<List<ItemsDTO>>> getDatosPlagas (
            @Valid PlagueRequestParams params
            ) {
        ApiResponse<List<ItemsDTO>> response = plagueService.obtenerDatosPlagas(params.getCrop(), params.getGroup());

        HttpStatus status = response.isSuccess() ? HttpStatus.OK : HttpStatus.SERVICE_UNAVAILABLE;

        return ResponseEntity.status(status).body(response);
    }
}
