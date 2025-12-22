defmodule AemetClient do
  @moduledoc """
  [Aemet Client](https://github.com/alvaromendoooo/Aemet.git)
  API Client para obtener datos de la API REST que ofrece Aemet
  """

  @doc """
  Dado la url que se le pasa por parámetros, construye la url completa para acceder a la API

  Devuelve:
  - {:ok, url_completa} si la URL es válida
  - {:error, message} si la URL está vacía
  """
  def get_full_url(url) do
    if String.length(url) > 0 do
      base = Application.get_env(:aemet, :aemet_base_url)
      {:ok, base <> url} # Devolvemos la url completa
    else
      {:error, "La url pasada por parámetros no debe de estar vacia"}
    end
  end

  @doc """
  Dada la url que se le pasa por parámetros, realiza las peticiones sobre la url construida

  Flujo:
  1. Construye la URL completa usando `get_full_url/1`
  2. Construye el header con el token de autenticacion
  3. Llama a `HTTPoison.get/2` y devuelve {:ok, body} o {:error, reason}

  Ejecución del método
  {ok, url} = AemetClient.realizar_peticiones("/valores/climatologicos/inventarioestaciones/todasestaciones")
  """
  def realizar_peticiones(url) do
    token = Application.get_env(:aemet, :aemet_api_key)
    header = [
      {"Authorization", "Bearer #{token}"},
      {"Accept", "Application/json; Charset=utf-8"}
    ]
    with {:ok, url_completa} <- get_full_url(url),
        {:ok, %HTTPoison.Response{status_code: 200, body: body_api}} <- HTTPoison.get(url_completa, header),  # Encadenamineto de acciones que pueden fallar
        body_clean = String.trim(body_api, "\""), # Limpiamos valores residuales del body
        {:ok, aemet_map} <- Poison.decode(body_clean), # Si las dos condiciones no fallan, almacena en aemet_map el resultado de los campos decodificados del json 'body'
        datos_url when is_binary(datos_url) <- aemet_map["datos"], # Comprueba que sea un string válido
        {:ok, %HTTPoison.Response{status_code: 200, body: body_datos}} <- HTTPoison.get(datos_url, header) do # Obtenemos los datos desde el endpoint interno que nos ha dado la primera petición
      {:ok, body_datos} # Devuelvo los datos RAW de la petición interna a AEMET
    else
      {:error, %HTTPoison.Error{} = err} -> # Manejo de errores
        {:error, "Error HTTPoison: #{inspect(err)}"}

      {:error, reason} -> {:error, reason} # Propaga errores de URL o de HTTP

      nil -> # Manejo de datos nulos
        {:error, "El campo 'datos' no existe en la respuesta por AEMET"}

      %HTTPoison.Response{status_code: code} ->
        {:error, "HTTP status: #{code}"} # Captura otros códigos HTTP distintos de 200

      other ->
        {:error, "Error desconocido: #{inspect(other)}"}
    end
  end
end
