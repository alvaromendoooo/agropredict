defmodule AemetApi.Application do
  use Application

  @impl true
  def start(_type, _args) do
    children = [
      # Iniciar el servidor HTTP con Cowboy
      {Plug.Cowboy, 
        scheme: :http, 
        plug: AemetApi.Router, 
        options: [port: get_port()]
      }
    ]

    opts = [strategy: :one_for_one, name: AemetApi.Supervisor]
    Supervisor.start_link(children, opts)
  end

  defp get_port do
    Application.get_env(:aemet_api, :port, 4000)
  end
end