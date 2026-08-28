defmodule Aemet.Supervisor do
  @moduledoc """
  [AemetSupervisor](https://github.com/alvaromendoooo/Aemet.git)
  Supervisor principal de la aplicación Aemet
  Se encarga de supervisar los procesos del sistema
  """

  use Supervisor

  ## API pública
  def start_link(init_arg \\ []) do
    Supervisor.start_link(__MODULE__, init_arg, name: __MODULE__)
  end

  ## Callbacks
  def init(_init_args) do
    children = [
      Aemet.Scheduler
    ]

    Supervisor.init(children, strategy: :one_for_one)
  end
end
