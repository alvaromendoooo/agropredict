package alvaro.riego.SiAR.model;


import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonPropertyOrder;
import lombok.Data;
import org.springframework.stereotype.Component;

import java.util.Date;
@Data
@Component
public class DiaDTO {
    @JsonProperty("TempMedia")
    // Registro de temperatura media
    private Float tempMedia;
    @JsonProperty("TempMax")
    // Registro de temperatura maxima
    private Float tempMax;
    @JsonProperty("HorMinTempMax")
    // Registro de temperatura maxima en minutos hora
    private Short horMinTempMax;
    @JsonProperty("TempMin")
    // Registro de temperatura minima
    private Float tempMin;
    @JsonProperty("HorMinTempMin")
    // Registro de temperatura minima en minutos hora
    private Short horMinTempMin;
    @JsonProperty("HumedadMedia")
    // Registro de humedad media
    private Float humedadMedia;
    @JsonProperty("HumedadMax")
    // Registro de humedad maxima
    private Float humedadMax;
    @JsonProperty("HorMinHumMax")
    // Registro de humedad maxima en minutos hora
    private Short horMinHumMax;
    @JsonProperty("HumedadMin")
    // Registro de humedad minima
    private Float humedadMin;
    @JsonProperty("HorMinHumMin")
    // Registro de humedad minima en minutos hora
    private Short horMinHumMin;
    @JsonProperty("VelViento")
    // Registro de velocidad del viento
    private Float velViento;
    @JsonPropertyOrder("DirViento")
    // Registro de la direccion del viento
    private Float dirViento;
    @JsonProperty("VelVientoMax")
    // Registro de la velocidad máxima del viento
    private Float velVientoMax;
    @JsonProperty("HorMinVelMax")
    // Registro de la velocidad maxima del viento en minutos hora
    private Short horMinVelMax;
    @JsonProperty("DirVientoVelMax")
    // Registro de la dirección del viento con velocidad maxima
    private Float dirVientoVelMax;
    @JsonProperty("Radiacion")
    // Registro de la radiación
    private Float radiacion;
    @JsonProperty("Precipitacion")
    // Registro de precipitaciones
    private Float precipitacion;
    @JsonProperty("TempSuelo1")
    // Registro de la temperatura del suelo en el punto 1
    private Float tempSuelo1;
    @JsonProperty("TempSuelo2")
    // Registro de la temperatura del suelo en el punto 2
    private Float tempSuelo2;
    @JsonProperty("EtPMon")
    // Registro del monitoreo de evapotranspiracion
    private Float EtPMon;
    @JsonProperty("PePMon")
    // Registro de la programación de la evaporación y transpiración
    private Float PePMon;
    @JsonProperty("Estacion")
    // Registro de la estación a consultar
    private String estacion;
    @JsonProperty("Fecha")
    // Registro de la fecha de consulta
    private Date fecha;

    public boolean tieneEstacion(){
        return estacion != null && !estacion.trim().isEmpty();
    }

    public boolean tieneTempMinMax(){
        return tempMin != 0.0 && tempMax != 0.0;
    }

    public boolean tieneHumedMinMax(){
        return humedadMin != 0.0 && humedadMax != 0.0;
    }

}
