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
from dateutil.relativedelta import relativedelta
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
URL_LOGO_UNIVERSIDAD = os.path.join(ruta_directorio_actual, "/assets/logouex.jpg")

#=== CONFIGURACION COLORES ===#
COLOR_PRIMARIO = colors.HexColor("#006414")
COLOR_SECUNDARIO = colors.HexColor("#462204")
COLOR_FONDO_TABLA = colors.HexColor("#EAF4FB")
COLOR_ACENTO = colors.red
COLOR_HOY = colors.HexColor("#FFF3CD")  # Amarillo claro para destacar hoy
COLOR_NUEVO = colors.HexColor("#D4EDDA")  # Verde claro para nuevas predicciones

MAPA_CODIGO_PROVINCIA = {
            "CC" : "Cáceres",
            "BA" : "Badajoz",
            "IB" : "Islas Baleares",
            "B" : "Barcelona",
            "C" : "A Coruña",
            "GI" : "Girona",
            "HU" : "Huesca",
            "LL" : "Lleida",
            "LO" : "La Rioja",
            "LU" : "Lugo",
            "M" : "Madrid",
            "MU" : "Murcia",
            "NA" : "Navarra",
            "OU" : "Ourense",
            "O" : "Asturias",
            "GC" : "Las Palmas",
            "PO" : "Pontevedra",
            "TF" : "Tenerife",
            "T" : "Tarragona",
            "TE" : "Teruel",
            "Z" : "Zaragoza"
        }

class InformeHeladaService():
    
    # Ruta para el archivo de metadatos
    METADATA_FILE = "informe_metadata.json"
    
    @staticmethod
    def _cargar_metadata(directorio):
        """Carga los metadatos del informe existente"""
        metadata_path = directorio / InformeHeladaService.METADATA_FILE
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
        metadata_path = directorio / InformeHeladaService.METADATA_FILE
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
    
    @staticmethod
    def _extraer_datos_para_tabla(predicciones, fecha_str):
        """
        Extrae los datos relevantes de la predicción para la tabla acumulativa
        """
        filas = []

        datos_variedades = predicciones.get('evaluaciones_variedades', {})
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
        lc.valueAxis.valueMin = 0
        lc.valueAxis.valueMax = 100
        lc.valueAxis.valueSteps = [5, 15, 25, 50, 75, 100]

        # Rotar las etiquetas 45 grados para que no se solapen
        lc.categoryAxis.labels.angle = 45

        # Anclar la etiqueta por su esquina superior derecha tras la rotación
        lc.categoryAxis.labels.boxAnchor = 'e'

        # Reducir el tamaño de la fuente
        lc.categoryAxis.labels.fontSize = 6

        # Desplazar las etiquetas hacia abajo para que no choquen con el eje
        lc.categoryAxis.labels.dy = -10

        # Separación mínima entre etiquetas (muestra una de cada N si no caben)
        paso = max(1, len(fechas) // 7)

        fechas_mostrar = [
            fecha if i % paso == 0 else ""
            for i, fecha in enumerate(fechas)
        ]

        lc.categoryAxis.categoryNames = fechas_mostrar


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
    def encabezado_pie(canvas_obj, doc, localizacion_calculo : str):
        canvas_obj.saveState()
        ancho, alto = letter

        canvas_obj.setFillColor(COLOR_PRIMARIO)
        canvas_obj.rect(0, alto - 70, ancho, 70, fill=True, stroke=False)  # ← más alto para caber más info

        canvas_obj.setFillColor(colors.white)
        canvas_obj.setFont("Helvetica-Bold", 14)
        canvas_obj.drawString(1 * inch, alto - 25, TITULO_INFORME)

        canvas_obj.setFont("Helvetica", 9)
        canvas_obj.drawString(1 * inch, alto - 38, SUBTITULO)

        # Fuentes de datos en la cabecera
        canvas_obj.setFont("Helvetica", 7)
        canvas_obj.drawString(1 * inch, alto - 50, "Fuentes: AEMET (predicción futura) · SiAR-Extremadura (datos históricos)")

        # Localización de cálculo
        canvas_obj.setFont("Helvetica", 7)
        canvas_obj.drawString(1 * inch, alto - 63, f"Localización de cálculo: {localizacion_calculo}")

        canvas_obj.setFont("Helvetica", 9)
        canvas_obj.drawRightString(ancho - 1 * inch, alto - 25, f"Actualización: {FECHA}")

        if hasattr(doc, 'total_entradas'):
            canvas_obj.drawRightString(ancho - 1 * inch, alto - 38, f"Registros: {doc.total_entradas}")

        if hasattr(doc, 'zona_geografica'):
            canvas_obj.drawRightString(ancho - 1 * inch, alto - 50, f"Zona: {doc.zona_geografica}")

        canvas_obj.setStrokeColor(COLOR_SECUNDARIO)
        canvas_obj.setLineWidth(2)
        canvas_obj.line(0.75 * inch, alto - 75, ancho - 0.75 * inch, alto - 75)

        # Pie de página (sin cambios)
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
        """
        Genera la sección de contexto inicial del informe: zona geográfica,
        fuentes de datos y período cubierto.
        """

        elementos = []

        estilo_normal = ParagraphStyle(
            "NormalContexto", parent=styles["Normal"],
            fontSize=9, leading=13, spaceAfter=4
        )

        # Tabla de contexto geográfico y fuentes
        datos_contexto = [
            ["Campo", "Detalle"],
            ["Zona geográfica", zona or "No especificada"],
            ["Provincia / Código", (
                f"{provincia} - {MAPA_CODIGO_PROVINCIA.get(provincia)}" 
                if provincia else "No especificada"
            )],
            ["Fuente datos históricos", "SiAR — Red de estaciones agrometeorológicas de Extremadura"],
            ["Fuente datos futuros", "AEMET — Agencia Estatal de Meteorología"],
            ["Tipo de predicción histórica", "Datos observados por estaciones (temperatura, HR, precipitación, viento)"],
            ["Tipo de predicción futura", "Predicción numérica a corto plazo (24-48h) por municipio o provincia"],
            ["Período cubierto", (
                f"{min(metadata['fechas_incluidas'])} → {max(metadata['fechas_incluidas'])}"
                if metadata.get('fechas_incluidas') else "Sin datos aún"
            )],
            ["Última actualización", (
                datetime.fromisoformat(metadata['ultima_actualizacion']).strftime('%d/%m/%Y %H:%M')
                if metadata.get('ultima_actualizacion') else "—"
            )],
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
            ("BACKGROUND", (0, 1), (-1, -1), COLOR_FONDO_TABLA),
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
        elementos.append(Spacer(1, 0.15 * inch))

        # Nota explicativa sobre las fuentes
        nota = (
            "<b>Nota sobre las fuentes:</b> Los datos históricos proceden de la red SiAR, con mediciones "
            "reales de estaciones instaladas en la provincia. Los datos futuros provienen de los modelos "
            "numéricos de AEMET y tienen un horizonte de predicción de 24 a 48 horas. Ambas fuentes se "
            "combinan en este informe para ofrecer una visión completa del riesgo de helada."
        )
        elementos.append(Paragraph(nota, ParagraphStyle(
            "NotaFuentes", parent=styles["Normal"],
            fontSize=7, textColor=colors.grey, leading=10
        )))

        return elementos
    
    @staticmethod
    def _crear_seccion_peticion(
        provincia: Optional[str],
        evaluacion_variedad: bool,
        evaluacion_localidad: bool,
        variedades: Optional[list],
        localidades: Optional[list],
    ):
        """
        Genera la sección de contexto dedicada a mostrar los parámetros
        de la petición en formato de tabla profesional.
        """
        elementos = []

        def _badge(texto, activo: bool):
            """Genera un badge visual de Sí/No con color."""
            color = "#006414" if activo else "#8B0000"
            return f'<font color="{color}"><b>{"✔ Sí" if activo else "✘ No"}</b></font>'

        datos_peticion = [
            ["Parámetro", "Valor"],
            [
                "Provincia",
                f"{provincia} — {MAPA_CODIGO_PROVINCIA.get(provincia, '—')}" if provincia else "No especificada"
            ],
            [
                "Evaluación sobre variedades",
                _badge("", evaluacion_variedad)
            ],
            [
                "Evaluación sobre localidades",
                _badge("", evaluacion_localidad)
            ],
            [
                "Variedades a evaluar",
                ", ".join(variedades) if variedades else "—"
            ],
            [
                "Localidades a evaluar",
                ", ".join(localidades) if localidades else "—"
            ],
        ]

        # Convertir celdas a Paragraph para soportar markup HTML
        estilo_clave = ParagraphStyle(
            "PeticionClave",
            fontName="Helvetica-Bold",
            fontSize=8,
            textColor=colors.HexColor("#2C2C2C"),
            leading=11,
        )
        estilo_valor = ParagraphStyle(
            "PeticionValor",
            fontName="Helvetica",
            fontSize=8,
            textColor=colors.black,
            leading=11,
        )

        filas_render = []
        for i, fila in enumerate(datos_peticion):
            if i == 0:
                filas_render.append(fila)  # cabecera como strings planos
            else:
                filas_render.append([
                    Paragraph(fila[0], estilo_clave),
                    Paragraph(fila[1], estilo_valor),
                ])

        col_widths = [2.5 * inch, 4.0 * inch]
        tabla = Table(filas_render, colWidths=col_widths)
        tabla.setStyle(TableStyle([
            # Cabecera
            ("BACKGROUND",    (0, 0), (-1, 0),  COLOR_PRIMARIO),
            ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
            ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
            ("FONTSIZE",      (0, 0), (-1, 0),  8),
            ("ALIGN",         (0, 0), (-1, 0),  "CENTER"),

            # Filas de datos — alternancia de color
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_FONDO_TABLA, colors.white]),

            # Columna clave con fondo suave
            ("BACKGROUND",    (0, 1), (0, -1),  colors.HexColor("#F0F7F0")),

            # Bordes
            ("GRID",          (0, 0), (-1, -1), 0.4, colors.HexColor("#CCCCCC")),
            ("BOX",           (0, 0), (-1, -1), 1.0, COLOR_PRIMARIO),

            # Línea separadora bajo cabecera
            ("LINEBELOW",     (0, 0), (-1, 0),  1.5, COLOR_SECUNDARIO),

            # Padding
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING",   (0, 0), (-1, -1), 8),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ]))

        elementos.append(tabla)
        elementos.append(Spacer(1, 0.15 * inch))

        return elementos
    
    @staticmethod
    def _color_a_hex(color) -> str:
        """Convierte un color de ReportLab a string hexadecimal para HTML inline."""
        r = int(color.red * 255)
        g = int(color.green * 255)
        b = int(color.blue * 255)
        return f"#{r:02X}{g:02X}{b:02X}"
    
    @staticmethod
    def _crear_contexto_estaciones(estaciones: list, fecha_inicio: str, styles) -> list:
        """
        Genera un bloque informativo sobre las estaciones meteorológicas
        utilizadas para el cálculo de los datos del informe.
        """
        print(estaciones)
        elementos = []

        estilo_caption = ParagraphStyle(
            "CaptionEstaciones", parent=styles["Normal"],
            fontSize=8, textColor=colors.grey, leading=10, spaceAfter=4,
            italics=1
        )

        # Cabecera descriptiva
        n = len(estaciones)
        if n == 1:
            intro = (
                f"Los datos de este informe se han calculado a partir de <b>1 estación "
                f"meteorológica</b> desde {fecha_inicio}."
            )
        else:
            intro = (
                f"Los datos de este informe se han calculado a partir de <b>{n} estaciones "
                f"meteorológicas</b> (media ponderada) desde {fecha_inicio}."
            )

        elementos.append(Paragraph(intro, estilo_caption))

        # Tabla de estaciones
        cabecera = ["Código", "Nombre"]
        filas = [cabecera]

        for est in estaciones:
            # Adapta los campos al modelo real de tu estación
            filas.append([
                est.get("codigo", est.get("code", "—")),
                est.get("nombre", est.get("name", "—")),
            ])

        col_widths = [1.0 * inch, 2.5 * inch]
        tabla = Table(filas, colWidths=col_widths)
        tabla.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0),  COLOR_PRIMARIO),
            ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
            ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
            ("FONTSIZE",      (0, 0), (-1, -1), 8),
            ("FONTNAME",      (0, 1), (-1, -1), "Helvetica"),
            ("ROWBACKGROUNDS",(0, 1), (-1, -1), [COLOR_FONDO_TABLA, colors.white]),
            ("GRID",          (0, 0), (-1, -1), 0.4, colors.lightgrey),
            ("BOX",           (0, 0), (-1, -1), 1,   COLOR_PRIMARIO),
            ("TOPPADDING",    (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING",   (0, 0), (-1, -1), 5),
        ]))

        elementos.append(tabla)
        return elementos

    @staticmethod
    def crear_informe(
        predicciones: dict, 
        estaciones,
        acumular: bool = True, 
        is_cultivo : bool = True,
        zona : Optional[str] = None, 
        provinicia : Optional[str] = None,
        cultivo : Optional[str] = None,
        variedades : Optional[list] = None,
        localidades : Optional[list] = None,
        ):
        """
        Crea o actualiza un informe acumulativo de predicciones
        
        :param predicciones: Nuevas predicciones a añadir
        :param acumular: Si es True, acumula en el informe existente
        """
        try:
            if not isinstance(predicciones, dict):
                print("Error: predicciones no es un diccionario válido")
                return

            directorio = Path(__file__).resolve().parent
            directorio.mkdir(parents=True, exist_ok=True)
            ruta_pdf = directorio / 'reports' / NOMBRE_ARCHIVO
            
            # Cargar metadatos existentes
            metadata = InformeHeladaService._cargar_metadata(directorio)
            
            # Fecha de esta predicción
            fecha_prediccion = predicciones.get("contexto", {}).get("fecha_generacion", "")
            if fecha_prediccion:
                fecha_prediccion = datetime.fromisoformat(fecha_prediccion).strftime("%d/%m/%Y")
            else:
                fecha_prediccion = FECHA
            
            # Extraer datos para la tabla
            nuevas_filas = InformeHeladaService._extraer_datos_para_tabla(predicciones, fecha_prediccion)
            
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
                InformeHeladaService._guardar_metadata(directorio, metadata)
                
            else:
                # Primer informe
                historial_datos = nuevas_filas
                historial_path = directorio / "historial_datos.json"
                with open(historial_path, 'w') as f:
                    json.dump(historial_datos, f, indent=2, default=str)
                
                metadata['fechas_incluidas'] = [fecha_prediccion]
                metadata['ultima_actualizacion'] = datetime.now().isoformat()
                metadata['total_entradas'] = len(historial_datos)
                InformeHeladaService._guardar_metadata(directorio, metadata)
            
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
            print(variedades)
            stats_text = f"""
            <b>Período analizado:</b> {min(metadata['fechas_incluidas'])} - {max(metadata['fechas_incluidas'])}<br/>
            <b>Total de registros:</b> {metadata['total_entradas']}<br/>
            <b>Última actualización:</b> {datetime.fromisoformat(metadata['ultima_actualizacion']).strftime('%d/%m/%Y %H:%M')}<br/>
            <b>Fechas incluidas:</b> {', '.join(sorted(metadata['fechas_incluidas']))}<br/>
            <b>Variedades de cultivo a procesar:</b> {', '.join(variedades or [])}<br/>
            <b>Cultivo asociado a las variedades indicadas:</b> {cultivo or 'No especificado'}<br/>
            """
            story.append(Paragraph(stats_text, estilo_normal))
            story.append(HRFlowable(width="100%", thickness=1, color=COLOR_SECUNDARIO))
            story.append(Spacer(1, 0.2 * inch))
            
            # === SECCIÓN FUENTES DE DATOS === #
            story.append(Paragraph("FUENTES DE DATOS UTILIZADAS", estilo_titulo))
            story.append(HRFlowable(width = "100%", thickness = 1, color = COLOR_PRIMARIO))
            story.append(Spacer(1, 0.1 * inch))

            elementos_fuente = InformeHeladaService._crear_seccion_contexto(
                metadata = metadata,
                zona = zona,
                provincia = provinicia,
                styles = styles
            )

            story.extend(elementos_fuente)
            story.append(Spacer(1, 0.08 * inch))

            # === SECCIÓN PARÁMETROS DE LA PETICIÓN === #
            story.append(Paragraph("CUERPO DE LA PETICIÓN - POST", estilo_titulo))
            story.append(HRFlowable(width = "100%", thickness = 1, color = COLOR_PRIMARIO))
            story.append(Spacer(1, 0.1 * inch))

            elementos_peticion = InformeHeladaService._crear_seccion_peticion(
                provincia = provinicia,
                evaluacion_variedad = is_cultivo,
                evaluacion_localidad = not is_cultivo,
                variedades = variedades,
                localidades = localidades
            )

            story.extend(elementos_peticion)
            story.append(Spacer(1, 0.08 * inch))

            # === TABLA HISTÓRICA ===
            story.append(Paragraph("1. HISTORIAL DE PREDICCIONES ANTE RIESGO DE HELADA", estilo_titulo))
            story.append(HRFlowable(width="100%", thickness=1, color=COLOR_SECUNDARIO))
            story.append(Spacer(1, 6))
            
            # Leyenda
            hex_hoy = InformeHeladaService._color_a_hex(COLOR_HOY)
            hex_antiguos = InformeHeladaService._color_a_hex(COLOR_FONDO_TABLA)
            
            leyenda = (
                f'<font color="{hex_hoy}">■</font> Nuevas predicciones (hoy)<br/>'
                f'<font color="{hex_antiguos}">■</font> Predicciones anteriores<br/>'
                f'<font color="#F2F2F2">■</font> Datos históricos (degradado por antigüedad)<br/>'
            )
            story.append(Paragraph(leyenda, estilo_resumen))
            story.append(Spacer(1, 6))
            
            # Generar tabla histórica
            tabla_historica = InformeHeladaService._generar_tabla_historica(historial_datos)
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

            # ── Contexto de cálculo ──────────────────────────────────────────
            if estaciones:
                fecha_hoy = datetime.today()
                elementos_est = InformeHeladaService._crear_contexto_estaciones(
                    estaciones=estaciones,
                    #fecha_inicio=metadata.get('fechas_incluidas', [FECHA])[0] if metadata.get('fechas_incluidas') else FECHA,
                    fecha_inicio=f"15 Noviembre {datetime.today().year - 1}",
                    styles=styles,
                )
                story.extend(elementos_est)
                story.append(Spacer(1, 0.1 * inch))
            
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
            d = InformeHeladaService._generar_grafico(
                data = historial_datos,
                is_cultivo = is_cultivo
            )

            story.append(d)

            encabezado_con_params = partial(
                InformeHeladaService.encabezado_pie,
                localizacion_calculo = provinicia
            )

            # Construir el PDF
            doc.build(story, onFirstPage=encabezado_con_params, 
                    onLaterPages=encabezado_con_params)
            
            print(f"Informe acumulativo actualizado: {NOMBRE_ARCHIVO}")
            print(f"Total registros: {metadata['total_entradas']}")
            print(f"Fechas incluidas: {len(metadata['fechas_incluidas'])}")

            return str(ruta_pdf)
        except Exception as e:
            print(f"Error al crear un nuevo informe de heladas futuras: {e}")