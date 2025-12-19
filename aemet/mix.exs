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
      {:oauther, "~> 1.1"} # Dependencia para OAuth
      # {:dep_from_hexpm, "~> 0.3.0"},
      # {:dep_from_git, git: "https://github.com/elixir-lang/my_dep.git", tag: "0.1.0"}
    ]
  end
end
