defmodule AemetApi.Router do
    use Plug.Router
    use Plug.ErrorHandler

    plug Plug.Logger
    plug :match
    plug Plug.Parsers, parsers: [:json], json_decoder: Poison
    plug :dispatch

    # Health check
    get "/health" do
        send_json(conn, 200, %{status: "ok", service: "aemet_api"})
    end

    #### PREDICCIONES ACTUALES ####

    # Prediccion de hoy por CCAA
    get "/api/prediccion/hoy/ccaa/:codigo" do
        endpoint = "/prediccion/ccaa/hoy/#{codigo}"
        realizar_peticion(conn, endpoint)
    end

    # Prediccion de hoy nacional
    get "/api/prediccion/hoy/nacional" do
        endpoint = "/prediccion/nacional/hoy"
        realizar_peticion(conn, endpoint)
    end

    # Prediccion de hoy provincia
    get "/api/prediccion/hoy/provincia/:codigo" do
        endpoint = "/prediccion/provincia/hoy/#{codigo}"
        realizar_peticion(conn, endpoint)
    end

    #### Predicciones futuras ####

    # Prediccion mañana por CCAA
    get "/api/prediccion/tomorrow/:ccaa/:fecha" do
        endpoint = "/prediccion/ccaa/manana/#{ccaa}/elaboracion/#{fecha}"
        realizar_peticion(conn, endpoint)
    end

    # Prediccion pasadomñana por CCAA
    get "/api/prediccion/aftertomorrow/:ccaa/:fecha" do
        endpoint = "/prediccion/ccaa/pasadomanana/#{ccaa}/elaboracion/#{fecha}"
        realizar_peticion(conn, endpoint)
    end

    # Prediccion mañana Nacional
    get "/api/prediccion/nacional/tomorrow/:fecha" do
        endpoint = "/prediccion/nacional/manana/elaboracion/#{fecha}"
        realizar_peticion(conn, endpoint)
    end

    # Prediccion pasadomañana Nacional
    get "/api/prediccion/nacional/aftertomorrow/:fecha" do
        endpoint = "/prediccion/nacional/pasadomanana/elaboracion/#{fecha}"
        realizar_peticion(conn, endpoint)
    end

    # Prediccion mañana Provincial
    get "/api/prediccion/provincial/tomorrow/:provincia/:fecha" do
        endpoint = "/prediccion/provincia/manana/#{provincia}/elaboracion/#{fecha}"
        realizar_peticion(conn, endpoint)
    end

    # Caso en el que no se encuentra la ruta que se ha solicitado
    match _ do
        send_json(conn, 404, %{error: "Ruta no encontrada"})
    end


    # Función para realizar peticiones
    defp realizar_peticion(conn, endpoint) do
        case AemetClient.realizar_peticiones(endpoint) do
            {:ok, datos} ->
                # Intentar parsear los datos a JSON, si falla, se devuelve en formato de texto
                case Poison.decode(datos) do
                    {:ok, json_data} -> send_json(conn, 200, json_data)
                    {:error, _} -> send_text(conn, 200, datos)
                end
            {:errro, reason} ->
                send_json(conn, 500, %{error: reason})
        end
    end

    # Función para enviar JSON
    defp send_json(conn, status, datos) do
        conn
        |> put_resp_content_type("application/json")
        |> send_resp(status, Poison.encode!(datos))
    end

    # Función para enviar texto plano
    defp send_text(conn, status, text) do
        conn
        |> put_resp_content_type("text/plain; charset=utf-8")
        |> send_resp(status, text)
    end

    # Manejador de errores
    def handle_errors(conn, %{kind: kind, reason: reason, stack: _stack}) do
        error_message = %{
        error: "Internal server error",
        kind: kind,
        reason: inspect(reason)
        }
        send_json(conn, 500, error_message)
    end
end

