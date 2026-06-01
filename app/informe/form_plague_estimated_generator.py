from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, PageBreak, KeepTogether
from datetime import date, datetime
from pathlib import Path
import os

ruta_directorio_actual = os.getcwd()

#=== INFORMACIÓN DE ESTRUCTURA INFORME ===#
TITULO_INFORME = "Predicciones Dinámicas sobre Riesgos ante Plagas"
SUBTITULO_1 = "Análisis temporal de riesgos por cultivo"
SUBTITULO_2 = "Evolución diaria de condiciones favorables para plagas"
AUTOR = "Álvaro Mendo Martín"
NOMBRE_UNIVERSIDAD = "Escuela Politécnica - Cáceres"
URL_LOGO_UNIVERSIDAD = os.path.join(ruta_directorio_actual, "assets", "logouex.jpg")

#=== CONFIGURACIÓN DE COLORES MANTENIDA ===#
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
    """Servicio optimizado para generar informes profesionales de plagas estimadas"""
    
    @staticmethod
    def definir_color_por_riesgo(nivel: str):
        nivel = nivel.lower()
        return MAP_NIVEL_COLOR.get(nivel, (COLOR_SIN_RIESGO, TEXTO_SIN_RIESGO))

    # ── Helpers de parcela ────────────────────────────────────────────────────

    @staticmethod
    def _calcular_centroide(geometria: list) -> tuple:
        try:
            coords = geometria[0]
            lons = [c[0] for c in coords]
            lats = [c[1] for c in coords]
            return round(sum(lats) / len(lats), 5), round(sum(lons) / len(lons), 5)
        except Exception:
            return None, None

    @staticmethod
    def _formatear_coordenadas(geometria: list) -> str:
        lat, lon = InformePlagaEstimadaService._calcular_centroide(geometria)
        if lat is None:
            return "No disponible"
        hemisferio_lat = "N" if lat >= 0 else "S"
        hemisferio_lon = "E" if lon >= 0 else "O"
        return f"{abs(lat)}° {hemisferio_lat}, {abs(lon)}° {hemisferio_lon}"

    # ── Secciones de contexto mejoradas con envoltura de párrafos ─────────────

    @staticmethod
    def crear_tabla_contexto_parcela(parcelas: list, styles) -> list:
        elementos = []

        estilo_subtitulo = ParagraphStyle(
            "SubtituloContexto",
            parent=styles["Heading2"],
            fontSize=10,
            textColor=COLOR_SECUNDARIO,
            spaceAfter=6,
            spaceBefore=8,
        )
        estilo_encabezado = ParagraphStyle(
            "EncabezadoContexto",
            fontName="Helvetica-Bold",
            fontSize=8,
            textColor=colors.white
        )
        estilo_celda_negrita = ParagraphStyle(
            "CeldaContextoNegrita",
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=11
        )
        estilo_celda_normal = ParagraphStyle(
            "CeldaContextoNormal",
            fontName="Helvetica",
            fontSize=8,
            leading=11
        )

        for parcela_info in parcelas:
            cultivo = parcela_info.get("cultivo", {})
            parcela = parcela_info.get("parcela", {})
            fecha_inicio_parcela = parcela_info.get("fecha_inicio")
            fecha_fin_parcela = parcela_info.get("fecha_fin")

            nombre_parcela = parcela.get("nombre", "Sin nombre")
            nombre_cultivo = cultivo.get("nombre", "-")
            nombre_cientifico = cultivo.get("nombre_cientifico", "")
            descripcion_cultivo = cultivo.get("descripcion", "-")
            geometria = parcela.get("geometria", [])
            coordenadas = InformePlagaEstimadaService._formatear_coordenadas(geometria)

            if fecha_inicio_parcela:
                try:
                    fi = datetime.fromisoformat(fecha_inicio_parcela).strftime("%d/%m/%Y")
                except Exception:
                    fi = fecha_inicio_parcela
            else:
                fi = "No definida"

            if fecha_fin_parcela:
                try:
                    ff = datetime.fromisoformat(fecha_fin_parcela).strftime("%d/%m/%Y")
                except Exception:
                    ff = fecha_fin_parcela
            else:
                ff = "En curso"

            elementos.append(Paragraph(f"Ubicación y Parcela: {nombre_parcela}", estilo_subtitulo))

            datos_tabla = [
                [Paragraph("Campo de Control", estilo_encabezado), Paragraph("Valor Registrado en Sistema", estilo_encabezado)],
                [Paragraph("Nombre de la parcela", estilo_celda_negrita), Paragraph(nombre_parcela, estilo_celda_normal)],
                [Paragraph("Cultivo", estilo_celda_negrita), Paragraph(f"{nombre_cultivo} (<i>{nombre_cientifico}</i>)" if nombre_cientifico else nombre_cultivo, estilo_celda_normal)],
                [Paragraph("Descripción del cultivo", estilo_celda_negrita), Paragraph(descripcion_cultivo, estilo_celda_normal)],
                [Paragraph("Localización (centroide)", estilo_celda_negrita), Paragraph(coordenadas, estilo_celda_normal)],
                [Paragraph("Período de actividad", estilo_celda_negrita), Paragraph(f"{fi} → {ff}", estilo_celda_normal)],
                [Paragraph("Identificador de parcela", estilo_celda_negrita), Paragraph(parcela.get("public_id", "-"), estilo_celda_normal)],
            ]

            # Ajuste estricto al ancho de rejilla (2.0 + 4.9 = 6.9 pulgadas)
            col_widths = [2.0 * inch, 4.9 * inch]
            tabla = Table(datos_tabla, colWidths=col_widths)
            tabla.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), COLOR_PRIMARIO),
                ("BACKGROUND", (0, 1), (-1, -1), COLOR_FONDO_TABLA),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.white),
                ("BOX", (0, 0), (-1, -1), 1, COLOR_PRIMARIO),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]))

            elementos.append(tabla)
            elementos.append(Spacer(1, 0.1 * inch))

        return elementos

    @staticmethod
    def crear_tabla_fuentes_datos(sensores: list, usa_meteo: bool, styles) -> list:
        elementos = []
        
        estilo_encabezado = ParagraphStyle("EncabezadoFuente", fontName="Helvetica-Bold", fontSize=8, textColor=colors.white)
        estilo_celda_bold = ParagraphStyle("CeldaFuenteBold", fontName="Helvetica-Bold", fontSize=7.5, leading=10)
        estilo_celda_normal = ParagraphStyle("CeldaFuenteNormal", fontName="Helvetica", fontSize=7.5, leading=10)

        datos_tabla = [[
            Paragraph("Fuente de datos", estilo_encabezado), 
            Paragraph("Descripción Operativa", estilo_encabezado), 
            Paragraph("Identificador / Detalle Técnico", estilo_encabezado)
        ]]

        if sensores:
            for i, eui in enumerate(sensores):
                datos_tabla.append([
                    Paragraph("Sensor de campo" if i == 0 else "", estilo_celda_bold),
                    Paragraph("Sensor IoT agroclimático instalado en finca. Proporciona registros de temperatura, humedad foliar y humedad de suelo en tiempo real." if i == 0 else "", estilo_celda_normal),
                    Paragraph(str(eui.get('sensor')), estilo_celda_normal)
                ])

        if usa_meteo:
            datos_tabla.append([
                Paragraph("Estación meteorológica (SiAR)", estilo_celda_bold),
                Paragraph("Red de estaciones oficiales de la Junta de Extremadura. Complementa contingencias de datos (HR ambiental, precipitación acumulada, viento).", estilo_celda_normal),
                Paragraph("Provincia: CC — Agregación: Diaria", estilo_celda_normal)
            ])

        # Ajuste estricto al ancho de rejilla (1.7 + 3.5 + 1.7 = 6.9 pulgadas)
        col_widths = [1.7 * inch, 3.5 * inch, 1.7 * inch]
        tabla = Table(datos_tabla, colWidths=col_widths)

        estilo = [
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_PRIMARIO),
            ("BACKGROUND", (0, 1), (-1, -1), COLOR_FONDO_TABLA),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.white),
            ("BOX", (0, 0), (-1, -1), 1, COLOR_PRIMARIO),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]

        if sensores and len(sensores) > 1:
            estilo.append(("SPAN", (0, 1), (0, len(sensores))))
            estilo.append(("SPAN", (1, 1), (1, len(sensores))))

        tabla.setStyle(TableStyle(estilo))
        elementos.append(tabla)
        return elementos

    # ── Métodos de Canvas (Encabezado y Pie Dinámico) ─────────────────────────

    @staticmethod
    def encabezado_pie(canva_obj, doc):
        canva_obj.saveState()
        ancho, alto = letter 

        # Cabecera Institucional
        canva_obj.setFillColor(COLOR_PRIMARIO)
        canva_obj.rect(0, alto - 60, ancho, 60, fill=True, stroke=False)

        canva_obj.setFillColor(colors.white)
        canva_obj.setFont("Helvetica-Bold", 13)
        canva_obj.drawString(0.8 * inch, alto - 28, TITULO_INFORME.upper())

        canva_obj.setFont("Helvetica", 9)
        canva_obj.drawString(0.8 * inch, alto - 42, SUBTITULO_1)

        fecha_actual = date.today().strftime("%d/%m/%Y")
        canva_obj.drawRightString(ancho - 0.8 * inch, alto - 35, f"Emisión: {fecha_actual}")

        # Separadores de diseño
        canva_obj.setStrokeColor(COLOR_SECUNDARIO)  
        canva_obj.setLineWidth(1.5)
        canva_obj.line(0.8 * inch, alto - 65, ancho - 0.8 * inch, alto - 65)

        # Línea divisoria inferior (Establecida exactamente en Y=50)
        canva_obj.setStrokeColor(colors.lightgrey)
        canva_obj.setLineWidth(0.5)
        canva_obj.line(0.8 * inch, 50, ancho - 0.8 * inch, 50)

        # Pie de página (Ubicado a Y=35, resguardado de la firma criptográfica)
        canva_obj.setFillColor(colors.dimgrey)
        canva_obj.setFont("Helvetica", 8)
        canva_obj.drawString(0.8 * inch, 35, f"© {date.today().year} - {AUTOR} ({NOMBRE_UNIVERSIDAD})")

        canva_obj.setFont("Helvetica-Bold", 8)
        canva_obj.drawCentredString(ancho / 2, 35, f"Pág. {doc.page}")

        canva_obj.setFont("Helvetica-Oblique", 7.5)
        canva_obj.drawRightString(ancho - 0.8 * inch, 35, SUBTITULO_2)
        canva_obj.restoreState()

    @staticmethod
    def crear_tabla_resumen_plagas(plagas_evaluadas: list) -> Table:
        cabecera = ["Agente de Riesgo Evaluado", "Taxonomía", "Días Crítica", "Días Preventiva", "Días Sin Riesgo", "Muestra Total"]
        col_widths = [1.9 * inch, 0.8 * inch, 1.0 * inch, 1.1 * inch, 1.3 * inch, 0.8 * inch]

        datos_tabla = [cabecera]
        
        for plaga in plagas_evaluadas:
            datos = plaga['datos_probabilidad']
            total_dias = len(datos)
            dias_critica = sum(1 for d in datos if d['nivel_riesgo'].lower() == 'critica')
            dias_preventiva = sum(1 for d in datos if d['nivel_riesgo'].lower() == 'preventiva')
            dias_sin_riesgo = sum(1 for d in datos if d['nivel_riesgo'].lower() == 'sin_riesgo')
            
            datos_tabla.append([
                plaga['nombre'],
                plaga['tipo'].capitalize(),
                str(dias_critica),
                str(dias_preventiva),
                str(dias_sin_riesgo),
                f"{total_dias} d"
            ])
        
        tabla = Table(datos_tabla, colWidths=col_widths, repeatRows=1)
        estilo_base = [
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_PRIMARIO),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("ALIGN", (2, 1), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("BOX", (0, 0), (-1, -1), 1, COLOR_PRIMARIO),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]
        tabla.setStyle(TableStyle(estilo_base))
        
        for i in range(1, len(datos_tabla)):
            fondo_critica, _ = InformePlagaEstimadaService.definir_color_por_riesgo("critica")
            tabla.setStyle(TableStyle([("BACKGROUND", (2, i), (2, i), fondo_critica)]))
            fondo_preventiva, _ = InformePlagaEstimadaService.definir_color_por_riesgo("preventiva")
            tabla.setStyle(TableStyle([("BACKGROUND", (3, i), (3, i), fondo_preventiva)]))
            fondo_sin_riesgo, _ = InformePlagaEstimadaService.definir_color_por_riesgo("sin_riesgo")
            tabla.setStyle(TableStyle([("BACKGROUND", (4, i), (4, i), fondo_sin_riesgo)]))
        
        return tabla
    
    @staticmethod
    def formatear_condiciones(lista):
        import re
        resultado = []

        # 1. Helper para formatear números puros a 2 decimales
        def _formatear_num(valor):
            if isinstance(valor, (int, float)):
                return f"{valor:.2f}"
            return str(valor)

        # 2. Helper con Regex para buscar y recortar CUALQUIER número decimal dentro de un texto
        def _limpiar_decimales_en_texto(texto):
            # Encuentra patrones como 23.45678 y los reemplaza por su versión con 2 decimales (23.46)
            return re.sub(r'[-+]?\d*\.\d+', lambda m: f"{float(m.group(0)):.2f}", texto)

        for item in lista:
            if isinstance(item, str):
                # CASO A: Si gdd_acumulado viene directamente como texto plano ("gdd_acumulado: 15.33333")
                resultado.append(_limpiar_decimales_en_texto(item))

            elif isinstance(item, (int, float)):
                # CASO B: Si viene el número flotante suelto
                resultado.append(_formatear_num(item))

            elif isinstance(item, dict):
                # CASO C: Estructura estándar con la clave "variable"
                if "variable" in item:
                    umbral = item.get('umbral', '')
                    valor_real = item.get('valor_real', '-')
                    
                    umbral_fmt = _formatear_num(umbral) if umbral != '' else ''
                    valor_real_fmt = _formatear_num(valor_real) if valor_real != '-' else '-'

                    texto = (
                        f"{item.get('variable')} "
                        f"{item.get('operador', '')} "
                        f"{umbral_fmt} "
                        f"(valor real: {valor_real_fmt})"
                    )
                    resultado.append(_limpiar_decimales_en_texto(texto))

                elif "dias_consecutivos" in item:
                    texto = (
                        f"Días consecutivos: "
                        f"{item.get('dias_consecutivos', 0)}/"
                        f"{item.get('dias_requeridos', 0)}"
                    )
                    resultado.append(texto)

                else:
                    # CASO D: Si gdd_acumulado viene como un diccionario genérico (ej: {"gdd_acumulado": 124.66666})
                    pares = []
                    for k, v in item.items():
                        v_fmt = _formatear_num(v) if isinstance(v, (int, float)) else _limpiar_decimales_en_texto(str(v))
                        pares.append(f"{k}: {v_fmt}")
                    resultado.append(", ".join(pares))

            else:
                # CASO E: Cualquier otro tipo de objeto desconocido lo convertimos a string y limpiamos sus decimales
                resultado.append(_limpiar_decimales_en_texto(str(item)))

        return "<br/>".join(resultado) or "-"
    
    @staticmethod
    def crear_tabla_evolucion_diaria(datos_probabilidad: list, nombre_plaga: str) -> Table:
        datos_mostrar = datos_probabilidad[-21:] if len(datos_probabilidad) > 21 else datos_probabilidad
        
        cabecera = ["Fecha", "Nivel Riesgo", "Condiciones Evaluadas Cumplidas", "Condiciones Pendientes / Umbral"]
        col_widths = [0.9 * inch, 1.0 * inch, 2.5 * inch, 2.5 * inch]
        
        datos_tabla = [cabecera]
        estilo_celda = ParagraphStyle("CeldaDetalle", fontName="Helvetica", fontSize=7, leading=9.5)
        
        for registro in datos_mostrar:
            fecha_str = registro['fecha']
            try:
                fecha = datetime.strptime(fecha_str, "%Y-%m-%d").strftime("%d/%m/%Y")
            except Exception:
                fecha = fecha_str
                
            nivel = registro['nivel_riesgo'].upper()
            fondo, texto_color = InformePlagaEstimadaService.definir_color_por_riesgo(registro['nivel_riesgo'])
            
            cumplidas = InformePlagaEstimadaService.formatear_condiciones(registro.get("condiciones_cumplidas", []))
            pendientes = InformePlagaEstimadaService.formatear_condiciones(registro.get("condiciones_pendientes", []))
            
            estilo_nivel = ParagraphStyle(
                "NivelStyle",
                parent=estilo_celda,
                alignment=1,
                textColor=texto_color,
                backColor=fondo,
                fontSize=7.5,
                fontName="Helvetica-Bold"
            )
            
            datos_tabla.append([
                Paragraph(fecha, estilo_celda),
                Paragraph(f"<font size='8'><b>{nivel}</b></font>", estilo_nivel),
                Paragraph(cumplidas, estilo_celda),
                Paragraph(pendientes, estilo_celda)
            ])
        
        tabla = Table(datos_tabla, colWidths=col_widths, repeatRows=1)
        estilo_tabla = [
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_PRIMARIO),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
            ("BOX", (0, 0), (-1, -1), 1, COLOR_PRIMARIO),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]
        
        for i in range(1, len(datos_tabla)):
            nivel_fila = datos_mostrar[i-1]['nivel_riesgo']
            fondo, _ = InformePlagaEstimadaService.definir_color_por_riesgo(nivel_fila)
            estilo_tabla.append(("BACKGROUND", (1, i), (1, i), fondo))
        
        tabla.setStyle(TableStyle(estilo_tabla))
        return tabla
    
    @staticmethod
    def crear_grafico_evolucion_temporal(datos_probabilidad: list, nombre_plaga: str) -> Table:
        datos_muestra = datos_probabilidad[-30:] if len(datos_probabilidad) > 30 else datos_probabilidad
        num_columnas = len(datos_muestra)
        
        ancho_total_disponible = 6.9 * inch
        ancho_columna = ancho_total_disponible / num_columnas
        col_widths = [ancho_columna] * num_columnas
        
        fila_bloques = [""] * num_columnas
        fila_fechas = [""] * num_columnas
        
        estilo_fecha = ParagraphStyle("FechaGrafico", fontName="Helvetica", fontSize=5.5, alignment=1, leading=7)
        
        estilos_celdas = []
        for idx, registro in enumerate(datos_muestra):
            nivel = registro['nivel_riesgo'].lower()
            fondo, _ = InformePlagaEstimadaService.definir_color_por_riesgo(nivel)
            
            estilos_celdas.append(("BACKGROUND", (idx, 0), (idx, 0), fondo))
            
            if idx % 5 == 0 or idx == num_columnas - 1:
                try:
                    label_fecha = datetime.strptime(registro['fecha'], "%Y-%m-%d").strftime("%d/%m")
                except Exception:
                    label_fecha = registro['fecha'][5:]
                fila_fechas[idx] = Paragraph(label_fecha, estilo_fecha)
            else:
                fila_fechas[idx] = ""

        datos_tabla = [fila_bloques, fila_fechas]
        
        tabla_grafico = Table(datos_tabla, colWidths=col_widths)
        estilo_base = [
            ("GRID", (0, 0), (-1, 0), 1, colors.white), 
            ("BOX", (0, 0), (-1, 0), 1, COLOR_PRIMARIO),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 14), 
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 1), (-1, 1), 2),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]
        estilo_base.extend(estilos_celdas)
        tabla_grafico.setStyle(TableStyle(estilo_base))
        
        return tabla_grafico
    
    @staticmethod
    def _crear_nota_metodologica_gdd(ventana: dict, condiciones_evaluables: list, styles) -> list:
        """
        Genera un bloque explicativo sobre la metodología GDD aplicada a esta plaga,
        destacando la evaluación en dos fases introducida en la última actualización.
        """
        elementos = []

        COLOR_NOTA_FONDO = colors.HexColor("#EAF4FB")
        COLOR_NOTA_BORDE = colors.HexColor("#006414")

        estilo_titulo_nota = ParagraphStyle(
            "TituloNota",
            fontName="Helvetica-Bold",
            fontSize=8,
            textColor=COLOR_PRIMARIO,
            spaceAfter=3,
            leading=11
        )
        estilo_cuerpo_nota = ParagraphStyle(
            "CuerpoNota",
            fontName="Helvetica",
            fontSize=7.5,
            leading=11,
            textColor=colors.HexColor("#1a1a1a")
        )

        dias_ventana     = ventana.get('dias_ventana', '–')
        temp_base        = ventana.get('temperatura_base', '–')
        gdd_objetivo     = ventana.get('gdd_objetivo', '–')
        nivel_si_cumple  = ventana.get('nivel_si_cumple', 'CRITICA')

        # Descripción de la condición secundaria (temperatura suelo u otras)
        condiciones_secundarias = []
        for c in condiciones_evaluables:
            condiciones_secundarias.append(
                f"{c.get('variable', c.get('tipo', '?'))} {c.get('operador','≥')} {c.get('valor','?')}"
            )
        texto_secundaria = " y ".join(condiciones_secundarias) if condiciones_secundarias else "ninguna adicional registrada"

        contenido = [
            Paragraph("⚙ Metodología de Evaluación: Acumulación de Grados-Día (GDD) + Verificación Secundaria", estilo_titulo_nota),
            Paragraph(
                f"<b>Fase 1 — Ventana deslizante GDD:</b> Para cada día del período analizado se acumulan los "
                f"grados-día de los <b>{dias_ventana} días anteriores</b>, usando temperatura base <b>{temp_base} °C</b>. "
                f"Se alcanza nivel <b>{nivel_si_cumple}</b> cuando el acumulado supera <b>{gdd_objetivo} GDD</b>.",
                estilo_cuerpo_nota
            ),
            Paragraph(
                f"<b>Fase 2 — Verificación de condición de suelo:</b> Superado el umbral GDD, se comprueba "
                f"adicionalmente: <b>{texto_secundaria}</b>. Solo si ambas fases se cumplen simultáneamente "
                f"el día recibe nivel <b>CRÍTICO</b>. Si el GDD se cumple pero la condición de suelo no, "
                f"el nivel se rebaja a <b>PREVENTIVO</b>.",
                estilo_cuerpo_nota
            ),
        ]

        tabla_nota = Table(
            [[contenido]],
            colWidths=[6.9 * inch]
        )
        tabla_nota.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), COLOR_NOTA_FONDO),
            ("BOX",        (0, 0), (-1, -1), 1.2, COLOR_NOTA_BORDE),
            ("TOPPADDING",    (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING",   (0, 0), (-1, -1), 10),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ]))

        elementos.append(tabla_nota)
        elementos.append(Spacer(1, 0.07 * inch))
        return elementos

    # ── Método principal de construcción ──────────────────────────────────────

    @staticmethod
    def crear_informe_estimado(
        datos: dict,
        parcelas: list = None,
        sensores: list = None,
        usa_meteo: bool = False
    ):
        if not datos or 'plagas_evaluadas' not in datos:
            print("Error: datos no contiene la estructura esperada")
            return None
        
        directorio = Path(__file__).resolve().parent
        directorio_reports = directorio / 'reports'
        directorio_reports.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_archivo = f"reporte_riesgos_{datos['cultivo'].lower()}_{timestamp}.pdf"
        ruta_pdf = directorio_reports / nombre_archivo
        
        # AJUSTE CRÍTICO: bottomMargin fijado en 2.1 pulgadas para blindar de forma absoluta
        # el espacio vertical (Y: 50 a 150) reservado para el estampado criptográfico de PyHanko.
        doc = SimpleDocTemplate(
            str(ruta_pdf),
            pagesize=letter,
            topMargin=1.3 * inch,   
            bottomMargin=2.1 * inch,  
            leftMargin=0.8 * inch,
            rightMargin=0.8 * inch,
            title=f"{TITULO_INFORME} - {datos['cultivo']}",
            author=AUTOR
        )
        
        styles = getSampleStyleSheet()
        
        estilo_titulo_principal = ParagraphStyle(
            "TituloPrincipal",
            parent=styles["Heading1"],
            fontSize=14,
            textColor=COLOR_PRIMARIO,
            alignment=1,
            spaceAfter=10,
        )
        
        estilo_titulo = ParagraphStyle(
            "TituloSeccion",
            parent=styles["Heading1"],
            fontSize=11,
            textColor=COLOR_PRIMARIO,
            spaceAfter=5,
            spaceBefore=12,
        )
        
        estilo_subtitulo = ParagraphStyle(
            "SubtituloSeccion",
            parent=styles["Heading2"],
            fontSize=10,
            textColor=COLOR_SECUNDARIO,
            spaceAfter=4,
            spaceBefore=8,
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
            textColor=colors.dimgrey,
            leading=11,
        )
        
        story = []
        
        # ====== PORTADA / RESUMEN GLOBAL ======
        story.append(Spacer(1, 0.15 * inch))
        story.append(Paragraph(
            f"INFORME TÉCNICO DE RIESGOS DE PLAGAS VIA SERIES TEMPORALES<br/><font size='12'>SISTEMA AGRO-PREDICT — CULTIVO: {datos['cultivo'].upper()}</font>",
            estilo_titulo_principal
        ))
        story.append(Spacer(1, 0.05 * inch))
        
        total_dias = (
            datetime.strptime(datos['fecha_final'], "%Y-%m-%d") -
            datetime.strptime(datos['fecha_inicio'], "%Y-%m-%d")
        ).days + 1

        periodo_texto = (
            f"<b>Período Cronológico Analizado:</b> {datos['fecha_inicio']} hasta {datos['fecha_final']}<br/>"
            f"<b>Rango Temporal Absoluto:</b> {total_dias} días de monitorización activa.<br/>"
            f"<b>Agentes de Riesgo Biológico Evaluados:</b> {len(datos['plagas_evaluadas'])} vectores."
        )

        story.append(Paragraph(periodo_texto, estilo_normal))
        story.append(HRFlowable(width="100%", thickness=1.2, color=COLOR_SECUNDARIO, spaceBefore=4, spaceAfter=8))
        
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
        
        stats_text = (
            f"<b>Métricas Consolidadas de Alertas:</b><br/>"
            f"• Alertas en Fase <b>CRÍTICA</b>: <font color='#721C24'><b>{total_critica} registros</b></font> (Requiere intervención fitosanitaria inmediata).<br/>"
            f"• Alertas en Fase <b>PREVENTIVA</b>: <font color='#856404'><b>{total_preventiva} registros</b></font> (Incrementar frecuencia de monitoreo en campo).<br/>"
            f"• Estados <b>SIN RIESGO</b> Activo: <font color='#155724'><b>{total_registros - total_critica - total_preventiva} registros</b></font> (Condiciones bioclimáticas estables)."
        )

        story.append(Paragraph(stats_text, estilo_normal))
        story.append(Spacer(1, 0.05 * inch))
        
        leyenda = """
        <b>Leyenda Operativa Analítica:</b> &nbsp;&nbsp;
        <font color="#721C24">■ <b>CRÍTICA (Condiciones Óptimas de Desarrollo)</b></font>  &nbsp;&nbsp;|&nbsp;&nbsp;
        <font color="#856404">■ <b>PREVENTIVA (Umbral de Riesgo Inicial)</b></font>  &nbsp;&nbsp;|&nbsp;&nbsp;
        <font color="#155724">■ <b>SIN RIESGO DETECTADO</b></font>
        """
        story.append(Paragraph(leyenda, estilo_resumen))
        story.append(Spacer(1, 0.1 * inch))

        # ====== SECCIÓN CONTEXTO: PARCELA ======
        if parcelas:
            story.append(Paragraph("1. CONTEXTO OPERATIVO DE LA PARCELA", estilo_titulo))
            story.append(HRFlowable(width="100%", thickness=0.8, color=COLOR_PRIMARIO, spaceAfter=4))
            elementos_parcela = InformePlagaEstimadaService.crear_tabla_contexto_parcela(parcelas, styles)
            story.extend(elementos_parcela)
            story.append(Spacer(1, 0.1 * inch))

        # ====== SECCIÓN FUENTES DE DATOS ======
        if sensores or usa_meteo:
            story.append(Paragraph("2. AUDITORÍA DE FUENTES DE DATOS UTILIZADAS", estilo_titulo))
            story.append(HRFlowable(width="100%", thickness=0.8, color=COLOR_PRIMARIO, spaceAfter=4))

            descripcion_fuentes = (
                "El motor predictivo de Agro-Predict ejecuta sus modelos de simulación matemática basándose "
                "en la ingesta multi-fuente descrita a continuación. Los sensores IoT locales computan "
                "microclima en dosel, priorizándose su lectura. Ante fallas de red, el sistema realiza una "
                "conmutación failover automática hacia los nodos de la red agrometeorológica pública SiAR."
            )
            story.append(Paragraph(descripcion_fuentes, estilo_normal))
            story.append(Spacer(1, 0.05 * inch))

            elementos_fuentes = InformePlagaEstimadaService.crear_tabla_fuentes_datos(sensores or [], usa_meteo, styles)
            story.extend(elementos_fuentes)
            story.append(Spacer(1, 0.1 * inch))

        # ====== TABLA RESUMEN DE PLAGAS ======
        story.append(Paragraph("3. CUADRO DE MANDO RESUMIDO DE RIESGOS", estilo_titulo))
        story.append(HRFlowable(width="100%", thickness=0.8, color=COLOR_PRIMARIO, spaceAfter=6))
        
        tabla_resumen = InformePlagaEstimadaService.crear_tabla_resumen_plagas(datos['plagas_evaluadas'])
        story.append(tabla_resumen)
        story.append(PageBreak()) 
        
        # ====== DETALLE POR PLAGA ======
        story.append(Paragraph("4. ANÁLISIS DINÁMICO Y AUDITORÍA DETALLADA POR VECTOR", estilo_titulo))      
        story.append(HRFlowable(width="100%", thickness=0.8, color=COLOR_PRIMARIO, spaceAfter=8))
        
        for idx, plaga in enumerate(datos['plagas_evaluadas'], start=1):
            nombre_plaga = plaga['nombre']
            tipo_plaga = plaga['tipo'].capitalize()
            datos_probabilidad = plaga['datos_probabilidad']
            
            elementos_plaga = []
            elementos_plaga.append(Paragraph(
                f"4.{idx}. {nombre_plaga} — Clasificación Biológica: <font size='9'><b>{tipo_plaga}</b></font>",
                estilo_subtitulo
            ))
            
            dias_critica = sum(1 for d in datos_probabilidad if d['nivel_riesgo'].lower() == 'critica')
            dias_preventiva = sum(1 for d in datos_probabilidad if d['nivel_riesgo'].lower() == 'preventiva')
            dias_sin = len(datos_probabilidad) - dias_critica - dias_preventiva
            
            stats_plaga = f"""
            <b>Distribución de Alertas en el Periodo:</b> &nbsp;&nbsp;
            Fase Crítica: <font color='#721C24'><b>{dias_critica} d</b></font> &nbsp;|&nbsp;
            Fase Preventiva: <font color='#856404'><b>{dias_preventiva} d</b></font> &nbsp;|&nbsp;
            Estable sin riesgo: <font color='#155724'><b>{dias_sin} d</b></font>
            """
            elementos_plaga.append(Paragraph(stats_plaga, estilo_normal))
            elementos_plaga.append(Spacer(1, 0.05 * inch))
            
            if len(datos_probabilidad) >= 5:
                try:
                    elementos_plaga.append(Paragraph("<b>Distribución y Tendencia de Riesgos (Últimos 30 días):</b>", estilo_resumen))
                    elementos_plaga.append(Spacer(1, 0.02 * inch))
                    grafico = InformePlagaEstimadaService.crear_grafico_evolucion_temporal(datos_probabilidad, nombre_plaga)
                    elementos_plaga.append(grafico)
                    elementos_plaga.append(Spacer(1, 0.08 * inch))
                except Exception:
                    pass
            
            ventanas = plaga.get('ventana_temporal', [])
            ventana_gdd = next((v for v in ventanas if v.get('modo') == 'acumulacion_gdd'), None)
            if ventana_gdd:
                condiciones_evaluables = plaga.get('condiciones_evaluables', [])
                nota_gdd = InformePlagaEstimadaService._crear_nota_metodologica_gdd(
                    ventana=ventana_gdd,
                    condiciones_evaluables=condiciones_evaluables,
                    styles=styles
                )
                elementos_plaga.extend(nota_gdd)

            elementos_plaga.append(Paragraph("<b>Auditoría Operativa de Condiciones de Campo:</b>", estilo_normal))
            tabla_evolucion = InformePlagaEstimadaService.crear_tabla_evolucion_diaria(datos_probabilidad, nombre_plaga)
            elementos_plaga.append(tabla_evolucion)
            
            story.append(KeepTogether(elementos_plaga))
            
            if idx < len(datos['plagas_evaluadas']):
                story.append(PageBreak())
            else:
                story.append(Spacer(1, 0.15 * inch))
        
        # ====== NOTA FINAL Y FINALIZACIÓN DE HISTORIA ======
        elementos_cierre = []
        elementos_cierre.append(HRFlowable(width="100%", thickness=1, color=COLOR_SECUNDARIO, spaceBefore=10, spaceAfter=5))
        
        nota_final = """
        <b>Cláusula de Exención y Nota Técnica:</b> Este documento automatizado compila modelos matemáticos bio-climáticos 
        asociados a los marcos de trabajo del DSL de Agro-Predict. Las alertas CRÍTICAS determinan exclusivamente que las variables de 
        campo coinciden con los rangos óptimos de desarrollo fisiológico del patógeno/insecto (p.ej. acumulación acumulada de GDD o 
        ventanas consecutivas húmedas). No sustituye la diagnosis visual de un técnico agrónomo calificado.
        """
        elementos_cierre.append(Paragraph(nota_final, estilo_resumen))
        
        story.append(KeepTogether(elementos_cierre))
        
        # Compilación final
        doc.build(
            story,
            onFirstPage=InformePlagaEstimadaService.encabezado_pie,
            onLaterPages=InformePlagaEstimadaService.encabezado_pie,
        )

        return str(ruta_pdf)