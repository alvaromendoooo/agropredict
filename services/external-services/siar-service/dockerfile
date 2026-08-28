# Uso de imagen MAVEN con JDK para compilar el proyecto
FROM maven:3.9.4-eclipse-temurin-21-alpine AS builder

# Persona encargada del dockerfile
MAINTAINER mendorr

# Incluyo en el contenedor el directorio base donde colgará toda la aplicacion
WORKDIR /app

# Copiar el archivo pom.xml y descargar las dependencias
COPY pom.xml .
RUN mvn dependency:go-offline -B

# Copiar el resto del codigo fuente
COPY src ./src

# Compilar y empaquetar la aplicación
RUN mvn -X clean package -Dmaven.test.skip=true

# Imagen base para ejecutar el proyecto compilado
FROM eclipse-temurin:21-jre-alpine

# Establecer el directorio de trabajo
WORKDIR /app

# Copiamos el JAR ejecutable desde la carpeta target generado tras la compilación y empaquetacion
COPY --from=builder /app/target/*.jar app.jar

# Expongo el puerto de la aplicacion
EXPOSE 8086

# Comando para ejecutar la aplicacion cuando se lance el contenedor
ENTRYPOINT ["java", "-jar", "app.jar"]