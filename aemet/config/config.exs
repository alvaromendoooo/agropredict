import Config

config :aemet,
  aemet_base_url: "https://opendata.aemet.es/opendata/api",
  aemet_poll_interval: 60_000, # cada 60 segundos
  aemet_api_key: "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJhbWVuZG9tYUBhbHVtbm9zLnVuZXguZXMiLCJqdGkiOiIxYmIwMjdlMy01NTU5LTRkNzUtYjU2NS05ODE5NzAxZTJhNzYiLCJpc3MiOiJBRU1FVCIsImlhdCI6MTc2MTU1ODE5MiwidXNlcklkIjoiMWJiMDI3ZTMtNTU1OS00ZDc1LWI1NjUtOTgxOTcwMWUyYTc2Iiwicm9sZSI6IiJ9.49xWV3gMuV-dXHSoDQK2Z_Q4CXMGCoFwG_U3V6Gfm78"

config :mix_docker, image: "mendo1/aemet"

config :logger,
  level: :info,
  truncate: 1024
