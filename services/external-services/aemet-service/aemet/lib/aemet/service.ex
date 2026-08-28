defmodule AemetService do
  @moduledoc """
  [AemetService](https://github.com/alvaromendoooo/Aemet.git)
  Servicio encargado de controlar la lógica de negocio de la app
  """

  alias AemetClient, as: Client # Uso del alias para el acceso al módulo para mayor comprensión en el código

  defp save_data_in_file(datos) do
    filename = "estaciones.json" # Nombre del fichero donde almacenamos los datos RAW
    ruta = Path.join(["private", "aemet", filename]) # Ruta relativa donde se va a guardar el fichero filename
    File.write(ruta, datos) # Almacenamiento de datos en fichero
    {:ok, "Se han almacenado correctamente los datos de la petición"}
  end

  defp manejador_errores(reason) do
    IO.inspect(reason, label: "Error AEMET") # Muestra por consola al usuario el contenido del error recibido
  end

  @doc """
  Función encargada de manejar toda la lógica relacionada a la consulta de datos
  sobre AEMET

  Flujo:
  1. Realiza la llamada al método de AemetClient encargado de obtener los datos
  sobre AEMET
  2. Si se han recuperado satisfactoriamente, se almacenan en el fichero definido
  3. Si ocurre algún error, se lo indicamos al usuario por consola
  """
  def actualizar_estaciones(url) do
    case Client.realizar_peticiones(url) do # Llamo a la función del cliente que hace la petición HTTP
      {:ok, datos_raw} -> save_data_in_file(datos_raw) # Si obtengo respuesta exitosa almaceno esos datos en el fichero
      {:error, reason} -> manejador_errores(reason) # Si la respuesta es de error, lo muestro por consola
    end
  end
end
