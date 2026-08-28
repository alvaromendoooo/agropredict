import Config

config :aemet_api,
  aemet_base_url: "https://opendata.aemet.es/opendata/api",
  aemet_poll_interval: 60_000, # cada 60 segundos
  aemet_api_key: System.get_env("AEMET_API_KEY"),
  port: String.to_integer(System.get_env("PORT") || "4000")

config :mix_docker, image: "mendo1/aemet"

config :logger,
  level: :info,
  truncate: 1024
