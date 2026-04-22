from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, PageBreak, KeepTogether
from datetime import date, datetime, timedelta
from pathlib import Path
import os

ruta_directorio_actual = os.getcwd()

#=== INFORMACIÓN DE ESTRUCTURA INFORME ===#
TITULO_INFORME = "Informe de Predicciones Dinámicas sobre Riesgos ante Plagas"
SUBTITULO_1 = "Análisis temporal de riesgos por cultivo"
SUBTITULO_2 = "Evolución diaria de condiciones favorables para plagas"
AUTOR = "Álvaro Mendo Martín"
NOMBRE_ARCHIVO = "reporte_riesgos_plagas_dinamico.pdf"
NOMBRE_UNIVERSIDAD = "Escuela Politécnica - Cáceres"
URL_LOGO_UNIVERSIDAD = os.path.join(ruta_directorio_actual, "/assets/logouex.jpg")

#=== CONFIGURACIÓN DE COLORES ===#
COLOR_PRIMARIO    = colors.HexColor("#006414")   
COLOR_SECUNDARIO  = colors.HexColor("#462204")   
COLOR_FONDO_TABLA = colors.HexColor("#EAF4FB")   

# Colores por nivel de riesgo
COLOR_CRITICA  = colors.HexColor("#F8D7DA")   
COLOR_PREVENTIVA = colors.HexColor("#FFF3CD")   
COLOR_SIN_RIESGO  = colors.HexColor("#D4EDDA")   

# Colores de texto nivel de riesgo
TEXTO_CRITICA  = colors.HexColor("#721C24")
TEXTO_PREVENTIVA = colors.HexColor("#856404")
TEXTO_SIN_RIESGO  = colors.HexColor("#155724")

# Mapeo de niveles
MAP_NIVEL_COLOR = {
    "critica": (COLOR_CRITICA, TEXTO_CRITICA),
    "preventiva": (COLOR_PREVENTIVA, TEXTO_PREVENTIVA),
    "sin_riesgo": (COLOR_SIN_RIESGO, TEXTO_SIN_RIESGO)
}

class InformePlagaEstimadaService:
    """Servicio para generar informes de plagas estimadas (series temporales)"""
    
    @staticmethod
    def definir_color_por_riesgo(nivel: str):
        """
        Dado el nivel de riesgos pasado por parámetros, devolverá el tipo de 
        color asociado al riesgo
        """
        nivel = nivel.lower()
        return MAP_NIVEL_COLOR.get(nivel, (COLOR_SIN_RIESGO, TEXTO_SIN_RIESGO))
    
    @staticmethod
    def encabezado_pie(canva_obj, doc):
        """
        Dibuja el encabezado y el pie de página en cada hoja del informe a generar
        """
        canva_obj.saveState()
        ancho, alto = letter

        #=== DEFINICIÓN DEL ENCABEZADO ===#
        canva_obj.setFillColor(COLOR_PRIMARIO)
        canva_obj.rect(0, alto - 60, ancho, 60, fill=True, stroke=False)

        canva_obj.setFillColor(colors.white)
        canva_obj.setFont("Helvetica-Bold", 14)
        canva_obj.drawString(1 * inch, alto - 30, TITULO_INFORME)

        canva_obj.setFont("Helvetica", 10)
        canva_obj.drawString(1 * inch, alto - 40, SUBTITULO_1)

        canva_obj.setFont("Helvetica", 9)
        fecha_actual = date.today().strftime("%d/%m/%Y")
        canva_obj.drawRightString(ancho - 1 * inch, alto - 30, f"Generación: {fecha_actual}")

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
        canva_obj.drawRightString(ancho - 1 * inch, 30, SUBTITULO_2)
        canva_obj.restoreState()

    @staticmethod
    def crear_tabla_resumen_plagas(plagas_evaluadas: list) -> Table:
        """
        Crea tabla resumen de todas las plagas con estadísticas generales
        """
        cabecera = ["Plaga", "Tipo", "Días Crítica", "Días Preventiva", "Días Sin Riesgo", "Total Días"]
        col_widths = [2*inch, 0.8*inch, 1*inch, 1.2*inch, 1.2*inch, 0.8*inch]

        datos_tabla = [cabecera]
        
        for plaga in plagas_evaluadas:
            datos = plaga['datos_probabilidad']
            total_dias = len(datos)
            
            # Contar días por nivel de riesgo
            dias_critica = sum(1 for d in datos if d['nivel_riesgo'].lower() == 'critica')
            dias_preventiva = sum(1 for d in datos if d['nivel_riesgo'].lower() == 'preventiva')
            dias_sin_riesgo = sum(1 for d in datos if d['nivel_riesgo'].lower() == 'sin_riesgo')
            
            datos_tabla.append([
                plaga['nombre'],
                plaga['tipo'].capitalize(),
                str(dias_critica),
                str(dias_preventiva),
                str(dias_sin_riesgo),
                str(total_dias)
            ])
        
        tabla = Table(datos_tabla, colWidths=col_widths, repeatRows=1)
        estilo_base = [
            # Cabecera
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_PRIMARIO),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            # Datos
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 7),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("BOX", (0, 0), (-1, -1), 1, COLOR_PRIMARIO),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]
        tabla.setStyle(TableStyle(estilo_base))
        
        # Colorear celdas según nivel de riesgo
        for i in range(1, len(datos_tabla)):
            # Columna de días crítica (índice 2)
            fondo_critica, _ = InformePlagaEstimadaService.definir_color_por_riesgo("critica")
            tabla.setStyle(TableStyle([("BACKGROUND", (2, i), (2, i), fondo_critica)]))
            
            # Columna de días preventiva (índice 3)
            fondo_preventiva, _ = InformePlagaEstimadaService.definir_color_por_riesgo("preventiva")
            tabla.setStyle(TableStyle([("BACKGROUND", (3, i), (3, i), fondo_preventiva)]))
            
            # Columna de días sin riesgo (índice 4)
            fondo_sin_riesgo, _ = InformePlagaEstimadaService.definir_color_por_riesgo("sin_riesgo")
            tabla.setStyle(TableStyle([("BACKGROUND", (4, i), (4, i), fondo_sin_riesgo)]))
        
        return tabla
    
    @staticmethod
    def crear_tabla_evolucion_diaria(datos_probabilidad: list, nombre_plaga: str) -> Table:
        """
        Crea tabla de evolución diaria de riesgos para una plaga específica
        """
        # Limitar a últimos 14 días si hay muchos para evitar páginas excesivas
        if len(datos_probabilidad) > 21:
            datos_mostrar = datos_probabilidad[-21:]  # Últimos 21 días
        else:
            datos_mostrar = datos_probabilidad
        
        cabecera = ["Fecha", "Riesgo", "Condiciones\nCumplidas", "Condiciones\nPendientes"]
        # Ajustar anchos dinámicamente
        col_widths = [0.8*inch, 0.9*inch, 2.2*inch, 2.2*inch]
        
        datos_tabla = [cabecera]
        
        estilo_celda = ParagraphStyle(
            "CeldaDetalle",
            fontName="Helvetica",
            fontSize=7,
            leading=9,
        )
        
        for registro in datos_mostrar:
            fecha = registro['fecha']
            nivel = registro['nivel_riesgo'].upper()
            fondo, texto_color = InformePlagaEstimadaService.definir_color_por_riesgo(registro['nivel_riesgo'])
            
            # Formatear condiciones
            cumplidas = "<br/>".join(registro.get('condiciones_cumplidas', [])) or "-"
            pendientes = "<br/>".join(registro.get('condiciones_pendientes', [])) or "-"
            
            # Celda de nivel con formato especial
            estilo_nivel = ParagraphStyle(
                "NivelStyle",
                parent=estilo_celda,
                alignment=1,  # CENTER
                textColor=texto_color,
                backColor=fondo,
                fontSize=8,
                fontName="Helvetica-Bold"
            )
            
            datos_tabla.append([
                Paragraph(fecha, estilo_celda),
                Paragraph(nivel, estilo_nivel),
                Paragraph(cumplidas, estilo_celda),
                Paragraph(pendientes, estilo_celda)
            ])
        
        tabla = Table(datos_tabla, colWidths=col_widths, repeatRows=1)
        
        estilo_tabla = [
            # Cabecera
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_PRIMARIO),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            # Datos
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.lightgrey),
            ("BOX", (0, 0), (-1, -1), 0.8, colors.grey),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ]
        
        # Aplicar colores de fondo por fila según nivel
        for i in range(1, len(datos_tabla)):
            nivel_fila = datos_mostrar[i-1]['nivel_riesgo']
            fondo, _ = InformePlagaEstimadaService.definir_color_por_riesgo(nivel_fila)
            estilo_tabla.append(("BACKGROUND", (1, i), (1, i), fondo))
        
        tabla.setStyle(TableStyle(estilo_tabla))
        return tabla
    
    @staticmethod
    def crear_grafico_evolucion_temporal(datos_probabilidad: list, nombre_plaga: str) -> Paragraph:
        """
        Crea una representación visual simple de la evolución de riesgos usando caracteres
        Nota: Para gráficos más avanzados, se podría integrar matplotlib
        """
        # Crear una línea de tiempo visual simple
        niveles_map = {
            "critica": "█",
            "preventiva": "▓",
            "sin_riesgo": "░"
        }
        
        # Tomar muestra representativa (máximo 30 días)
        if len(datos_probabilidad) > 30:
            step = len(datos_probabilidad) // 30
            datos_muestra = datos_probabilidad[::step][:30]
        else:
            datos_muestra = datos_probabilidad
        
        # Construir representación visual
        visual_chars = []
        fechas_labels = []
        
        for registro in datos_muestra:
            nivel = registro['nivel_riesgo'].lower()
            visual_chars.append(niveles_map.get(nivel, "?"))
            # Mostrar solo algunas fechas para no saturar
            if len(fechas_labels) % 5 == 0 or len(fechas_labels) == len(datos_muestra) - 1:
                fechas_labels.append(registro['fecha'][5:])  # MM-DD
            else:
                fechas_labels.append("")
        
        visual_line = "".join(visual_chars)
        
        # Crear leyenda
        leyenda = """
        <font color="#721C24"><b>█ Crítica</b></font>  
        <font color="#856404"><b>▓ Preventiva</b></font>  
        <font color="#155724"><b>░ Sin Riesgo</b></font>
        """
        
        estilo_grafico = ParagraphStyle(
            "GraficoStyle",
            fontName="Courier",
            fontSize=8,
            leading=12,
            fontFamily="Courier"
        )
        
        contenido = f"""
        <b>Evolución temporal de {nombre_plaga}:</b><br/>
        <font face="Courier" size="8">{visual_line}</font><br/>
        """
        
        # Añadir etiquetas de fechas
        if fechas_labels:
            fecha_line = " ".join(f"{label:^3}" for label in fechas_labels)
            contenido += f'<font face="Courier" size="6">{fecha_line}</font><br/><br/>'
        
        contenido += f"<font size='7'>{leyenda}</font>"
        
        return Paragraph(contenido, estilo_grafico)
    
    @staticmethod
    def crear_informe_estimado(datos: dict):
        """
        Crea el informe de predicciones dinámicas sobre plagas (series temporales)
        
        :param datos: Diccionario con estructura:
            {
                "cultivo": "Tomate",
                "fecha_inicio": "2026-04-01",
                "fecha_final": "2026-04-20",
                "plagas_evaluadas": [...]
            }
        """

        if not datos or 'plagas_evaluadas' not in datos:
            print("Error: datos no contiene la estructura esperada")
            return None
        
        # Crear directorio de reports si no existe
        directorio = Path(__file__).resolve().parent
        directorio_reports = directorio / 'reports'
        directorio_reports.mkdir(parents=True, exist_ok=True)
        
        # Generar nombre de archivo con timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_archivo = f"reporte_riesgos_{datos['cultivo'].lower()}_{timestamp}.pdf"
        ruta_pdf = directorio_reports / nombre_archivo
        
        # Configuración del documento
        doc = SimpleDocTemplate(
            str(ruta_pdf),
            pagesize=letter,
            topMargin=1.2 * inch,
            bottomMargin=0.9 * inch,
            leftMargin=0.8 * inch,
            rightMargin=0.8 * inch,
            title=f"{TITULO_INFORME} - {datos['cultivo']}",
            author=AUTOR
        )
        
        styles = getSampleStyleSheet()
        
        # Estilos personalizados
        estilo_titulo_principal = ParagraphStyle(
            "TituloPrincipal",
            parent=styles["Heading1"],
            fontSize=14,
            textColor=COLOR_PRIMARIO,
            alignment=1,  # CENTER
            spaceAfter=12,
        )
        
        estilo_titulo = ParagraphStyle(
            "TituloSeccion",
            parent=styles["Heading1"],
            fontSize=12,
            textColor=COLOR_PRIMARIO,
            spaceAfter=6,
            spaceBefore=6,
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
        story.append(Spacer(1, 0.3 * inch))
        story.append(Paragraph(
            f"INFORME DE RIESGOS DE PLAGAS<br/>CULTIVO: {datos['cultivo'].upper()}",
            ParagraphStyle("TituloPrincipalGrande", parent=estilo_titulo_principal, fontSize=16)
        ))
        story.append(Spacer(1, 0.1 * inch))
        
        # Información del período
        periodo_texto = f"""
        <b>Período analizado:</b> {datos['fecha_inicio']} → {datos['fecha_final']}<br/>
        <b>Total de días:</b> {
            (datetime.strptime(datos['fecha_final'], '%Y-%m-%d') - 
             datetime.strptime(datos['fecha_inicio'], '%Y-%m-%d')).days + 1
        } días<br/>
        <b>Plagas evaluadas:</b> {len(datos['plagas_evaluadas'])}
        """
        story.append(Paragraph(periodo_texto, estilo_normal))
        story.append(HRFlowable(width="100%", thickness=1.5, color=COLOR_SECUNDARIO))
        story.append(Spacer(1, 0.15 * inch))
        
        # Estadísticas globales
        total_registros = sum(len(p['datos_probabilidad']) for p in datos['plagas_evaluadas'])
        total_critica = sum(
            1 for p in datos['plagas_evaluadas'] 
            for d in p['datos_probabilidad'] 
            if d['nivel_riesgo'].lower() == 'critica'
        )
        total_preventiva = sum(
            1 for p in datos['plagas_evaluadas'] 
            for d in p['datos_probabilidad'] 
            if d['nivel_riesgo'].lower() == 'preventiva'
        )
        
        stats_text = f"""
        <b>Resumen de alertas:</b><br/>
        • Alertas CRÍTICAS: {total_critica}<br/>
        • Alertas PREVENTIVAS: {total_preventiva}<br/>
        • Sin riesgo: {total_registros - total_critica - total_preventiva}
        """
        story.append(Paragraph(stats_text, estilo_normal))
        story.append(Spacer(1, 0.1 * inch))
        
        # Leyenda de colores
        leyenda = """
        <font color="#721C24"><b>■ CRÍTICA</b></font>  &nbsp;&nbsp;
        <font color="#856404"><b>■ PREVENTIVA</b></font>  &nbsp;&nbsp;
        <font color="#155724"><b>■ SIN RIESGO</b></font>
        """
        story.append(Paragraph(leyenda, estilo_resumen))
        story.append(Spacer(1, 0.2 * inch))
        
        # ====== TABLA RESUMEN DE PLAGAS ======
        story.append(Paragraph("RESUMEN DE PLAGAS EVALUADAS", estilo_titulo))
        story.append(HRFlowable(width="100%", thickness=1, color=COLOR_PRIMARIO))
        story.append(Spacer(1, 0.1 * inch))
        
        tabla_resumen = InformePlagaEstimadaService.crear_tabla_resumen_plagas(
            datos['plagas_evaluadas']
        )
        story.append(tabla_resumen)
        story.append(PageBreak())
        
        # ====== DETALLE POR PLAGA ======
        story.append(Paragraph("ANÁLISIS DETALLADO POR PLAGA", estilo_titulo))
        story.append(HRFlowable(width="100%", thickness=1, color=COLOR_PRIMARIO))
        story.append(Spacer(1, 0.1 * inch))
        
        for idx, plaga in enumerate(datos['plagas_evaluadas'], start=1):
            nombre_plaga = plaga['nombre']
            tipo_plaga = plaga['tipo'].capitalize()
            datos_probabilidad = plaga['datos_probabilidad']
            
            # Título de la plaga
            story.append(Paragraph(
                f"{idx}. {nombre_plaga} <font size='8'>({tipo_plaga})</font>",
                estilo_subtitulo
            ))
            
            # Estadísticas de esta plaga
            dias_critica = sum(1 for d in datos_probabilidad if d['nivel_riesgo'].lower() == 'critica')
            dias_preventiva = sum(1 for d in datos_probabilidad if d['nivel_riesgo'].lower() == 'preventiva')
            dias_sin = len(datos_probabilidad) - dias_critica - dias_preventiva
            
            stats_plaga = f"""
            <b>Días con alerta crítica:</b> {dias_critica} &nbsp;|&nbsp;
            <b>Días con alerta preventiva:</b> {dias_preventiva} &nbsp;|&nbsp;
            <b>Días sin riesgo:</b> {dias_sin}
            """
            story.append(Paragraph(stats_plaga, estilo_normal))
            story.append(Spacer(1, 0.05 * inch))
            
            # Gráfico de evolución (si hay suficientes datos)
            if len(datos_probabilidad) >= 5:
                try:
                    grafico = InformePlagaEstimadaService.crear_grafico_evolucion_temporal(
                        datos_probabilidad, nombre_plaga
                    )
                    story.append(grafico)
                    story.append(Spacer(1, 0.1 * inch))
                except:
                    pass  # Si falla la generación del gráfico, continuar
            
            # Tabla detallada de evolución
            story.append(Paragraph("Evolución diaria:", estilo_normal))
            tabla_evolucion = InformePlagaEstimadaService.crear_tabla_evolucion_diaria(
                datos_probabilidad, nombre_plaga
            )
            story.append(tabla_evolucion)
            
            # Añadir salto de página después de cada plaga excepto la última
            if idx < len(datos['plagas_evaluadas']):
                story.append(PageBreak())
            else:
                story.append(Spacer(1, 0.2 * inch))
        
        # ====== NOTA FINAL ======
        story.append(HRFlowable(width="100%", thickness=1, color=COLOR_SECUNDARIO))
        nota_final = """
        <font size="7" color="gray">
        <b>Nota:</b> Este informe se ha generado automáticamente basado en los datos de sensores disponibles 
        y modelos predictivos de plagas. Las alertas CRÍTICAS indican condiciones favorables para el desarrollo 
        de la plaga. Las alertas PREVENTIVAS sugieren monitoreo continuo. Consulte siempre a un especialista 
        para la toma de decisiones de manejo integrado de plagas.
        </font>
        """
        story.append(Paragraph(nota_final, estilo_resumen))
        
        # Construir PDF
        doc.build(
            story,
            onFirstPage=InformePlagaEstimadaService.encabezado_pie,
            onLaterPages=InformePlagaEstimadaService.encabezado_pie,
        )