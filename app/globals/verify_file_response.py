import os
from flask import send_file, jsonify, request
import time

# Ruta absoluta de la carpeta globals/ (donde está este fichero)
GLOBALS_DIR = os.path.dirname(os.path.abspath(__file__))

# Subimos niveles hasta la raíz del proyecto y bajamos a reports/
def _get_directorio(tipo: str) -> str:
    directorios = {
        "plagas":  os.path.join(GLOBALS_DIR, "..", "informe", "reports", "plagas"),
        "heladas": os.path.join(GLOBALS_DIR, "..", "informe", "reports", "heladas"),
    }
    # Normalizamos la ruta (resuelve los "..")
    ruta = directorios.get(tipo)
    return os.path.normpath(ruta) if ruta else None


def verify_file_response(tipo: str, margen_segundos: int = 90):

    directorio = _get_directorio(tipo)

    if not directorio or not os.path.exists(directorio):
        return jsonify({"error": f"Directorio no encontrado para tipo '{tipo}'"}), 404

    pdfs = [
        os.path.join(directorio, f)
        for f in os.listdir(directorio)
        if f.endswith(".pdf")
    ]

    if not pdfs:
        return jsonify({"error": "No hay informes PDF disponibles"}), 404

    pdf_mas_reciente = max(pdfs, key=os.path.getmtime)

    tiempo_modificacion = os.path.getmtime(pdf_mas_reciente)
    segundos_transcurridos = time.time() - tiempo_modificacion

    if segundos_transcurridos > margen_segundos:
        return jsonify({
            "error" : "El informe más reciente es demasiado antiguo",
            "segundos" : round(segundos_transcurridos)
        })

    return send_file(
        pdf_mas_reciente,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=os.path.basename(pdf_mas_reciente)
    )