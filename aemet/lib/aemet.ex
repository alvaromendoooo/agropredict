defmodule Aemet do
  use Application
  @moduledoc """
  Documentation for `Aemet`.
  """

  @doc """
  Hello world.

  ## Examples

      iex> Aemet.hello()
      :world

  """
  def hello do
    :world
  end

  def start(_type, _args) do
    Aemet.Supervisor.start_link()
  end
end
