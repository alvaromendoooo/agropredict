import threading
import logging
from ..informe.form_cert_sign import FirmaService
from typing import Optional


logger = logging.getLogger()

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
    plagas : Optional[list],
    tipo_informe : str,
    datos_estimados : Optional[dict],
    parcelas : Optional[dict],
    sensores : Optional[list]
):
    """
    Lanza en background la generación del informe sobre riesgos de plagas y enfermedades y 
    su firma digital.
    """
    from ..informe.form_plagues_calculated_generator import InformePlagaService
    from ..informe.form_plague_estimated_generator import InformePlagaEstimadaService

    if tipo_informe == "calculado":
        pasos = [
            (InformePlagaService.crear_informe, (plagas), {}),
            (FirmaService.generar_firma, ("plagas",), {}),
        ]
    elif tipo_informe == "estimado":
        pasos = [(InformePlagaEstimadaService.crear_informe_estimado, (datos_estimados, parcelas, sensores, True), {}),]

    thread = threading.Thread(
        target = _background_pipeline,
        args = (app, pasos),
        daemon = True
    )
    thread.start()