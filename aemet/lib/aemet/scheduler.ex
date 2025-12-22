defmodule Aemet.Scheduler do
  @moduledoc """
  [AemetScheduler](https://github.com/alvaromendoooo/Aemet.git)
  Planificador de tareas periódicas para la actualización
  de datos meteorológicos desde AEMET.

  El planificador se ha implementado mediante un proceso GenServer que envía
  mensaje temporizados a sí mismo, evitando llamadas síncronas y desacomplando
  la ejecución periódica de la lógica de negocios. El scheduler únicamente
  corrdina el tiempo de ejecución, delegando la tarea completa en la capa de servicico
  """
  use GenServer # Instancia de servidor que ejecuta procesos concurrentemente
  alias AemetService, as: Service # Alias para entender mejor el codigo

  ## API pública
  @doc """

  Funcionamiento:
  Aemet.Scheduler.start_link(%{
    interval: :timer.hours(6),
    url: "/valores/climatologicos/inventarioestaciones/todasestaciones"
  })
  """
  def start_link(%{interval: interval, url: url}) do
    GenServer.start_link(__MODULE__, %{interval: interval, url: url}, name: __MODULE__)
  end

  ## CallBacks

  @impl true
  def init(state) do
    # Primera ejecución
    Process.send_after(self(), :tick, state.interval)
    {:ok, state}
  end

  @impl true
  def handle_info(:tick, %{interval: interval, url: url} = state) do
    Service.actualizar_estaciones(url)

    #Reprogramar
    Process.send_after(self(), :tick, interval)

    {:noreply, state}
  end
end
