import threading
import logging

logger = logging.getLogger()

def _background_task(
    app,
    func,
    *args,
    **kwargs
):
    with app.app_context():
        func(*args, **kwargs)


def _background_pipeline(
    app, 
    pasos : list[tuple]
):
    """
    Ejecuta una lista de (func, args, kwargs) en secuencia dentro del mismo contexto de aplicación.
    Si un paso falla los siguientes se omiten.
    """
    with app.app_context():
        for func, args, kwargs in pasos:
            try:
                logger.info(f"Ejecutando paso: {func.__name__}")
                func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Fallo en el paso: {func.__name__} : {e}")
                break

def generar_informe_background(
    app
):
    """
    Lanza en background la generación del informe y su firma digital.
    Los dos pasos se ejecutan en secuencia dentro del mismo hilo.
    """
    from ..informe.form_generator import InformeService
    from ..informe.form_cert_sign import FirmaService

    datos = [
        {"fecha": "2025-01-14", "temp_min": 1.5,  "prob_helada": 0.32, "riesgo": "Bajo"},
        {"fecha": "2025-01-15", "temp_min": -1.2, "prob_helada": 0.71, "riesgo": "Medio"},
        {"fecha": "2025-01-16", "temp_min": -4.0, "prob_helada": 0.93, "riesgo": "Alto"},
        {"fecha": "2025-01-17", "temp_min": -2.8, "prob_helada": 0.85, "riesgo": "Alto"},
        {"fecha": "2025-01-18", "temp_min": 0.3,  "prob_helada": 0.45, "riesgo": "Medio"},
    ]

    pasos = [
        (InformeService.crear_informe, (datos,), {}),
        (FirmaService.generar_firma, (),{}),
    ]

    thread = threading.Thread(
        target=_background_pipeline,
        args=(app, pasos),
        daemon=True
    )
    thread.start()