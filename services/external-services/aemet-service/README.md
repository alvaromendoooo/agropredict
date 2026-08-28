# AEMET Data Collector Service
Servicio Elixir que consume datos meteorológicos de la API oficial de la Agencia Estatal de Meteorología (AEMET). El servicio se ejecuta periódicamente para recopilar y procesar información meteorológica actualizada, utilizando una arquitectura basada en procesos OTP.

## Propósito
Recopilar y procesar datos meteorológicos de AEMET de forma automatizada y periódica, proporcionando una capa de abstracción que transforma, valida y estructura la información para su posterior consumo o almacenamiento.

## Arquitectura del Proyecto
### Estructura del Proyecto
```
lib/aemet/
├── application.ex        # Punto de entrada de la aplicación
├── supervisor.ex         # Supervisor principal
├── scheduler.ex          # Programador de tareas periódicas
├── orchestrator.ex       # Orquestador de flujos de datos
├── client.ex             # Cliente HTTP para API de AEMET
├── parser.ex             # Parser y transformador de datos
├── config/
│   └── config.ex         # Configuración de la aplicación
└── utils/
    └── validators.ex     # Utilidades de validación
```
### Flujo de Datos
```
Scheduler → Orchestrator → Client → API AEMET
     ↓           ↓           ↓         ↓
Periodic Task   Flow Control  HTTP Request  JSON Response
     ↓           ↓           ↓         ↓
  Timer    Data Pipeline   Response   Raw Data
                     ↓           ↓
                  Parser → Processed Data
                     ↓
               Storage/Output
```

## Diagrama de Procesos OTP
```
Application
    |
Supervisor
    ├── Scheduler (GenServer)
    ├── Orchestrator (GenServer)
    ├── Client (Agent/GenServer)
    └── Parser (Worker)
```

## Tecnologías Utilizadas
* Elixir 1.14+

* Erlang/OTP 25+

* Mix - Gestor de dependencias y build tool

* HTTPoison o Req - Cliente HTTP

* Jason - Parsing JSON

* Logger - Sistema de logging integrado

* ExUnit - Framework de testing

## Configuración
```elixir
# pom de mi proyecto, metadatos del proyecto
defmodule Aemet.MixProject do
  use Mix.Project # Modulo gestionado por mix

  def project do
    [
      app: :aemet, # Nombre de mi proyecto
      version: "0.1.0", # Versión del proyecto
      elixir: "~> 1.19", # Versión de elixir
      start_permanent: Mix.env() == :prod, # Apagar la VM en producción si se cae la app
      deps: deps() # Dependencias externas
    ]
  end

  # Run "mix help compile.app" to learn about applications.
  def application do # Define como se comporta la app al arrancar
    [
      extra_applications: [:logger]
    ]
  end

  # Run "mix help deps" to learn about dependencies.
  defp deps do
    [
      {:httpoison, "~> 2.0"}, # Dependencia de HTTP clients
      {:poison, "~> 3.1"}, # Dependencia JSON decoder
      {:oauther, "~> 1.1"}, # Dependencia para OAuth
      {:jason, "~> 1.0"}, # Dependencia para crear ficheros json
      {:mix_docker, "~> 0.5.0"} # Dependencia para contenerizar la app
      # {:dep_from_hexpm, "~> 0.3.0"},
      # {:dep_from_git, git: "https://github.com/elixir-lang/my_dep.git", tag: "0.1.0"}
    ]
  end
end
```
