package alvaro.riego.SiAR.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

import java.util.Date;

@Data
public class SemanaDTO {
    @JsonProperty("Año")
    private Short año;
    @JsonProperty("Semana")
    private Short semana;
    @JsonProperty("TempMedia")
    private Float tempMedia;
    @JsonProperty("TempMax")
    private Float tempMax;
    @JsonProperty("DiaHorMinTempMax")
    private Date diaHorMinTempMax;
    @JsonProperty("TempMin")
    private Float tempMin;
    @JsonProperty("DiaHorMinTempMin")
    private Date diaHorMinTempMin;
    @JsonProperty("HumedadMedia")
    private Float humedadMedia;
    @JsonProperty("HumedadMax")
    private Float humedadMax;
    @JsonProperty("DiaHorMinHumMin")
    private Date diaHorMinHumMin;
    @JsonProperty("VelViento")
    private Float velViento;
    @JsonProperty("DirViento")
    private Float dirViento;
    @JsonProperty("VelVientoMax")
    private Float velVientoMax;
    @JsonProperty("DiaHorMinVelMax")
    private Date diaHorMinVelMax;
    @JsonProperty("DirVientoVelMax")
    private Float dirVientoVelMax;
    @JsonProperty("Radiacion")
    private Float radiacion;
    @JsonProperty("Precipitacion")
    private Float precipitacion;
    @JsonProperty("EtPMon")
    private Float EtPMon;
    @JsonProperty("PePMon")
    private Float PePMon;
    @JsonProperty("Estacion")
    private String estacion;
}
