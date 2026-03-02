from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, PageBreak, KeepTogether
from datetime import date, datetime
from pathlib import Path
import os
import json

ruta_directorio_actual = os.getcwd()
#=== INFORMACIÓN DE ESTRUCTURA INFORME ===#
TITULO_INFORME = "Informe de Predicciones sobre Riesgos ante Plagas"
SUBTITULO_1 = "Análisis de riesgos por grupo de cultivo"
SUBTITULO_2 = "Análisis de riesgos por cultivos e información de sensores"
AUTOR = "Álvaro Mendo Martín"
FECHA = date.today().strftime("%d/%m/%Y")
NOMBRE_ARCHIVO = "reporte_riesgos_plagas.pdf"
NOMBRE_UNIVERSIDAD = "Escuela Politécnica - Cáceres"
URL_LOGO_UNIVERSIDAD = os.path.join(ruta_directorio_actual, "/assets/logouex.jpg")

#=== CONFIGURACIÓN DE COLORES ===#
COLOR_PRIMARIO    = colors.HexColor("#006414")   
COLOR_SECUNDARIO  = colors.HexColor("#462204")   
COLOR_FONDO_TABLA = colors.HexColor("#EAF4FB")   

# Colores por nivel de riesgo
COLOR_ALTA  = colors.HexColor("#F8D7DA")   
COLOR_MEDIA = colors.HexColor("#FFF3CD")   
COLOR_BAJA  = colors.HexColor("#D4EDDA")   

# Colores de texto nivel de riesgo
TEXTO_ALTA  = colors.HexColor("#721C24")
TEXTO_MEDIA = colors.HexColor("#856404")
TEXTO_BAJA  = colors.HexColor("#155724")

class InformePlagaService:
    
    @staticmethod
    def definir_color_por_riesgo(
        nivel : str
    ):
        """
        Dado el nivel de riesgos pasado por parámetros, devolverá el tipo de 
        color asociado al riesgo
        """
        nivel = nivel.upper()
        if nivel == "ALTA":
            return COLOR_ALTA, TEXTO_ALTA
        elif nivel == "MEDIA":
            return COLOR_MEDIA, TEXTO_MEDIA
        else:
            return COLOR_BAJA, TEXTO_BAJA
        
    @staticmethod
    def encabezado_pie(canva_obj, doc):
        """
        Dibuja el encabezado y el pie de págian en cada hoja del informe a generar
        """
        canva_obj.saveState()
        ancho, alto = letter

        #=== DEFINICIÓN DEL ENCABEZADO ===#
        canva_obj.setFillColor(COLOR_PRIMARIO)
        canva_obj.rect(0, alto - 60, ancho, 60, fill = True, stroke = False)

        canva_obj.setFillColor(colors.white)
        canva_obj.setFont("Helvetica-Bold", 14)
        canva_obj.drawString(1 * inch, alto - 30, TITULO_INFORME)

        canva_obj.setFont("Helvetica", 10)
        canva_obj.drawString(1 * inch, alto - 40, SUBTITULO_1)

        canva_obj.setFont("Helvetica", 9)
        canva_obj.drawRightString(ancho - 1 * inch, alto - 30, f"Actualización : {FECHA}")

        canva_obj.setStrokeColor(COLOR_SECUNDARIO)  
        canva_obj.setLineWidth(2)
        canva_obj.line(0.75 * inch, alto - 65, ancho - 0.75 * inch, alto - 65)

        #=== PIE DE PAGINA ===#
        canva_obj.setStrokeColor(COLOR_PRIMARIO)
        canva_obj.setLineWidth(1)
        canva_obj.line(0.75 * inch, 45, ancho - 0.75 * inch, 45)

        canva_obj.setFillColor(COLOR_PRIMARIO)
        canva_obj.setFont("Helvetica", 8)
        canva_obj.drawString(1 * inch, 30, f"© {date.today().year} {AUTOR}")

        canva_obj.setFont("Helvetica-Bold", 9)
        canva_obj.drawCentredString(ancho / 2, 30, f"Página {doc.page}")

        canva_obj.setFont("Helvetica", 8)
        canva_obj.drawRightString(ancho - 1 * inch, 30, "Informe de Riesgos de Plagas")
        canva_obj.restoreState()

    
    @staticmethod
    def configuracion_tabla_resumen(
        plagas: list
    ):
        cabecera = ["Nombre", "Tipo", "Agente Causante", "Riesgo"]
        col_widths = [2.1*inch, 0.8*inch, 2.5*inch, 0.9*inch]

        datos_tabla = [cabecera]
        datos_color = []

        for p in plagas:
            nivel_riesgo = p['nivel_riesgo']

            datos_color.append(
                nivel_riesgo
            )

            datos_tabla.append(
                [
                    p['nombre'],
                    p['tipo'].capitalize(),
                    p['agente_causante'],
                    nivel_riesgo
                ]
            )

        tabla = Table(datos_tabla, colWidths=col_widths, repeatRows=1)
        estilo_base = [
            # Cabecera
            ("BACKGROUND",   (0, 0), (-1, 0), COLOR_PRIMARIO),
            ("TEXTCOLOR",    (0, 0), (-1, 0), colors.white),
            ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",     (0, 0), (-1, 0), 9),
            ("ALIGN",        (0, 0), (-1, 0), "CENTER"),
            # Datos
            ("FONTNAME",     (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE",     (0, 1), (-1, -1), 7),
            ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
            ("GRID",         (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("BOX",          (0, 0), (-1, -1), 1, COLOR_PRIMARIO),
            ("TOPPADDING",   (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
            ("LEFTPADDING",  (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            # Columna nivel centrada
            ("ALIGN",        (3, 1), (3, -1), "CENTER"),
            ("FONTNAME",     (3, 1), (3, -1), "Helvetica-Bold"),
        ]
        tabla.setStyle(TableStyle(estilo_base))

        # Coloreo las filas 
        for i, nivel in enumerate(datos_color, start = 1):
            
            fondo, texto = InformePlagaService.definir_color_por_riesgo(
                nivel = nivel
            )

            tabla.setStyle(TableStyle([
                ("BACKGROUND", (3, i), (3, i), fondo),
                ("TEXTCOLOR",  (3, i), (3, i), texto),
            ])) 

        return tabla
    
    @staticmethod
    def configuracion_tabla_detalles(plaga: dict):
    
        cols_width = [1.3*inch, 1.5*inch, 2.2*inch, 1.3*inch, 0.9*inch]

        fondo, texto = InformePlagaService.definir_color_por_riesgo(
            nivel=plaga['nivel_riesgo']
        )

        estilo_celda = ParagraphStyle(
            "CeldaDetalle",
            fontName="Helvetica",
            fontSize=8,
            leading=10,
        )
        estilo_nivel = ParagraphStyle(
            "CeldaNivel",
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            alignment=1,  # CENTER
            textColor=texto,
            backColor=fondo,
        )

        cabecera = ["Agente Causante", "Momento Crítico", "Observaciones", "Más información", "Nivel Riesgo"]

        datos = [
            cabecera,
            [
                Paragraph(plaga.get('agente_causante') or '-', estilo_celda),
                Paragraph(plaga.get('momento_critico') or '-', estilo_celda),
                Paragraph(plaga.get('observaciones')   or '-', estilo_celda),
                Paragraph(plaga.get('mas_info')        or '—', estilo_celda),
                Paragraph(plaga.get('nivel_riesgo')    or '-', estilo_nivel),
            ]
        ]

        tabla = Table(data=datos, colWidths=cols_width)
        tabla.setStyle(TableStyle([
            # Cabecera
            ("BACKGROUND",    (0, 0), (-1, 0),  COLOR_PRIMARIO),
            ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
            ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
            ("FONTSIZE",      (0, 0), (-1, 0),  8),
            ("ALIGN",         (0, 0), (-1, 0),  "CENTER"),
            # Datos
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
            ("GRID",          (0, 0), (-1, -1), 0.3, colors.lightgrey),
            ("BOX",           (0, 0), (-1, -1), 0.8, colors.grey),
            ("TOPPADDING",    (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING",   (0, 0), (-1, -1), 5),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
            ("BACKGROUND",    (4, 1), (4, 1),   fondo),
        ]))

        return tabla

    @staticmethod
    def crear_informe(
        datos : dict,
    ):
        """
        Crea el informe de predicciones acumuladas sobre plagas y enfermedades

        :param datos: Lista de predicciones obtenidas
        :type datos: list[dict]
        """
        if not isinstance(datos, list):
            print("Error: datos no es una lista válida")
            return None
        
        directorio = Path(__file__).resolve().parent
        directorio.mkdir(parents = True, exist_ok = True)
        ruta_pdf = directorio / NOMBRE_ARCHIVO

        # Generación del PDF
        doc = SimpleDocTemplate(
            str(ruta_pdf),
            pagesize = letter,
            topMargin = 1.2 * inch,
            bottomMargin = 0.9 * inch,
            leftMargin = 1 * inch,
            rightMargin = 1 * inch,
            title = f"{TITULO_INFORME}",
            author = AUTOR
        )

        styles = getSampleStyleSheet()

        estilo_titulo = ParagraphStyle(
            "TituloSeccion",
            parent=styles["Heading1"],
            fontSize=13,
            textColor=COLOR_PRIMARIO,
            spaceAfter=6,
        )
        estilo_subtitulo = ParagraphStyle(
            "SubtituloSeccion",
            parent=styles["Heading2"],
            fontSize=10,
            textColor=COLOR_SECUNDARIO,
            spaceAfter=4,
            spaceBefore=10,
        )
        estilo_normal = ParagraphStyle(
            "Normal_Custom",
            parent=styles["Normal"],
            fontSize=9,
            leading=13,
            spaceAfter=4,
        )
        estilo_resumen = ParagraphStyle(
            "Resumen",
            parent=styles["Normal"],
            fontSize=8,
            textColor=colors.grey,
            leading=11,
        )

        story = []

        # ====== PORTADA / RESUMEN GLOBAL ======
        story.append(Spacer(1, 0.4 * inch))
        story.append(Paragraph(
            "INFORME DE RIESGOS DE PLAGAS Y ENFERMEDADES",
            ParagraphStyle("TituloPrincipal", parent=estilo_titulo, fontSize=16, alignment=1)
        ))
        story.append(Spacer(1, 0.15 * inch))
        total_cultivos = len(datos)
        total_plagas = sum(len(c.get("plagas", [])) for c in datos)
        print(total_plagas)
        plagas_alta   = sum(1 for c in datos for p in c.get("plagas", []) if p.get("nivel_riesgo", "").upper() == "ALTA")
        plagas_media  = sum(1 for c in datos for p in c.get("plagas", []) if p.get("nivel_riesgo", "").upper() == "MEDIA")
        plagas_baja   = sum(1 for c in datos for p in c.get("plagas", []) if p.get("nivel_riesgo", "").upper() == "BAJA")
        resumen_text = (
            f"<b>Fecha del informe:</b> {FECHA}<br/>"
            f"<b>Cultivos analizados:</b> {total_cultivos}<br/>"
            f"<b>Total plagas/enfermedades:</b> {total_plagas}<br/>"
            f"<b>Nivel ALTO:</b> {plagas_alta} &nbsp;&nbsp; "
            f"<b>Nivel MEDIO:</b> {plagas_media} &nbsp;&nbsp; "
            f"<b>Nivel BAJO:</b> {plagas_baja}"
        )
        story.append(Paragraph(resumen_text, estilo_normal))
        story.append(HRFlowable(width="100%", thickness=1.5, color=COLOR_SECUNDARIO))
        story.append(Spacer(1, 0.1 * inch))

        # Leyenda de colores
        leyenda = (
            '<font color="#721C24"><b>■ ALTA</b></font>  &nbsp;&nbsp;'
            '<font color="#856404"><b>■ MEDIA</b></font>  &nbsp;&nbsp;'
            '<font color="#155724"><b>■ BAJA</b></font>'
        )
        story.append(Paragraph(leyenda, estilo_resumen))
        story.append(Spacer(1, 0.2 * inch))
        # ====== SECCIÓN POR CULTIVO ======
        for idx, cultivo_data in enumerate(datos, start=1):
            cultivo = cultivo_data.get("cultivo", {})
            nombre_cultivo = cultivo.get("nombre", f"Cultivo {idx}").upper()
            grupo_cultivo  = cultivo.get("grupo", "").capitalize()
            plagas = cultivo_data.get("plagas", [])

            if idx > 1:
                story.append(PageBreak())

            story.append(Paragraph(
                f"{idx}. CULTIVO: {nombre_cultivo} ({grupo_cultivo})",
                estilo_titulo
            ))
            story.append(HRFlowable(width="100%", thickness=1, color=COLOR_PRIMARIO))
            story.append(Spacer(1, 0.1 * inch))

            n_alta  = sum(1 for p in plagas if p.get("nivel_riesgo", "").upper() == "ALTA")
            n_media = sum(1 for p in plagas if p.get("nivel_riesgo", "").upper() == "MEDIA")
            n_baja  = sum(1 for p in plagas if p.get("nivel_riesgo", "").upper() == "BAJA")
            story.append(Paragraph(
                f"Total amenazas identificadas: <b>{len(plagas)}</b> &nbsp;|&nbsp; "
                f"Alta: <b>{n_alta}</b> &nbsp;|&nbsp; Media: <b>{n_media}</b> &nbsp;|&nbsp; Baja: <b>{n_baja}</b>",
                estilo_normal
            ))
            story.append(Spacer(1, 0.1 * inch))

            # ---- Tabla resumen ----
            story.append(Paragraph("Tabla resumen", estilo_subtitulo))
            tabla_resumen = InformePlagaService.configuracion_tabla_resumen(plagas)
            story.append(tabla_resumen)
            story.append(Spacer(1, 0.25 * inch))

            # ---- Fichas detalladas por prioridad (ALTA primero) ----
            story.append(Paragraph("Fichas de plaga/enfermedad detalladas por nivel de riesgo", estilo_subtitulo))
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
            story.append(Spacer(1, 0.05 * inch))

            orden_nivel = {"ALTA": 0, "MEDIA": 1, "BAJA": 2}
            plagas_ordenadas = sorted(plagas, key=lambda p: orden_nivel.get(p.get("nivel_riesgo", "BAJA").upper(), 3))

            for plaga in plagas_ordenadas:
                nombre_plaga = plaga.get("nombre", "-")
                tipo_plaga   = plaga.get("tipo", "-").capitalize()
                nivel        = plaga.get("nivel_riesgo", "-").upper()
                fondo, texto = InformePlagaService.definir_color_por_riesgo(plaga.get('nivel_riesgo', "-").upper())

                titulo_plaga = Paragraph(
                    f"<b>{nombre_plaga}</b>  —  {tipo_plaga}  —  Riesgo: {nivel}",
                    ParagraphStyle(
                        "TituloPlaga",
                        parent=estilo_normal,
                        textColor=texto,
                        backColor=fondo,
                        borderPad=4,
                        spaceAfter=2,
                        spaceBefore=8,
                    )
                )
                tabla_detalle = InformePlagaService.configuracion_tabla_detalles(plaga)

                story.append(KeepTogether([titulo_plaga, tabla_detalle]))
                story.append(Spacer(1, 0.1 * inch))

        # Construir PDF
        doc.build(
            story,
            onFirstPage = InformePlagaService.encabezado_pie,
            onLaterPages = InformePlagaService.encabezado_pie,
        )