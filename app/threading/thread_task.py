import threading
import logging
from ..informe.form_cert_sign import FirmaService
from typing import Optional


logger = logging.getLogger()

def _background_pipeline(
    app, 
    pasos: list[tuple],
    pdf_queue=None,
):
    with app.app_context():
        resultado = None
        for func, args, kwargs in pasos:
            try:
                logger.info(f"Ejecutando paso: {func.__name__}")
                # Si args es un callable, lo ejecutamos para obtener los args reales
                # Esto permite inyectar el resultado del paso anterior
                args_resueltos = args(resultado) if callable(args) else args
                resultado = func(*args_resueltos, **kwargs)
            except Exception as e:
                logger.error(f"Fallo en el paso: {func.__name__} : {e}")
                if pdf_queue is not None:
                    pdf_queue.put(None)
                break
        else:
            if pdf_queue is not None:
                pdf_queue.put(resultado)

def generar_informe_heladas_background(
    app,
    datos_prediccion : dict,
    acumular : bool,
    is_cultivo : bool,
    tipo : str,
    zona : Optional[str],
    provincia : Optional[str],
    cultivo : Optional[str],
    variedades : Optional[list],
    localidades : Optional[list],
    estaciones,
    pdf_queue = None,
):
    """
    Lanza en background la generación del informe y su firma digital.
    Los dos pasos se ejecutan en secuencia dentro del mismo hilo.
    """
    from ..informe.form_frost_generator import InformeHeladaService
    from ..informe.form_frost_observed import InformeHeladaObservadaService

    if tipo == "futuros":
        pasos = [
            (InformeHeladaService.crear_informe, (datos_prediccion, estaciones, acumular, is_cultivo, zona, provincia, cultivo, variedades, localidades), {}),
            (FirmaService.generar_firma, lambda ruta: ("heladas", None, ruta),{}),
        ]
    elif tipo == "observado":
        pasos = [
            (InformeHeladaObservadaService.crear_informe, (datos_prediccion, zona, provincia, estaciones), {}),
            (FirmaService.generar_firma, lambda ruta: ("heladas", None, ruta), {}),
        ]

    thread = threading.Thread(
        target=_background_pipeline,
        args=(app, pasos, pdf_queue),
        daemon=True
    )

    thread.start()

def generar_informe_plagas_background(
    app, 
    plagas : Optional[list],
    tipo_informe : str,
    datos_estimados : Optional[dict],
    parcelas : Optional[dict],
    sensores : Optional[list],
    pdf_queue = None,
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
            (FirmaService.generar_firma, lambda ruta: ("plagas", None, ruta), {}),
        ]
    elif tipo_informe == "estimado":
        pasos = [
            (InformePlagaEstimadaService.crear_informe_estimado, (datos_estimados, parcelas, sensores, True), {}),
            (FirmaService.generar_firma, lambda ruta: ("plagas", datos_estimados, ruta), {}),    
        ]

    thread = threading.Thread(
        target = _background_pipeline,
        args = (app, pasos, pdf_queue),
        daemon = True
    )
    thread.start()