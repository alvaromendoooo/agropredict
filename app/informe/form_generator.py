from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.platypus import PageBreak
from reportlab.pdfgen import canvas
from datetime import date, datetime
from pathlib import Path
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

class InformeService():
    
    @staticmethod
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

    @staticmethod
    def crear_informe(predicciones: dict):

        if not isinstance(predicciones, dict):
            print("Error : predicciones no es un diccionario válido")
            return 

        directorio = Path(__file__).resolve().parent
        directorio.mkdir(parents=True, exist_ok=True)
        ruta_pdf = directorio / NOMBRE_ARCHIVO

        doc = SimpleDocTemplate(
            str(ruta_pdf),
            pagesize = letter,
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

        try:
            # Inicialización de la cabecera de la tabla
            datos_tabla = []

            # Inicialización de datos específicos por prediccion
            datos_variedades = []
            datos_localidades = []

            # Obtener datos de predicción sobre variedades si se ha especificado en la predicción. Puede ser None
            if predicciones.get('evaluaciones_variedades', {}):
                datos_variedades = predicciones.get('evaluaciones_variedades', {}).get('evaluaciones', [])

            # Obtener datos de predicción sobre localidades si se ha especificado en la predicción. Puede ser None
            if not datos_variedades:
                datos_localidades = predicciones.get('evaluacion_localidades', {}).get('evaluaciones', [])

            # Obtener la fecha de prediccion
            fecha = predicciones.get("contexto", {}).get("fecha_generacion", "")
            if fecha:
                fecha = datetime.fromisoformat(fecha).strftime("%Y-%m-%d")
            else:
                "-"

            if datos_variedades: # Quiero que rellene la tabla con datos de variedades predecidas
                # Añado un nuevo campo a la cabecera
                datos_tabla = [["Fecha", "Temp. Min (ºC)", "Probabilidad Helada %", "Variedad", "Nivel de Riesgo"]]
                for p in datos_variedades:
                    print(f"Dato variedad : {p}")
                    nivel = p.get("nivel_riesgo", "—")
                    prob_helada = 0.25 # Temporal
                    datos_tabla.append(
                        [
                            f"{fecha}",
                            f"{p.get("temperatura_evaluada", 0):.1f}",
                            f"{prob_helada * 100:.0f}%",
                            p.get('variedad', "-"),
                            nivel
                        ]
                    )
            elif datos_localidades:
                print(f"Datos localidades : {datos_localidades}")
                # Modifico la cabecera general
                datos_tabla = [["Fecha", "Localidad", "Provincia", "Temp. Mín (ºC)", "Temp. Max (ºC)", "Nivel de Riesgo"]]
                for p in datos_localidades:
                    datos_tabla.append(
                        [
                            f"{fecha}",
                            p.get('localidad', '-'),
                            p.get('provincia', '-'),
                            f"{p.get('temperatura_minima', 0):.1f}",
                            f"{p.get('temperatura_maxima', 0):.1f}",
                            p.get('nivel_riesgo', "-")
                        ]
                    )
            else:
                # Cabecera de la tabla general
                datos_tabla = [["Fecha", "Estado del cielo", "Tendencia Temp. General", "Precipitaciones"]]
                # Prediccion sin filtros específicos
                datos_tabla.append(
                    [
                        f"{fecha}",
                        predicciones.get("datos_meteorologicos", {}).get("estado_cielo", "-"),
                        predicciones.get("datos_meteorologicos", {}).get('tendencia_temp_general'),
                        predicciones.get("datos_meteorologicos", {}).get('precipitaciones', "-")
                    ]
                )

            # Determinar el ancho de las columnas en función del tipo de prediccion obtenida
            if datos_variedades:
                col_widths = [1.2 * inch, 1.2 * inch, 1.3 * inch, 1.5 * inch, 1.3 * inch]
            elif datos_localidades:
                col_widths = [1.0 * inch, 1.2 * inch, 1.0 * inch, 1.0 * inch, 1.0 * inch, 1.2 * inch]
            else:
                col_widths = [1.5 * inch, 1.8 * inch, 1.8 * inch, 1.7 * inch]

            tabla = Table(datos_tabla, colWidths = col_widths)
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

            if datos_variedades:
                alertas_generales = predicciones.get("alertas", [])
                for alerta in alertas_generales:
                    story.append(
                        Paragraph(
                            f"⚠ {alerta.get('mensaje', "-")} {alerta.get('recomendacion', "-")} - Nivel de alerta: {alerta.get('nivel', "-")}",
                            estilo_alerta
                        )
                    )
                
                for p in datos_variedades:
                    alertas_variedades = p.get('alertas', [])
                    for alerta in alertas_variedades:
                        story.append(
                            Paragraph(
                                f"⚠ Alerta sobre la variedad {p.get('variedad', "-")}: {alerta.get('mensaje', "-")} {alerta.get('recomendacion', "-")} - Nivel de alerta: {alerta.get('nivel', "-")}",
                                estilo_alerta
                            )
                        )
            elif datos_localidades:
                alertas_generales = predicciones.get("alertas", [])
                for alerta in alertas_generales:
                    story.append(
                        Paragraph(
                            f"⚠ {alerta.get('mensaje', "-")} {alerta.get('recomendacion', "-")} - Nivel de alerta: {alerta.get('nivel', "-")}",
                            estilo_alerta
                        )
                    )
                
                for p in datos_localidades:
                    story.append(
                        Paragraph(
                            p.get('resumen', "-"),
                            estilo_normal
                        )
                    )
            else:
                story.append(Paragraph("No se detectan periodos de riesgo alto en el horizonte analizado.", estilo_normal))
            
            riesgos_heladas_blancas = predicciones.get('riesgos_heladas_blancas', [])
            riesgos_heladas_negras = predicciones.get('riesgos_heladas_negras', [])
            if riesgos_heladas_blancas: # Incluyo información de heladas blancas y negras si existen
                for r in riesgos_heladas_blancas:
                    story.append(
                        Paragraph(
                            f"Se ha registrado un riesgo por helada blanca: {r.get('humedad', 0)} Valor de Humedad, {r.get('temperatura', 0)} Valor de Temperatura"
                        ),
                        estilo_normal
                    )
            if riesgos_heladas_negras:
                for r in riesgos_heladas_negras:
                    story.append(
                        Paragraph(
                            f"Se ha registrado un riesgo por helada negra: {r.get('humedad', 0)} Valor de Humedad, {r.get('temperatura', 0)} Valor de Temperatura"
                        ),
                        estilo_normal
                    )
            # ── Construir el PDF pasando la función de encabezado/pie ──
            doc.build(story, onFirstPage = InformeService.encabezado_pie, onLaterPages = InformeService.encabezado_pie)
            print(f"PDF generado: {NOMBRE_ARCHIVO}")
        
        except Exception as e:
            print(f"Error al generar el PDF: {e}")
            return