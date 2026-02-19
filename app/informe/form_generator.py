from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.platypus import PageBreak
from reportlab.pdfgen import canvas
from datetime import date
import os

ruta_directorio_actual = os.getcwd()
#=== INFORMACIÓN DE ESTRUCTURA INFORME ===#
TITULO_INFORME = "Informe de Predicciones sobre Riesgos de Helada"
SUBTITULO = "Predicciones Meteorológicas Automatizadas"
AUTOR = "Álvaro Mendo Martín"
FECHA = date.today().strftime("%d/%m/%Y")
NOMBRE_ARCHIVO = f"reporte_riesgos_heladas_{date.today()}.pdf"
NOMBRE_UNIVERSIDAD = "Escuela Politécnica - Cáceres"
URL_LOGO_UNIVERSIDAD = os.path.join(ruta_directorio_actual, "/assets/logouex.jpg")

#=== CONFIGURACION COLORES ===#
COLOR_PRIMARIO = colors.HexColor("#006414")
COLOR_SECUNDARIO = colors.HexColor("#462204")
COLOR_FONDO_TABLA = colors.HexColor("#EAF4FB")
COLOR_ACENTO = colors.red

def encabezado_pie(
    canvas_obj,
    doc
):
    """
    Dibuja el encabezado y el pie de pagina definido en cada una de las páginas del documento.
    """
    canvas_obj.saveState()
    ancho, alto = letter

    #=== DEFINICION DEL ENCABEZADO ===#
    # LINEA DECORATIVA SUPERIOR
    canvas_obj.setFillColor(COLOR_PRIMARIO)
    canvas_obj.rect(0, alto - 60, ancho, 60, fill = True, stroke = False)

    # TITULO DEL ENCABEZADO
    canvas_obj.setFillColor(colors.white)
    canvas_obj.setFont("Helvetica-Bold", 14)
    canvas_obj.drawString(1 * inch, alto - 30, TITULO_INFORME)

    canvas_obj.setFont("Helvetica", 10)
    canvas_obj.drawString(1 * inch, alto - 40, SUBTITULO)

    # FECHA EN LA ESQUINA SUPERIOR DERECHA
    canvas_obj.setFont("Helvetica", 9)
    canvas_obj.drawRightString(ancho - 1 * inch, alto - 30, f"Fecha: {FECHA}")
    canvas_obj.drawRightString(ancho - 1 * inch, alto - 48, AUTOR)

    # LÍNEA DECORATIVA BAJO EL ENCABEZADO
    canvas_obj.setStrokeColor(COLOR_SECUNDARIO)
    canvas_obj.setLineWidth(2)
    canvas_obj.line(0.75 * inch, alto - 65, ancho - 0.75 * inch, alto - 65)

    #=== PIE DE PAGINA ===#
    canvas_obj.setStrokeColor(COLOR_PRIMARIO)
    canvas_obj.setLineWidth(1)
    canvas_obj.line(0.75 * inch, 45, ancho - 0.75 * inch, 45)

    canvas_obj.setFillColor(COLOR_PRIMARIO)
    canvas_obj.setFont("Helvetica", 8)
    canvas_obj.drawString(1 * inch, 30, f"© {date.today().year} {AUTOR}  |  Generado: {FECHA}")

    # Número de página centrado
    canvas_obj.setFont("Helvetica-Bold", 9)
    canvas_obj.drawCentredString(ancho / 2, 30, f"Página {doc.page}")

    # Texto derecho del pie
    canvas_obj.setFont("Helvetica", 8)
    canvas_obj.drawRightString(ancho - 1 * inch, 30, "Uso interno — Confidencial")

    canvas_obj.restoreState()

def crear_informe(predicciones: list[dict]):
   
    doc = SimpleDocTemplate(
        NOMBRE_ARCHIVO,
        pagesize = letter,
        # Márgenes: top grande para dejar sitio al encabezado
        topMargin = 1 * inch,
        bottomMargin = 0.9 * inch,
        leftMargin = 1 * inch,
        rightMargin = 1 * inch,
        title = TITULO_INFORME,
        author = AUTOR,
    )

    styles = getSampleStyleSheet()

    # Estilos personalizados
    estilo_titulo = ParagraphStyle(
        "TituloSeccion",
        parent=styles["Heading1"],
        fontSize=13,
        textColor=COLOR_PRIMARIO,
        spaceAfter=8,
        spaceBefore=16,
    )
    estilo_normal = ParagraphStyle(
        "Normal_Custom",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        spaceAfter=6,
    )
    estilo_alerta = ParagraphStyle(
        "Alerta",
        parent=styles["Normal"],
        fontSize=10,
        textColor = COLOR_ACENTO,
        leading=14,
    )

    # ── Contenido ──
    story = []

    # Separador visual (el encabezado ya ocupa la parte superior)
    story.append(Spacer(1, 0.2 * inch))

    # Sección: Resumen ejecutivo
    story.append(Paragraph("1. Resumen Ejecutivo", estilo_titulo))
    story.append(HRFlowable(width="100%", thickness=1, color=COLOR_SECUNDARIO))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        f"Este informe presenta las predicciones de riesgo de heladas generadas el {FECHA}. "
        "Se han analizado las condiciones meteorológicas previstas para los próximos días, "
        "identificando los periodos de mayor vulnerabilidad.",
        estilo_normal,
    ))

    story.append(Spacer(1, 0.15 * inch))

    # Sección: Tabla de predicciones
    story.append(Paragraph("2. Predicciones por Fecha", estilo_titulo))
    story.append(HRFlowable(width="100%", thickness=1, color=COLOR_SECUNDARIO))
    story.append(Spacer(1, 6))

    # Cabecera de la tabla
    datos_tabla = [["Fecha", "Temp. Mín (°C)", "Prob. Helada (%)", "Nivel de Riesgo"]]
    for p in predicciones:
        nivel = p.get("riesgo", "—")
        datos_tabla.append([
            p.get("fecha", ""),
            f"{p.get('temp_min', 0):.1f}",
            f"{p.get('prob_helada', 0) * 100:.0f}%",
            nivel,
        ])

    tabla = Table(datos_tabla, colWidths=[1.5 * inch, 1.5 * inch, 1.8 * inch, 1.7 * inch])
    tabla.setStyle(TableStyle([
        # Cabecera
        ("BACKGROUND",    (0, 0), (-1, 0),  COLOR_PRIMARIO),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0),  10),
        ("ALIGN",         (0, 0), (-1, 0),  "CENTER"),
        # Filas de datos
        ("FONTNAME",      (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",      (0, 1), (-1, -1), 9),
        ("ALIGN",         (1, 1), (-1, -1), "CENTER"),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, COLOR_FONDO_TABLA]),
        # Bordes
        ("GRID",          (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("BOX",           (0, 0), (-1, -1), 1,   COLOR_PRIMARIO),
        # Padding
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(tabla)

    story.append(Spacer(1, 0.2 * inch))

    # Sección: Notas / alertas
    story.append(Paragraph("3. Notas y Alertas", estilo_titulo))
    story.append(HRFlowable(width="100%", thickness=1, color=COLOR_SECUNDARIO))
    story.append(Spacer(1, 6))

    alertas = [p for p in predicciones if p.get("riesgo") == "Alto"]
    if alertas:
        story.append(Paragraph(
            f"⚠ Se han detectado {len(alertas)} periodos con riesgo ALTO de helada. "
            "Se recomienda activar medidas de protección de cultivos.",
            estilo_alerta,
        ))
    else:
        story.append(Paragraph("No se detectan periodos de riesgo alto en el horizonte analizado.", estilo_normal))

    # ── Construir el PDF pasando la función de encabezado/pie ──
    doc.build(story, onFirstPage=encabezado_pie, onLaterPages=encabezado_pie)
    print(f"PDF generado: {NOMBRE_ARCHIVO}")


if __name__ == "__main__":
    datos_ejemplo = [
        {"fecha": "2025-01-14", "temp_min": 1.5,  "prob_helada": 0.32, "riesgo": "Bajo"},
        {"fecha": "2025-01-15", "temp_min": -1.2, "prob_helada": 0.71, "riesgo": "Medio"},
        {"fecha": "2025-01-16", "temp_min": -4.0, "prob_helada": 0.93, "riesgo": "Alto"},
        {"fecha": "2025-01-17", "temp_min": -2.8, "prob_helada": 0.85, "riesgo": "Alto"},
        {"fecha": "2025-01-18", "temp_min": 0.3,  "prob_helada": 0.45, "riesgo": "Medio"},
    ]
    crear_informe(datos_ejemplo)