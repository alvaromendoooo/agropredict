from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, PageBreak, KeepTogether
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.widgets.markers import makeMarker
from reportlab.pdfgen import canvas
from datetime import date, datetime, timedelta
from pathlib import Path
import os
import json


ruta_directorio_actual = os.getcwd()
#=== INFORMACIÓN DE ESTRUCTURA INFORME ===#
TITULO_INFORME = "Informe de Predicciones sobre Riesgos de Helada"
SUBTITULO = "Predicciones Meteorológicas Automatizadas - Histórico"
AUTOR = "Álvaro Mendo Martín"
FECHA = date.today().strftime("%d/%m/%Y")
NOMBRE_ARCHIVO = f"reporte_riesgos_heladas_acumulado.pdf"
NOMBRE_UNIVERSIDAD = "Escuela Politécnica - Cáceres"
URL_LOGO_UNIVERSIDAD = os.path.join(ruta_directorio_actual, "/assets/logouex.jpg")

#=== CONFIGURACION COLORES ===#
COLOR_PRIMARIO = colors.HexColor("#006414")
COLOR_SECUNDARIO = colors.HexColor("#462204")
COLOR_FONDO_TABLA = colors.HexColor("#EAF4FB")
COLOR_ACENTO = colors.red
COLOR_HOY = colors.HexColor("#FFF3CD")  # Amarillo claro para destacar hoy
COLOR_NUEVO = colors.HexColor("#D4EDDA")  # Verde claro para nuevas predicciones

class InformeService():
    
    # Ruta para el archivo de metadatos
    METADATA_FILE = "informe_metadata.json"
    
    @staticmethod
    def _cargar_metadata(directorio):
        """Carga los metadatos del informe existente"""
        metadata_path = directorio / InformeService.METADATA_FILE
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                return json.load(f)
        return {
            "fechas_incluidas": [],
            "ultima_actualizacion": None,
            "total_entradas": 0,
            "tipo_datos": []
        }
    
    @staticmethod
    def _guardar_metadata(directorio, metadata):
        """Guarda los metadatos del informe"""
        metadata_path = directorio / InformeService.METADATA_FILE
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
    
    @staticmethod
    def _extraer_datos_para_tabla(predicciones, fecha_str):
        """
        Extrae los datos relevantes de la predicción para la tabla acumulativa
        """
        filas = []

        datos_variedades = predicciones.get('evaluaciones_variedades', {})
        print(type(datos_variedades))
        # Determinar el tipo de predicción
        if datos_variedades is not None:
            datos = datos_variedades.get('evaluaciones')
            for p in datos:
                filas.append({
                    'fecha': fecha_str,
                    'tipo': 'variedad',
                    'nombre': p.get('variedad', '-'),
                    'temp_min': p.get('temperatura_evaluada', 0),
                    'temp_max': None,            
                    'nivel': p.get('nivel_riesgo', '-'),
                    'porcentaje_riesgo': p.get('porcentaje_riesgo', 0),
                    'localidad': None,
                    'provincia': None,
                    'altitud': None
                })
                
        elif predicciones.get('evaluacion_localidades', {}).get('evaluaciones', []) is not None:
            datos = predicciones['evaluacion_localidades']['evaluaciones']
            print("entro")
            for p in datos:
                filas.append({
                    'fecha': fecha_str,
                    'tipo': 'localidad',
                    'nombre': p.get('localidad', '-'),
                    'temp_min': p.get('temperatura_minima', 0),
                    'temp_max': p.get('temperatura_maxima', 0),
                    'nivel': p.get('nivel_riesgo', '-'),
                    'porcentaje_riesgo': p.get('porcentaje_riesgo', 0),
                    'localidad': p.get('localidad'),
                    'provincia': p.get('provincia'),
                    'altitud': p.get('altitud_metros')
                })
        else:
            # Datos generales
            filas.append({
                'fecha': fecha_str,
                'tipo': 'general',
                'nombre': 'Predicción General',
                'temp_min': None,
                'temp_max': None,
                'nivel': predicciones.get('nivel', '—'),
                'porcentaje_riesgo': predicciones.get('porcentaje_riesgo', 0),
                'localidad': None,
                'provincia': None,
                'altitud': None,
                'estado_cielo': predicciones.get('datos_meteorologicos', {}).get('estado_cielo', '-'),
                'precipitaciones': predicciones.get('datos_meteorologicos', {}).get('precipitaciones', '-')
            })
        
        return filas
    
    def _generar_grafico(data: list, is_cultivo: bool):
        d = Drawing(400, 200)

        # Extraigo fechas únicas y mantener el orden
        fechas = list(dict.fromkeys(dato['fecha'] for dato in data))

        # Extraigo nombres únicos (para series)
        etiquetas = list(dict.fromkeys(
            dato['nombre'] 
            for dato in data 
            if not is_cultivo or (is_cultivo and dato.get('tipo') == 'variedad')
        ))

        # Construyo los datos para cada serie
        series = []
        for nombre in etiquetas:
            serie = []
            for fecha in fechas:
                encontrado = next(
                    (d['porcentaje_riesgo'] for d in data 
                    if d['nombre'] == nombre and d['fecha'] == fecha),
                    0
                )
                serie.append(encontrado)
            series.append(serie)

        # Si solo hay una fecha, duplicamos para que la línea se dibuje
        if len(fechas) == 1:
            fechas.append(fechas[0])
            for serie in series:
                serie.append(serie[0])

        # Crear gráfico
        lc = HorizontalLineChart()
        lc.x = 50
        lc.y = 50
        lc.height = 125
        lc.width = 300
        lc.data = series
        lc.joinedLines = 1
        lc.fillColor = colors.white
        lc.categoryAxis.categoryNames = fechas
        lc.categoryAxis.labels.boxAnchor = 'n'
        lc.valueAxis.valueMin = 0
        lc.valueAxis.valueMax = 100
        lc.valueAxis.valueSteps = [5, 15, 25, 50, 75, 100]

        # Configurar líneas
        for i, line in enumerate(lc.lines):
            line.strokeWidth = 2 if i == 0 else 1.5
            line.symbol = makeMarker('Circle')  # Siempre dibuja un punto también

        from reportlab.graphics.charts.legends import LineLegend

        # Leyenda
        legend = LineLegend()
        legend.fontSize = 8
        legend.alignment = 'right'
        legend.x = 0
        legend.y = 0
        legend.columnMaximum = 2
        legend.fontName = 'Helvetica'
        color_pairs = [(lc.lines[i].strokeColor, etiquetas[i]) for i in range(len(series))]
        legend.colorNamePairs = color_pairs
        print(f"LC : {lc}")
        d.add(lc)
        d.add(legend)
        return d
    
    @staticmethod
    def _generar_tabla_historica(historial_datos):
        """
        Genera una tabla con todo el historial de predicciones
        """
        if not historial_datos:
            return None
        
        # Determinar el tipo de datos predominante
        tipos = set([d['tipo'] for d in historial_datos])
        
        if 'variedad' in tipos:
            # Tabla para variedades
            cabecera = ["Fecha", "Variedad", "Temp. Min", "Nivel", "Riesgo %"]
            datos_tabla = [cabecera]
            
            for d in historial_datos:
                if d['tipo'] == 'variedad':
                    datos_tabla.append([
                        d['fecha'],
                        d['nombre'],
                        f"{d['temp_min']:.1f}°C" if d['temp_min'] else '-',
                        d['nivel'].upper() if d['nivel'] else '-',
                        f"{d['porcentaje_riesgo']:.0f}%"
                    ])
            
            col_widths = [1.2*inch, 1.5*inch, 0.9*inch, 1.0*inch, 1.0*inch]
            
        elif 'localidad' in tipos:
            # Tabla para localidades
            cabecera = ["Fecha", "Localidad", "Provincia", "Temp. Min", "Temp. Max", "Nivel", "Riesgo %"]
            datos_tabla = [cabecera]
            
            for d in historial_datos:
                if d['tipo'] == 'localidad':
                    datos_tabla.append([
                        d['fecha'],
                        d['localidad'],
                        d['provincia'],
                        f"{d['temp_min']:.1f}°C",
                        f"{d['temp_max']:.1f}°C" if d['temp_max'] else '-',
                        d['nivel'].upper() if d['nivel'] else '-',
                        f"{d['porcentaje_riesgo']:.0f}%"
                    ])
            
            col_widths = [1.0*inch, 1.2*inch, 1.0*inch, 0.9*inch, 0.9*inch, 1.0*inch, 0.8*inch]
            
        else:
            # Tabla para datos generales
            cabecera = ["Fecha", "Estado Cielo", "Precipitaciones", "Nivel", "Riesgo %"]
            datos_tabla = [cabecera]
            
            for d in historial_datos:
                if d['tipo'] == 'general':
                    datos_tabla.append([
                        d['fecha'],
                        d.get('estado_cielo', '-'),
                        d.get('precipitaciones', '-'),
                        d['nivel'].upper() if d['nivel'] else '-',
                        f"{d['porcentaje_riesgo']:.0f}%"
                    ])
            
            col_widths = [1.2*inch, 2.0*inch, 1.5*inch, 1.2*inch, 0.9*inch]
        
        tabla = Table(datos_tabla, colWidths=col_widths, repeatRows=1)
        tabla.setStyle(TableStyle([
            # Cabecera
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_PRIMARIO),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            # Filas de datos
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
            ("ALIGN", (1, 1), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("BOX", (0, 0), (-1, -1), 1, COLOR_PRIMARIO),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        
        # Colorear filas nuevas (últimas 24h)
        hoy = date.today().strftime("%d/%m/%Y")
        ayer = (date.today() - timedelta(days=1)).strftime("%d/%m/%Y")
        
        for i, fila in enumerate(datos_tabla[1:], start=1):
            if fila[0] == hoy:
                tabla.setStyle(TableStyle([
                    ('BACKGROUND', (0, i), (-1, i), COLOR_HOY),
                ]))
            elif fila[0] not in [hoy, ayer]:  # Datos antiguos
                # Degradado de color según antigüedad (más claro cuanto más antiguo)
                alpha = max(0.85, 1.0 - (i * 0.02))
                color_fondo = colors.Color(0.95, 0.95, 0.95, alpha=alpha)
                tabla.setStyle(TableStyle([
                    ('BACKGROUND', (0, i), (-1, i), color_fondo),
                ]))
        
        return tabla
    
    @staticmethod
    def encabezado_pie(canvas_obj, doc):
        """
        Dibuja el encabezado y el pie de pagina definido en cada una de las páginas del documento.
        """
        canvas_obj.saveState()
        ancho, alto = letter

        #=== DEFINICION DEL ENCABEZADO ===#
        canvas_obj.setFillColor(COLOR_PRIMARIO)
        canvas_obj.rect(0, alto - 60, ancho, 60, fill=True, stroke=False)

        canvas_obj.setFillColor(colors.white)
        canvas_obj.setFont("Helvetica-Bold", 14)
        canvas_obj.drawString(1 * inch, alto - 30, TITULO_INFORME)

        canvas_obj.setFont("Helvetica", 10)
        canvas_obj.drawString(1 * inch, alto - 40, SUBTITULO)

        canvas_obj.setFont("Helvetica", 9)
        canvas_obj.drawRightString(ancho - 1 * inch, alto - 30, f"Actualización: {FECHA}")
        
        # Mostrar número de entradas históricas
        if hasattr(doc, 'total_entradas'):
            canvas_obj.drawRightString(ancho - 1 * inch, alto - 48, f"Registros: {doc.total_entradas}")

        canvas_obj.setStrokeColor(COLOR_SECUNDARIO)
        canvas_obj.setLineWidth(2)
        canvas_obj.line(0.75 * inch, alto - 65, ancho - 0.75 * inch, alto - 65)

        #=== PIE DE PAGINA ===#
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
    def crear_informe(
        predicciones: dict, 
        acumular: bool = True, 
        is_cultivo : bool = True):
        """
        Crea o actualiza un informe acumulativo de predicciones
        
        :param predicciones: Nuevas predicciones a añadir
        :param acumular: Si es True, acumula en el informe existente
        """
        if not isinstance(predicciones, dict):
            print("Error: predicciones no es un diccionario válido")
            return

        directorio = Path(__file__).resolve().parent
        directorio.mkdir(parents=True, exist_ok=True)
        ruta_pdf = directorio / NOMBRE_ARCHIVO
        
        # Cargar metadatos existentes
        metadata = InformeService._cargar_metadata(directorio)
        
        # Fecha de esta predicción
        fecha_prediccion = predicciones.get("contexto", {}).get("fecha_generacion", "")
        if fecha_prediccion:
            fecha_prediccion = datetime.fromisoformat(fecha_prediccion).strftime("%d/%m/%Y")
        else:
            fecha_prediccion = FECHA
        
        # Extraer datos para la tabla
        nuevas_filas = InformeService._extraer_datos_para_tabla(predicciones, fecha_prediccion)
        
        if acumular and ruta_pdf.exists():
            # Intentar leer el historial existente del PDF (simplificado)
            # En una implementación real, podrías guardar los datos en un archivo JSON
            historial_path = directorio / "historial_datos.json"
            if historial_path.exists():
                with open(historial_path, 'r') as f:
                    historial_datos = json.load(f)
            else:
                historial_datos = []
            
            # Añadir nuevas filas si no existen ya para esta fecha/tipo
            fechas_existentes = set([(d['fecha'], d['tipo'], d['nombre']) for d in historial_datos])
            for fila in nuevas_filas:
                clave = (fila['fecha'], fila['tipo'], fila['nombre'])
                if clave not in fechas_existentes:
                    historial_datos.append(fila)
            
            # Guardar historial actualizado
            with open(historial_path, 'w') as f:
                json.dump(historial_datos, f, indent=2, default=str)
            
            # Actualizar metadatos
            if fecha_prediccion not in metadata['fechas_incluidas']:
                metadata['fechas_incluidas'].append(fecha_prediccion)
            metadata['ultima_actualizacion'] = datetime.now().isoformat()
            metadata['total_entradas'] = len(historial_datos)
            InformeService._guardar_metadata(directorio, metadata)
            
        else:
            # Primer informe
            historial_datos = nuevas_filas
            historial_path = directorio / "historial_datos.json"
            with open(historial_path, 'w') as f:
                json.dump(historial_datos, f, indent=2, default=str)
            
            metadata['fechas_incluidas'] = [fecha_prediccion]
            metadata['ultima_actualizacion'] = datetime.now().isoformat()
            metadata['total_entradas'] = len(historial_datos)
            InformeService._guardar_metadata(directorio, metadata)
        
        # Ordenar historial por fecha (más reciente primero)
        historial_datos.sort(key=lambda x: datetime.strptime(x['fecha'], "%d/%m/%Y"), reverse=True)
        
        # Generar el PDF
        doc = SimpleDocTemplate(
            str(ruta_pdf),
            pagesize=letter,
            topMargin=1.2 * inch,  # Más espacio para el encabezado
            bottomMargin=0.9 * inch,
            leftMargin=1 * inch,
            rightMargin=1 * inch,
            title=f"{TITULO_INFORME} - Histórico",
            author=AUTOR,
        )
        
        # Añadir metadatos al documento para el pie de página
        doc.total_entradas = metadata['total_entradas']
        doc.fecha_inicio = min(metadata['fechas_incluidas']) if metadata['fechas_incluidas'] else FECHA
        
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
            textColor=COLOR_ACENTO,
            leading=14,
        )
        estilo_resumen = ParagraphStyle(
            "Resumen",
            parent=styles["Normal"],
            fontSize=9,
            textColor=colors.gray,
            leading=12,
        )

        story = []
        
        # === PORTADA/RESUMEN ===
        story.append(Spacer(1, 0.5 * inch))
        story.append(Paragraph("INFORME ACUMULATIVO DE RIESGOS DE HELADA", 
                              ParagraphStyle('Titulo', parent=estilo_titulo, fontSize=16, alignment=1)))
        story.append(Spacer(1, 0.2 * inch))
        
        # Estadísticas generales
        stats_text = f"""
        <b>Período analizado:</b> {min(metadata['fechas_incluidas'])} - {max(metadata['fechas_incluidas'])}<br/>
        <b>Total de registros:</b> {metadata['total_entradas']}<br/>
        <b>Última actualización:</b> {datetime.fromisoformat(metadata['ultima_actualizacion']).strftime('%d/%m/%Y %H:%M')}<br/>
        <b>Fechas incluidas:</b> {', '.join(sorted(metadata['fechas_incluidas']))}
        """
        story.append(Paragraph(stats_text, estilo_normal))
        story.append(HRFlowable(width="100%", thickness=1, color=COLOR_SECUNDARIO))
        story.append(Spacer(1, 0.2 * inch))
        
        # === TABLA HISTÓRICA ===
        story.append(Paragraph("1. HISTORIAL DE PREDICCIONES", estilo_titulo))
        story.append(HRFlowable(width="100%", thickness=1, color=COLOR_SECUNDARIO))
        story.append(Spacer(1, 6))
        
        # Leyenda
        leyenda = """
        <para>
        <font color="green">■</font> Nuevas predicciones (hoy)<br/>
        <font color="blue">■</font> Predicciones anteriores<br/>
        <i>Las filas más recientes aparecen al inicio de la tabla.</i>
        </para>
        """
        story.append(Paragraph(leyenda, estilo_resumen))
        story.append(Spacer(1, 6))
        
        # Generar tabla histórica
        tabla_historica = InformeService._generar_tabla_historica(historial_datos)
        if tabla_historica:
            story.append(tabla_historica)
        
        story.append(Spacer(1, 0.3 * inch))
        
        # === NUEVAS ALERTAS ===
        story.append(Paragraph("2. NUEVAS ALERTAS DETECTADAS", estilo_titulo))
        story.append(HRFlowable(width="100%", thickness=1, color=COLOR_SECUNDARIO))
        story.append(Spacer(1, 6))
        
        alertas_nuevas = predicciones.get('alertas', [])
        if alertas_nuevas:
            for alerta in alertas_nuevas:
                story.append(Paragraph(
                    f"⚠ {alerta.get('mensaje', '-')} - {alerta.get('recomendacion', '-')}",
                    estilo_alerta
                ))
        else:
            story.append(Paragraph("No se detectaron nuevas alertas en esta predicción.", estilo_normal))
        
        # === GRÁFICAS (placeholder para futura implementación) ===
        story.append(PageBreak())
        story.append(Paragraph("3. ANÁLISIS TEMPORAL (PRÓXIMAMENTE)", estilo_titulo))
        story.append(HRFlowable(width="100%", thickness=1, color=COLOR_SECUNDARIO))
        story.append(Spacer(1, 6))
        story.append(Paragraph(
            "En futuras versiones se incluirán gráficas de evolución del riesgo, "
            "temperaturas mínimas y probabilidades de helada a lo largo del tiempo.",
            estilo_normal
        ))
        # Obtengo el gráfico configurado
        d = InformeService._generar_grafico(
            data = historial_datos,
            is_cultivo = is_cultivo
        )

        story.append(d)

        # Construir el PDF
        doc.build(story, onFirstPage=InformeService.encabezado_pie, 
                 onLaterPages=InformeService.encabezado_pie)
        
        print(f"Informe acumulativo actualizado: {NOMBRE_ARCHIVO}")
        print(f"Total registros: {metadata['total_entradas']}")
        print(f"Fechas incluidas: {len(metadata['fechas_incluidas'])}")