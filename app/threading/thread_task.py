import threading
import logging
from ..informe.form_cert_sign import FirmaService


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

def generar_informe_heladas_background(
    app,
    datos_prediccion : dict,
    acumular : bool,
    is_cultivo : bool
):
    """
    Lanza en background la generación del informe y su firma digital.
    Los dos pasos se ejecutan en secuencia dentro del mismo hilo.
    """
    from ..informe.form_frost_generator import InformeHeladaService

    pasos = [
        (InformeHeladaService.crear_informe, (datos_prediccion,acumular,is_cultivo,), {}),
        (FirmaService.generar_firma, ("heladas",),{}),
    ]

    thread = threading.Thread(
        target=_background_pipeline,
        args=(app, pasos),
        daemon=True
    )
    thread.start()

def generar_informe_plagas_background(
    app, 
    plagas : list
):
    """
    Lanza en background la generación del informe sobre riesgos de plagas y enfermedades y 
    su firma digital.
    """
    from ..informe.form_plagues_generator import InformePlagaService

    pasos = [
        (InformePlagaService.crear_informe, (plagas), {}),
        (FirmaService.generar_firma, ("plagas",), {}),
    ]

    thread = threading.Thread(
        target = _background_pipeline,
        args = (app, pasos),
        daemon = True
    )
    thread.start()