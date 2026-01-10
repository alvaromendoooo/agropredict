import Config

if config_env() == :prod do
  config :aemet_api,
    aemet_base_url: System.get_env("AEMET_BASE_URL") || "https://opendata.aemet.es/opendata/api",
    aemet_api_key: System.get_env("AEMET_API_KEY") || raise("AEMET_API_KEY no configurada"),
    port: String.to_integer(System.get_env("PORT") || "4000")
end
