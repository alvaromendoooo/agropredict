from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, PageBreak, KeepTogether
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.shapes import Drawing
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional
from functools import partial
import os
import json

ruta_directorio_actual = os.getcwd()

#=== INFORMACIÓN DE ESTRUCTURA INFORME ===#
TITULO_INFORME = "Informe de Predicciones ante Riesgos de Helada"
SUBTITULO = "Predicciones Meteorológicas Automatizadas - Histórico"
AUTOR = "Álvaro Mendo Martín"
FECHA = date.today().strftime("%d/%m/%Y")
NOMBRE_ARCHIVO = "reporte_riesgos_heladas_acumulado.pdf"
NOMBRE_UNIVERSIDAD = "Escuela Politécnica - Cáceres"
URL_LOGO_UNIVERSIDAD = os.path.join(ruta_directorio_actual, "assets", "logouex.jpg")

#=== CONFIGURACION COLORES ===#
COLOR_PRIMARIO = colors.HexColor("#006414")
COLOR_SECUNDARIO = colors.HexColor("#462204")
COLOR_FONDO_TABLA = colors.HexColor("#EAF4FB")
COLOR_ACENTO = colors.HexColor("#B91C1C")
COLOR_HOY = colors.HexColor("#FFF3CD")  
COLOR_NUEVO = colors.HexColor("#D4EDDA")  

MAPA_CODIGO_PROVINCIA = {
    "CC" : "Cáceres", "BA" : "Badajoz", "IB" : "Islas Baleares", "B" : "Barcelona",
    "C" : "A Coruña", "GI" : "Girona", "HU" : "Huesca", "LL" : "Lleida",
    "LO" : "La Rioja", "LU" : "Lugo", "M" : "Madrid", "MU" : "Murcia",
    "NA" : "Navarra", "OU" : "Ourense", "O" : "Asturias", "GC" : "Las Palmas",
    "PO" : "Pontevedra", "TF" : "Tenerife", "T" : "Tarragona", "TE" : "Teruel", "Z" : "Zaragoza"
}

class InformeHeladaService():
    
    METADATA_FILE = "informe_metadata.json"
    
    @staticmethod
    def _cargar_metadata(directorio):
        metadata_path = directorio / InformeHeladaService.METADATA_FILE
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                return json.load(f)
        return {"fechas_incluidas": [], "ultima_actualizacion": None, "total_entradas": 0, "tipo_datos": []}
    
    @staticmethod
    def _guardar_metadata(directorio, metadata):
        metadata_path = directorio / InformeHeladaService.METADATA_FILE
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
    
    @staticmethod
    def _extraer_datos_para_tabla(predicciones, fecha_str):
        filas = []
        datos_variedades = predicciones.get('evaluaciones_variedades', {})
        
        if datos_variedades is not None and 'evaluaciones' in datos_variedades:
            datos = datos_variedades.get('evaluaciones', [])
            for p in datos:
                filas.append({
                    'fecha': fecha_str, 'tipo': 'variedad', 'nombre': p.get('variedad', '-'),
                    'temp_min': p.get('temperatura_evaluada', 0), 'temp_max': None,            
                    'nivel': p.get('nivel_riesgo', '-'), 'porcentaje_riesgo': p.get('porcentaje_riesgo', 0),
                    'localidad': None, 'provincia': None, 'altitud': None
                })
                
        elif predicciones.get('evaluacion_localidades', {}).get('evaluaciones') is not None:
            datos = predicciones['evaluacion_localidades']['evaluaciones']
            for p in datos:
                filas.append({
                    'fecha': fecha_str, 'tipo': 'localidad', 'nombre': p.get('localidad', '-'),
                    'temp_min': p.get('temperatura_minima', 0), 'temp_max': p.get('temperatura_maxima', 0),
                    'nivel': p.get('nivel_riesgo', '-'), 'porcentaje_riesgo': p.get('porcentaje_riesgo', 0),
                    'localidad': p.get('localidad'), 'provincia': p.get('provincia'), 'altitud': p.get('altitud_metros')
                })
        else:
            filas.append({
                'fecha': fecha_str, 'tipo': 'general', 'nombre': 'Predicción General',
                'temp_min': None, 'temp_max': None, 'nivel': predicciones.get('nivel', '—'),
                'porcentaje_riesgo': predicciones.get('porcentaje_riesgo', 0), 'localidad': None,
                'provincia': None, 'altitud': None,
                'estado_cielo': predicciones.get('datos_meteorologicos', {}).get('estado_cielo', '-'),
                'precipitaciones': predicciones.get('datos_meteorologicos', {}).get('precipitaciones', '-')
            })
        return filas
    
    @staticmethod
    def _generar_grafico(data: list, is_cultivo: bool):
        d = Drawing(400, 200)
        fechas = list(dict.fromkeys(dato['fecha'] for dato in data))
        etiquetas = list(dict.fromkeys(
            dato['nombre'] for dato in data if not is_cultivo or (is_cultivo and dato.get('tipo') == 'variedad')
        ))

        series = []
        for nombre in etiquetas:
            serie = []
            for fecha in fechas:
                encontrado = next((d['porcentaje_riesgo'] for d in data if d['nombre'] == nombre and d['fecha'] == fecha), 0)
                serie.append(encontrado)
            series.append(serie)

        lc = HorizontalLineChart()
        lc.x, lc.y = 50, 50
        lc.height, lc.width = 125, 300
        lc.data = series
        lc.joinedLines = 1
        lc.fillColor = colors.white
        lc.categoryAxis.categoryNames = fechas
        lc.valueAxis.valueMin, lc.valueAxis.valueMax = 0, 100
        lc.valueAxis.valueSteps = [5, 15, 25, 50, 75, 100]

        lc.categoryAxis.labels.angle = 45
        lc.categoryAxis.labels.boxAnchor = 'e'
        lc.categoryAxis.labels.fontSize = 6
        lc.categoryAxis.labels.dy = -10

        paso = max(1, len(fechas) // 7)
        lc.categoryAxis.categoryNames = [fecha if i % paso == 0 else "" for i, fecha in enumerate(fechas)]

        from reportlab.graphics.charts.legends import LineLegend
        legend = LineLegend()
        legend.fontSize = 8
        legend.alignment = 'right'
        legend.x, legend.y = 0, 0
        legend.columnMaximum = 2
        legend.fontName = 'Helvetica'
        legend.colorNamePairs = [(lc.lines[i].strokeColor, etiquetas[i]) for i in range(len(series))]

        d.add(lc)
        d.add(legend)
        return d
    
    @staticmethod
    def _generar_tabla_historica(historial_datos):
        if not historial_datos:
            return None
        
        tipos = set([d['tipo'] for d in historial_datos])
        
        if 'variedad' in tipos:
            cabecera = ["Fecha", "Variedad", "Temp. Mín", "Nivel", "Riesgo %"]
            datos_tabla = [cabecera]
            for d in historial_datos:
                if d['tipo'] == 'variedad':
                    datos_tabla.append([d['fecha'], d['nombre'], f"{float(d['temp_min']):.1f}°C" if d['temp_min'] is not None else '-', d['nivel'].upper() if d['nivel'] else '-', f"{float(d['porcentaje_riesgo']):.0f}%"])
            # Rediseño: sumatoria exacta a 6.5 pulgadas
            col_widths = [1.2*inch, 1.8*inch, 1.1*inch, 1.2*inch, 1.2*inch]
            
        elif 'localidad' in tipos:
            cabecera = ["Fecha", "Localidad", "Provincia", "T. Mín", "T. Máx", "Nivel", "Riesgo %"]
            datos_tabla = [cabecera]
            for d in historial_datos:
                if d['tipo'] == 'localidad':
                    datos_tabla.append([d['fecha'], d['localidad'] or '-', d['provincia'] or '-', f"{float(d['temp_min']):.1f}°C", f"{float(d['temp_max']):.1f}°C" if d['temp_max'] is not None else '-', d['nivel'].upper() if d['nivel'] else '-', f"{float(d['porcentaje_riesgo']):.0f}%"])
            # Rediseño: Corregido desbordamiento previo (sumaba 6.8). Ahora 6.5 exactas.
            col_widths = [0.9*inch, 1.2*inch, 0.9*inch, 0.8*inch, 0.8*inch, 1.0*inch, 0.9*inch]
            
        else:
            cabecera = ["Fecha", "Estado Cielo", "Precipitaciones", "Nivel", "Riesgo %"]
            datos_tabla = [cabecera]
            for d in historial_datos:
                if d['tipo'] == 'general':
                    datos_tabla.append([d['fecha'], d.get('estado_cielo', '-'), d.get('precipitaciones', '-'), d['nivel'].upper() if d['nivel'] else '-', f"{float(d['porcentaje_riesgo']):.0f}%"])
            # Rediseño: Corregido desbordamiento previo. Ahora 6.5 exactas.
            col_widths = [1.1*inch, 1.8*inch, 1.4*inch, 1.2*inch, 1.0*inch]
        
        tabla = Table(datos_tabla, colWidths=col_widths, repeatRows=1)
        tabla.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_PRIMARIO),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 8.5),
            ("ALIGN", (1, 1), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("BOX", (0, 0), (-1, -1), 1, COLOR_PRIMARIO),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        
        hoy = date.today().strftime("%d/%m/%Y")
        ayer = (date.today() - timedelta(days=1)).strftime("%d/%m/%Y")
        
        for i, fila in enumerate(datos_tabla[1:], start=1):
            if fila[0] == hoy:
                tabla.setStyle(TableStyle([('BACKGROUND', (0, i), (-1, i), COLOR_HOY)]))
            elif fila[0] not in [hoy, ayer]:
                alpha = max(0.85, 1.0 - (i * 0.02))
                color_fondo = colors.Color(0.95, 0.95, 0.95, alpha=alpha)
                tabla.setStyle(TableStyle([('BACKGROUND', (0, i), (-1, i), color_fondo)]))
        
        return tabla
    
    @staticmethod
    def encabezado_pie(canvas_obj, doc, localizacion_calculo: str):
        canvas_obj.saveState()
        ancho, alto = letter

        canvas_obj.setFillColor(COLOR_PRIMARIO)
        canvas_obj.rect(0, alto - 70, ancho, 70, fill=True, stroke=False)

        canvas_obj.setFillColor(colors.white)
        canvas_obj.setFont("Helvetica-Bold", 14)
        canvas_obj.drawString(1 * inch, alto - 25, TITULO_INFORME)

        canvas_obj.setFont("Helvetica", 9)
        canvas_obj.drawString(1 * inch, alto - 38, SUBTITULO)

        canvas_obj.setFont("Helvetica", 7)
        canvas_obj.drawString(1 * inch, alto - 50, "Fuentes: AEMET (predicción futura) · SiAR-Extremadura (datos históricos)")
        canvas_obj.drawString(1 * inch, alto - 63, f"Localización de cálculo: {localizacion_calculo or 'No especificada'}")

        canvas_obj.setFont("Helvetica", 9)
        canvas_obj.drawRightString(ancho - 1 * inch, alto - 25, f"Actualización: {FECHA}")

        if hasattr(doc, 'total_entradas'):
            canvas_obj.drawRightString(ancho - 1 * inch, alto - 38, f"Registros: {doc.total_entradas}")

        canvas_obj.setStrokeColor(COLOR_SECUNDARIO)
        canvas_obj.setLineWidth(2)
        canvas_obj.line(0.75 * inch, alto - 75, ancho - 0.75 * inch, alto - 75)

        # Rejilla inferior protectora fija en Y=45
        canvas_obj.setStrokeColor(COLOR_PRIMARIO)
        canvas_obj.setLineWidth(1)
        canvas_obj.line(0.75 * inch, 45, ancho - 0.75 * inch, 45)

        canvas_obj.setFillColor(COLOR_PRIMARIO)
        canvas_obj.setFont("Helvetica", 8)
        canvas_obj.drawString(1 * inch, 30, f"© {date.today().year} {AUTOR}  |  Histórico desde: {getattr(doc, 'fecha_inicio', FECHA)}")

        canvas_obj.setFont("Helvetica-Bold", 9)
        canvas_obj.drawCentredString(ancho / 2, 30, f"Página {doc.page}")

        canvas_obj.setFont("Helvetica", 8)
        canvas_obj.drawRightString(ancho - 1 * inch, 30, "Informe acumulativo")
        canvas_obj.restoreState()

    @staticmethod
    def _crear_seccion_contexto(metadata: dict, zona: str, provincia: str, styles) -> list:
        elementos = []
        datos_contexto = [
            ["Campo", "Detalle"],
            ["Zona geográfica", zona or "No especificada"],
            ["Provincia / Código", f"{provincia} - {MAPA_CODIGO_PROVINCIA.get(provincia, 'No mapeado')}" if provincia else "No especificada"],
            ["Fuente datos históricos", "SiAR — Red de estaciones agrometeorológicas de Extremadura"],
            ["Fuente datos futuros", "AEMET — Agencia Estatal de Meteorología"],
            ["Período cubierto", f"{min(metadata['fechas_incluidas'])} → {max(metadata['fechas_incluidas'])}" if metadata.get('fechas_incluidas') else "Sin datos aún"],
            ["Última actualización", datetime.fromisoformat(metadata['ultima_actualizacion']).strftime('%d/%m/%Y %H:%M') if metadata.get('ultima_actualizacion') else "—"],
        ]

        col_widths = [2.2 * inch, 4.3 * inch]
        tabla = Table(datos_contexto, colWidths=col_widths)
        tabla.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_PRIMARIO),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8),
            ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (1, 1), (1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_FONDO_TABLA, colors.white]),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
            ("BOX", (0, 0), (-1, -1), 1, COLOR_PRIMARIO),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        elementos.append(tabla)
        return elementos
    
    @staticmethod
    def _crear_seccion_peticion(provincia: Optional[str], evaluacion_variedad: bool, evaluacion_localidad: bool, variedades: Optional[list], localidades: Optional[list]):
        elementos = []
        _badge = lambda act: f'<font color="{"#006414" if act else "#8B0000"}"><b>{"✔ Sí" if act else "✘ No"}</b></font>'

        datos_peticion = [
            ["Parámetro", "Valor"],
            ["Provincia objetivo", f"{provincia} — {MAPA_CODIGO_PROVINCIA.get(provincia, '—')}" if provincia else "No especificada"],
            ["Evaluación sobre variedades", _badge(evaluacion_variedad)],
            ["Evaluación sobre localidades", _badge(evaluacion_localidad)],
            ["Variedades a evaluar", ", ".join(variedades) if variedades else "—"],
            ["Localidades a evaluar", ", ".join(localidades) if localidades else "—"],
        ]

        estilo_clave = ParagraphStyle("PetClave", fontName="Helvetica-Bold", fontSize=8, leading=11)
        estilo_valor = ParagraphStyle("PetValor", fontName="Helvetica", fontSize=8, leading=11)

        filas_render = [datos_peticion[0]]
        for fila in datos_peticion[1:]:
            filas_render.append([Paragraph(fila[0], estilo_clave), Paragraph(fila[1], estilo_valor)])

        col_widths = [2.5 * inch, 4.0 * inch]
        tabla = Table(filas_render, colWidths=col_widths)
        tabla.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_PRIMARIO),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_FONDO_TABLA, colors.white]),
            ("BACKGROUND", (0, 1), (0, -1), colors.HexColor("#F0F7F0")),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CCCCCC")),
            ("BOX", (0, 0), (-1, -1), 1.0, COLOR_PRIMARIO),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        elementos.append(tabla)
        return elementos
    
    @staticmethod
    def _color_a_hex(color) -> str:
        return f"#{int(color.red * 255):02X}{int(color.green * 255):02X}{int(color.blue * 255):02X}"
    
    # ── MÓDULO REDISEÑADO: Estaciones a Ancho Completo ─────────────────────────
    @staticmethod
    def _crear_contexto_estaciones(estaciones: list, fecha_inicio: str, styles) -> list:
        elementos = []
        estilo_caption = ParagraphStyle(
            "CaptionEstaciones", parent=styles["Normal"],
            fontSize=8.5, textColor=colors.HexColor("#475569"), leading=12, spaceAfter=6
        )

        n = len(estaciones)
        intro = (
            f"<b>Estaciones utilizadas para la obtención de datos climáticos:</b> Registros calculados automáticamente sobre "
            f"<b>{n} estación{'es' if n > 1 else ''} meteorológica{'s' if n > 1 else ''}</b> de la red oficial "
            f"SiAR con ponderación geográfica activa desde el {fecha_inicio}."
        )
        elementos.append(Paragraph(intro, estilo_caption))

        estilo_th = ParagraphStyle("TH_Est", fontName="Helvetica-Bold", fontSize=8, textColor=colors.white)
        estilo_td = ParagraphStyle("TD_Est", fontName="Helvetica", fontSize=8, leading=11)
        estilo_td_bold = ParagraphStyle("TD_Est_B", fontName="Helvetica-Bold", fontSize=8, leading=11)

        cabecera = [Paragraph("ID Estación", estilo_th), Paragraph("Ubicación Operativa / Municipio", estilo_th), Paragraph("Red de Origen", estilo_th)]
        filas = [cabecera]

        for est in estaciones:
            filas.append([
                Paragraph(str(est.get("codigo", est.get("code", "—"))), estilo_td_bold),
                Paragraph(str(est.get("nombre", est.get("name", "—"))), estilo_td),
                Paragraph("SiAR Extremadura (Oficial)", estilo_td)
            ])

        # Rediseño: Ajuste exacto al grid de 6.5 pulgadas (1.2 + 3.8 + 1.5 = 6.5)
        col_widths = [1.2 * inch, 3.8 * inch, 1.5 * inch]
        tabla = Table(filas, colWidths=col_widths)
        tabla.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_PRIMARIO),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_FONDO_TABLA, colors.white]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ("BOX", (0, 0), (-1, -1), 1, COLOR_PRIMARIO),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        elementos.append(tabla)
        return elementos

    @staticmethod
    def crear_informe(
        predicciones: dict, estaciones, acumular: bool = True, is_cultivo: bool = True,
        zona: Optional[str] = None, provinicia: Optional[str] = None, cultivo: Optional[str] = None,
        variedades: Optional[list] = None, localidades: Optional[list] = None
    ):
        try:
            if not isinstance(predicciones, dict):
                print("Error: predicciones no es un diccionario válido")
                return

            directorio = Path(__file__).resolve().parent
            directorio_reports = directorio / 'reports'
            directorio_reports.mkdir(parents=True, exist_ok=True)
            ruta_pdf = directorio_reports / NOMBRE_ARCHIVO
            
            metadata = InformeHeladaService._cargar_metadata(directorio)
            fecha_prediccion = predicciones.get("contexto", {}).get("fecha_generacion", "")
            fecha_prediccion = datetime.fromisoformat(fecha_prediccion).strftime("%d/%m/%Y") if fecha_prediccion else FECHA
            
            nuevas_filas = InformeHeladaService._extraer_datos_para_tabla(predicciones, fecha_prediccion)
            
            historial_path = directorio / "historial_datos.json"
            if acumular and ruta_pdf.exists():
                if historial_path.exists():
                    with open(historial_path, 'r') as f:
                        historial_datos = json.load(f)
                else:
                    historial_datos = []
                
                fechas_existentes = set([(d['fecha'], d['tipo'], d['nombre']) for d in historial_datos])
                for fila in nuevas_filas:
                    if (fila['fecha'], fila['tipo'], fila['nombre']) not in fechas_existentes:
                        historial_datos.append(fila)
            else:
                historial_datos = nuevas_filas
                
            with open(historial_path, 'w') as f:
                json.dump(historial_datos, f, indent=2, default=str)
            
            if fecha_prediccion not in metadata['fechas_incluidas']:
                metadata['fechas_incluidas'].append(fecha_prediccion)
            metadata['ultima_actualizacion'] = datetime.now().isoformat()
            metadata['total_entradas'] = len(historial_datos)
            InformeHeladaService._guardar_metadata(directorio, metadata)
            
            historial_datos.sort(key=lambda x: datetime.strptime(x['fecha'], "%d/%m/%Y"), reverse=True)
            
            # === CONFIGURACIÓN CRÍTICA DEL LIENZO ===
            # bottomMargin fijada en 2.1 pulgadas para blindar el espacio de firma PyHanko (Y:50 a Y:150)
            doc = SimpleDocTemplate(
                str(ruta_pdf), pagesize=letter,
                topMargin=1.2 * inch, bottomMargin=2.1 * inch,
                leftMargin=1 * inch, rightMargin=1 * inch,
                title=f"{TITULO_INFORME} - Histórico", author=AUTOR
            )
            
            doc.total_entradas = metadata['total_entradas']
            doc.fecha_inicio = min(metadata['fechas_incluidas']) if metadata['fechas_incluidas'] else FECHA
            
            styles = getSampleStyleSheet()
            estilo_titulo = ParagraphStyle("TituloSeccion", parent=styles["Heading1"], fontSize=12, textColor=COLOR_PRIMARIO, spaceAfter=6, spaceBefore=14)
            estilo_normal = ParagraphStyle("Normal_Custom", parent=styles["Normal"], fontSize=9, leading=13, spaceAfter=5)
            estilo_resumen = ParagraphStyle("Resumen", parent=styles["Normal"], fontSize=8, textColor=colors.gray, leading=11)

            # Estilo personalizado para el interior de las tarjetas de advertencia
            estilo_alerta_box = ParagraphStyle("AlertaBox", parent=styles["Normal"], fontSize=9, leading=13.5, textColor=colors.HexColor("#1E293B"))

            story = [Spacer(1, 0.4 * inch)]
            story.append(Paragraph("INFORME ACUMULATIVO DE RIESGOS DE HELADA<br/><font size='12'>SISTEMA AGRO-PREDICT</font>", ParagraphStyle('Titulo', parent=estilo_titulo, fontSize=15, alignment=1)))
            story.append(Spacer(1, 0.15 * inch))
            
            stats_text = f"""
            <b>Período analizado:</b> {min(metadata['fechas_incluidas'])} - {max(metadata['fechas_incluidas'])}<br/>
            <b>Total de registros:</b> {metadata['total_entradas']} entr.<br/>
            <b>Última actualización:</b> {datetime.fromisoformat(metadata['ultima_actualizacion']).strftime('%d/%m/%Y %H:%M')}<br/>
            <b>Variedades evaluadas:</b> {', '.join(variedades or ['—'])} (Cultivo: {cultivo or 'General'}).
            """
            story.append(Paragraph(stats_text, estilo_normal))
            story.append(HRFlowable(width="100%", thickness=1, color=COLOR_SECUNDARIO, spaceAfter=10))
            
            story.append(Paragraph("FUENTES DE DATOS UTILIZADAS", estilo_titulo))
            story.extend(InformeHeladaService._crear_seccion_contexto(metadata, zona, provinicia, styles))
            story.append(Spacer(1, 0.1 * inch))

            story.append(Paragraph("CUERPO DE LA PETICIÓN - PARÁMETROS", estilo_titulo))
            story.extend(InformeHeladaService._crear_seccion_peticion(provinicia, is_cultivo, not is_cultivo, variedades, localidades))
            story.append(Spacer(1, 0.15 * inch))

            story.append(Paragraph("1. HISTORIAL DE PREDICCIONES ANTE RIESGO DE HELADA", estilo_titulo))
            leyenda = f'<font color="{InformeHeladaService._color_a_hex(COLOR_HOY)}">■</font> Nuevas (hoy) &nbsp;|&nbsp; <font color="{InformeHeladaService._color_a_hex(COLOR_FONDO_TABLA)}">■</font> Anteriores'
            story.append(Paragraph(leyenda, estilo_resumen))
            story.append(Spacer(1, 4))
            
            tabla_historica = InformeHeladaService._generar_tabla_historica(historial_datos)
            if tabla_historica: story.append(tabla_historica)
            story.append(Spacer(1, 0.15 * inch))
            
            # ── MÓDULO REDISEÑADO: Unión Estructurada de Alertas y Estaciones ──────────
            story.append(Paragraph("2. ALERTAS DETECTADAS Y CAPTURA DE CONDICIONES", estilo_titulo))
            story.append(HRFlowable(width="100%", thickness=0.8, color=COLOR_SECUNDARIO, spaceAfter=6))

            contenedor_tecnico = []
            alertas_nuevas = predicciones.get('alertas', [])
            
            if alertas_nuevas:
                for alerta in alertas_nuevas:
                    # Construcción del Callout Box semántico
                    html_alerta = (
                        f"<b><font color='#991B1B'>⚠ ALERTA CRÍTICA DE HELADA:</font></b> {alerta.get('mensaje', '-')}<br/>"
                        f"<font size='8' color='#475569'><b>Recomendación del sistema:</b> {alerta.get('recomendacion', '-')}</font>"
                    )
                    p_alerta = Paragraph(html_alerta, estilo_alerta_box)
                    t_alerta = Table([[p_alerta]], colWidths=[6.5 * inch])
                    t_alerta.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FEF2F2")),
                        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#FCA5A5")),
                        ('LINELEFT', (0, 0), (0, -1), 4.0, colors.HexColor("#DC2626")), # Borde grueso rojo izquierda
                        ('TOPPADDING', (0, 0), (-1, -1), 8),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                        ('LEFTPADDING', (0, 0), (-1, -1), 10),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                    ]))
                    contenedor_tecnico.append(t_alerta)
                    contenedor_tecnico.append(Spacer(1, 0.08 * inch))
            else:
                contenedor_tecnico.append(Paragraph("No se computaron alertas de riesgo bioclimático críticas para el ciclo actual.", estilo_normal))
                contenedor_tecnico.append(Spacer(1, 0.05 * inch))

            if estaciones:
                contenedor_tecnico.append(Spacer(1, 0.05 * inch))
                elementos_est = InformeHeladaService._crear_contexto_estaciones(
                    estaciones=estaciones,
                    fecha_inicio=f"15 de Noviembre",
                    styles=styles
                )
                contenedor_tecnico.extend(elementos_est)
            
            # KeepTogether evita que las Alertas queden separadas de sus Estaciones de cálculo en páginas distintas
            story.append(KeepTogether(contenedor_tecnico))
            
            story.append(PageBreak())
            story.append(Paragraph("3. ANÁLISIS TEMPORAL GRÁFICO", estilo_titulo))
            story.append(Spacer(1, 4))
            d = InformeHeladaService._generar_grafico(historial_datos, is_cultivo)
            story.append(d)

            encabezado_con_params = partial(InformeHeladaService.encabezado_pie, localizacion_calculo=provinicia)
            doc.build(story, onFirstPage=encabezado_con_params, onLaterPages=encabezado_con_params)
            
            print(f"Informe acumulativo actualizado exitosamente.")
            return str(ruta_pdf)
        except Exception as e:
            print(f"Error al crear un nuevo informe de heladas futuras: {e}")