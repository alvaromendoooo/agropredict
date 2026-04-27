from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.shapes import Drawing, String
from datetime import date, datetime
from pathlib import Path
from typing import Optional
import os

# === CONFIGURACIÓN DEL INFORME === #
ruta_directorio_actual = os.getcwd()

TITULO_INFORME = "Informe de Heladas Observadas"
SUBTITULO = "Análisis de Datos Históricos — Estaciones Agrometeorológicas"
AUTOR = "Álvaro Mendo Martín"
FECHA = date.today().strftime("%d/%m/%Y")
NOMBRE_ARCHIVO = "reporte_heladas_observadas.pdf"
NOMBRE_UNIVERSIDAD = "Escuela Politécnica - Cáceres"

# === COLORES === #
COLOR_PRIMARIO = colors.HexColor("#006414")
COLOR_SECUNDARIO = colors.HexColor("#462204")
COLOR_FONDO_TABLA = colors.HexColor("#EAF4FB")
COLOR_FONDO_ALERTA = colors.HexColor("#FFF3CD")
COLOR_ACENTO = colors.red
COLOR_RIESGO_CRITICO = colors.HexColor("#DC3545")
COLOR_RIESGO_ALTO = colors.HexColor("#FD7E14")
COLOR_RIESGO_MODERADO = colors.HexColor("#FFC107")
COLOR_RIESGO_DEBIL = colors.HexColor("#17A2B8")
COLOR_SIN_RIESGO = colors.HexColor("#28A745")

# Mapa de colores por nivel de riesgo
COLORES_NIVEL = {
    "critico": COLOR_RIESGO_CRITICO,
    "alto": COLOR_RIESGO_ALTO,
    "moderado": COLOR_RIESGO_MODERADO,
    "debil": COLOR_RIESGO_DEBIL,
    "sin_riesgo": COLOR_SIN_RIESGO,
}


class InformeHeladaObservadaService:
    """
    Generador de informes PDF para predicciones de heladas observadas
    basadas en datos históricos de estaciones agrometeorológicas.

    A diferencia del informe acumulativo (futuras), este informe es
    autónomo por ejecución: resume el análisis completo del período
    histórico disponible en una única entrega estática.
    """

    # ------------------------------------------------------------------ #
    # ENCABEZADO Y PIE DE PÁGINA                                          #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _encabezado_pie(canvas_obj, doc):
        canvas_obj.saveState()
        ancho, alto = letter

        # Banda superior
        canvas_obj.setFillColor(COLOR_PRIMARIO)
        canvas_obj.rect(0, alto - 70, ancho, 70, fill=True, stroke=False)

        canvas_obj.setFillColor(colors.white)
        canvas_obj.setFont("Helvetica-Bold", 13)
        canvas_obj.drawString(1 * inch, alto - 25, TITULO_INFORME)

        canvas_obj.setFont("Helvetica", 9)
        canvas_obj.drawString(1 * inch, alto - 38, SUBTITULO)

        canvas_obj.setFont("Helvetica", 7)
        canvas_obj.drawString(1 * inch, alto - 52, "Fuente: SiAR — Red de estaciones agrometeorológicas de Extremadura")

        canvas_obj.setFont("Helvetica", 9)
        canvas_obj.drawRightString(ancho - 1 * inch, alto - 25, f"Generado: {FECHA}")

        if hasattr(doc, "periodo_analisis"):
            canvas_obj.drawRightString(ancho - 1 * inch, alto - 38, f"Período: {doc.periodo_analisis}")

        if hasattr(doc, "tipo_prediccion"):
            canvas_obj.drawRightString(ancho - 1 * inch, alto - 52, f"Tipo: {doc.tipo_prediccion.upper()}")

        canvas_obj.setStrokeColor(COLOR_SECUNDARIO)
        canvas_obj.setLineWidth(2)
        canvas_obj.line(0.75 * inch, alto - 75, ancho - 0.75 * inch, alto - 75)

        # Pie de página
        canvas_obj.setStrokeColor(COLOR_PRIMARIO)
        canvas_obj.setLineWidth(1)
        canvas_obj.line(0.75 * inch, 45, ancho - 0.75 * inch, 45)

        canvas_obj.setFillColor(COLOR_PRIMARIO)
        canvas_obj.setFont("Helvetica", 8)
        canvas_obj.drawString(1 * inch, 30, f"© {date.today().year} {AUTOR}  |  {NOMBRE_UNIVERSIDAD}")

        canvas_obj.setFont("Helvetica-Bold", 9)
        canvas_obj.drawCentredString(ancho / 2 + 8, 30, f"Página {doc.page}")

        canvas_obj.setFont("Helvetica", 8)
        canvas_obj.drawRightString(ancho - 1 * inch, 30, "Datos observados — No acumulativo")

        canvas_obj.restoreState()

    # ------------------------------------------------------------------ #
    # SECCIÓN: CONTEXTO DE CÁLCULO                                        #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _seccion_contexto(predicciones: dict, styles) -> list:
        """
        Genera la sección de contexto de cálculo detallando el período
        analizado, las fuentes de datos y los parámetros de estimación.
        """
        elementos = []

        contexto = predicciones.get("contexto", {})
        fecha_inicio = predicciones.get("fecha_comiezo_registros", "—")
        fecha_fin = predicciones.get("fecha_fin_registros", "—")
        tipo_prediccion = predicciones.get("tipo_prediccion", "—")
        fuentes = ", ".join(contexto.get("fuente", [])) or "—"
        tipos_datos = ", ".join(contexto.get("tipos_datos", [])) or "—"
        tipo_estimacion = contexto.get("prediccion_o_estimacion", "—")
        fecha_generacion_raw = contexto.get("fecha_generacion", "")

        try:
            fecha_generacion = datetime.fromisoformat(fecha_generacion_raw).strftime("%d/%m/%Y %H:%M")
        except Exception:
            fecha_generacion = fecha_generacion_raw or "—"

        # Calcular duración del período
        try:
            d_inicio = datetime.fromisoformat(fecha_inicio)
            d_fin = datetime.fromisoformat(fecha_fin)
            dias_periodo = (d_fin - d_inicio).days
        except Exception:
            dias_periodo = "—"

        datos_contexto = [
            ["Parámetro", "Valor"],
            ["Período analizado", f"{fecha_inicio} → {fecha_fin}"],
            ["Duración del período", f"{dias_periodo} días" if isinstance(dias_periodo, int) else dias_periodo],
            ["Tipo de predicción", tipo_prediccion.capitalize()],
            ["Naturaleza del cálculo", tipo_estimacion.capitalize()],
            ["Tipos de datos empleados", tipos_datos.capitalize()],
            ["Fuente de datos", fuentes],
            ["Fecha de generación del informe", fecha_generacion],
        ]

        col_widths = [2.4 * inch, 4.1 * inch]
        tabla = Table(datos_contexto, colWidths=col_widths)
        tabla.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_PRIMARIO),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (1, 1), (1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_FONDO_TABLA, colors.white]),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
            ("BOX", (0, 0), (-1, -1), 1, COLOR_PRIMARIO),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))

        elementos.append(tabla)
        elementos.append(Spacer(1, 0.12 * inch))

        nota = (
            "<b>Nota metodológica:</b> Este informe se basa exclusivamente en datos <i>observados</i> "
            "registrados por estaciones agrometeorológicas de la red SiAR. Los valores reflejan "
            "condiciones reales medidas durante el período indicado, no proyecciones futuras. "
            "Las probabilidades de helada tardía se calculan mediante análisis estadístico de la "
            "distribución histórica de temperaturas mínimas."
        )
        elementos.append(Paragraph(nota, ParagraphStyle(
            "NotaContexto", parent=styles["Normal"],
            fontSize=7, textColor=colors.grey, leading=10
        )))

        return elementos

    # ------------------------------------------------------------------ #
    # SECCIÓN: RESUMEN EJECUTIVO                                          #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _seccion_resumen(predicciones: dict, styles) -> list:
        """
        Resumen ejecutivo con el nivel de riesgo global, comentarios
        y estadísticas de temperatura mínima del período.
        """
        elementos = []

        nivel = predicciones.get("nivel", "sin_riesgo")
        comentarios = predicciones.get("comentarios", "Sin comentarios disponibles.")
        registro_temp = predicciones.get("registro_temperatura_minima", {})
        dias_bajo_cero = registro_temp.get("dias_bajo_cero", 0)
        temp_minima = registro_temp.get("temperatura_minima_registrada", None)

        color_nivel = COLORES_NIVEL.get(nivel.lower(), COLOR_SIN_RIESGO)

        estilo_normal = ParagraphStyle(
            "NormalResumen", parent=styles["Normal"],
            fontSize=10, leading=14, spaceAfter=6
        )

        # Indicador visual del nivel de riesgo global
        datos_nivel = [
            [
                Paragraph("<b>NIVEL DE RIESGO GLOBAL</b>", ParagraphStyle(
                    "NivelLabel", parent=styles["Normal"],
                    fontSize=10, textColor=colors.white, alignment=1
                )),
                Paragraph(f"<b>{nivel.upper().replace('_', ' ')}</b>", ParagraphStyle(
                    "NivelValor", parent=styles["Normal"],
                    fontSize=14, textColor=colors.white, alignment=1
                ))
            ]
        ]
        tabla_nivel = Table(datos_nivel, colWidths=[3 * inch, 3.5 * inch])
        tabla_nivel.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), color_nivel),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("BOX", (0, 0), (-1, -1), 1.5, COLOR_SECUNDARIO),
        ]))
        elementos.append(tabla_nivel)
        elementos.append(Spacer(1, 0.15 * inch))

        # Comentario de análisis
        elementos.append(Paragraph(comentarios, estilo_normal))
        elementos.append(Spacer(1, 0.1 * inch))

        # Estadísticas de temperatura mínima
        if temp_minima is not None:
            datos_stats = [
                ["Estadística", "Valor"],
                ["Temperatura mínima registrada", f"{temp_minima:.3f} °C"],
                ["Días con temperatura bajo cero", str(dias_bajo_cero)],
            ]
            tabla_stats = Table(datos_stats, colWidths=[3.2 * inch, 3.3 * inch])
            tabla_stats.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), COLOR_SECUNDARIO),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (1, 1), (1, -1), "Helvetica"),
                ("FONTSIZE", (0, 1), (-1, -1), 9),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_FONDO_TABLA, colors.white]),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
                ("BOX", (0, 0), (-1, -1), 1, COLOR_SECUNDARIO),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]))
            elementos.append(tabla_stats)

        return elementos

    # ------------------------------------------------------------------ #
    # SECCIÓN: ALERTAS                                                    #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _seccion_alertas(predicciones: dict, styles) -> list:
        """
        Muestra las alertas generadas por el análisis, clasificadas
        por nivel (informativa, advertencia, crítica).
        """
        elementos = []
        alertas = predicciones.get("alertas", [])

        estilo_normal = ParagraphStyle(
            "NormalAlerta", parent=styles["Normal"],
            fontSize=9, leading=13, spaceAfter=4
        )

        if not alertas:
            elementos.append(Paragraph(
                "No se generaron alertas durante el período analizado.",
                estilo_normal
            ))
            return elementos

        ICONOS_NIVEL = {
            "informativa": "ℹ",
            "advertencia": "⚠",
            "critica": "🔴",
        }

        COLORES_ALERTA = {
            "informativa": colors.HexColor("#D1ECF1"),
            "advertencia": colors.HexColor("#FFF3CD"),
            "critica": colors.HexColor("#F8D7DA"),
        }

        for alerta in alertas:
            nivel_alerta = alerta.get("nivel", "informativa").lower()
            icono = ICONOS_NIVEL.get(nivel_alerta, "•")
            color_fondo = COLORES_ALERTA.get(nivel_alerta, colors.HexColor("#D1ECF1"))

            datos_alerta = [[
                Paragraph(
                    f"<b>{icono} {alerta.get('mensaje', '-')}</b><br/>"
                    f"<i>Recomendación:</i> {alerta.get('recomendacion', '-')}",
                    estilo_normal
                )
            ]]
            tabla_alerta = Table(datos_alerta, colWidths=[6.5 * inch])
            tabla_alerta.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), color_fondo),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ]))
            elementos.append(tabla_alerta)
            elementos.append(Spacer(1, 4))

        return elementos

    # ------------------------------------------------------------------ #
    # SECCIÓN: EVALUACIÓN DE VARIEDADES                                   #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _seccion_variedades(predicciones: dict, styles) -> list:
        """
        Tabla detallada con la evaluación de riesgo por variedad de cultivo,
        incluyendo umbrales críticos y porcentaje de riesgo calculado.
        """
        elementos = []

        eval_variedades = predicciones.get("evaluaciones_variedades", {})
        if not eval_variedades:
            elementos.append(Paragraph(
                "No se solicitó evaluación de variedades para este análisis.",
                ParagraphStyle("Sin", parent=styles["Normal"], fontSize=9)
            ))
            return elementos

        evaluaciones = eval_variedades.get("evaluaciones", [])

        # Resumen numérico por nivel
        resumen_datos = [
            ["Total evaluadas", "Crítico", "Alto", "Moderado", "Débil", "Sin riesgo"],
            [
                str(eval_variedades.get("total_variedades_evaluados", 0)),
                str(eval_variedades.get("variedades_en_riesgo_critico", 0)),
                str(eval_variedades.get("variedades_en_riesgo_alto", 0)),
                str(eval_variedades.get("variedades_en_riesgo_moderado", 0)),
                str(eval_variedades.get("variedades_en_riesgo_debil", 0)),
                str(eval_variedades.get("variedades_sin_riesgo", 0)),
            ]
        ]

        col_widths_resumen = [1.2 * inch] * 6
        tabla_resumen = Table(resumen_datos, colWidths=col_widths_resumen)
        tabla_resumen.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_PRIMARIO),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            # Colores de celda según nivel
            ("BACKGROUND", (1, 1), (1, 1), COLOR_RIESGO_CRITICO),
            ("BACKGROUND", (2, 1), (2, 1), COLOR_RIESGO_ALTO),
            ("BACKGROUND", (3, 1), (3, 1), COLOR_RIESGO_MODERADO),
            ("BACKGROUND", (4, 1), (4, 1), COLOR_RIESGO_DEBIL),
            ("BACKGROUND", (5, 1), (5, 1), COLOR_SIN_RIESGO),
            ("TEXTCOLOR", (1, 1), (5, 1), colors.white),
            ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 1), (-1, 1), 10),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
            ("BOX", (0, 0), (-1, -1), 1, COLOR_PRIMARIO),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        elementos.append(tabla_resumen)
        elementos.append(Spacer(1, 0.15 * inch))

        if not evaluaciones:
            return elementos

        # Tabla detallada por variedad
        cabecera = [
            "Variedad", "Etapa fenológica", "Temp. evaluada",
            "% Riesgo", "Nivel", "Umbral crítico", "Umbral alto"
        ]
        datos_tabla = [cabecera]

        for ev in evaluaciones:
            umbrales = ev.get("umbrales", {})
            datos_tabla.append([
                ev.get("variedad", "—"),
                ev.get("etapa_fenologica", "—").capitalize(),
                f"{ev.get('temperatura_evaluada', 0):.3f} °C",
                f"{ev.get('porcentaje_riesgo', 0):.1f} %",
                ev.get("nivel_riesgo", "—").upper(),
                f"{umbrales.get('critico', '—')} °C",
                f"{umbrales.get('alto', '—')} °C",
            ])

        col_widths = [1.3 * inch, 1.4 * inch, 1.1 * inch, 0.8 * inch, 0.9 * inch, 1.0 * inch, 0.9 * inch]
        tabla = Table(datos_tabla, colWidths=col_widths, repeatRows=1)
        tabla.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_SECUNDARIO),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_FONDO_TABLA, colors.white]),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
            ("BOX", (0, 0), (-1, -1), 1, COLOR_SECUNDARIO),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))

        # Colorear celda del nivel por variedad
        for i, ev in enumerate(evaluaciones, start=1):
            nivel_ev = ev.get("nivel_riesgo", "sin_riesgo").lower()
            color_celda = COLORES_NIVEL.get(nivel_ev, COLOR_SIN_RIESGO)
            tabla.setStyle(TableStyle([
                ("BACKGROUND", (4, i), (4, i), color_celda),
                ("TEXTCOLOR", (4, i), (4, i), colors.white),
            ]))

        elementos.append(tabla)
        return elementos

    # ------------------------------------------------------------------ #
    # SECCIÓN: HELADAS BLANCAS Y NEGRAS                                   #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _seccion_tipos_helada(predicciones: dict, styles) -> list:
        """
        Tablas separadas para los episodios de helada blanca y negra
        detectados durante el período histórico analizado.
        """
        elementos = []

        estilo_normal = ParagraphStyle(
            "NormalHelada", parent=styles["Normal"],
            fontSize=9, leading=13, spaceAfter=4
        )
        estilo_subtitulo = ParagraphStyle(
            "SubtituloHelada", parent=styles["Normal"],
            fontSize=10, textColor=COLOR_SECUNDARIO,
            fontName="Helvetica-Bold", spaceAfter=6
        )

        heladas_blancas = predicciones.get("riesgos_heladas_blancas", [])
        heladas_negras = predicciones.get("riesgos_heladas_negras", [])

        # --- Heladas blancas ---
        elementos.append(Paragraph("Heladas Blancas (T ≤ 2°C + HR ≥ 60%)", estilo_subtitulo))

        if heladas_blancas:
            cabecera_blanca = ["Fecha", "Temperatura (°C)", "Humedad (%)", "Estación (Temp.)", "Estaciones (HR)"]
            datos_blanca = [cabecera_blanca]

            for h in heladas_blancas:
                estaciones_hr = h.get("estacion_id_hum", [])
                estaciones_hr_str = ", ".join(str(e) for e in estaciones_hr) if isinstance(estaciones_hr, list) else str(estaciones_hr)
                datos_blanca.append([
                    str(h.get("timestamp", "—")),
                    f"{h.get('temperatura', 0):.3f}",
                    f"{h.get('humedad', 0):.2f}",
                    str(h.get("estacion_id_temp", "—")),
                    estaciones_hr_str,
                ])

            col_widths_b = [1.3 * inch, 1.3 * inch, 1.2 * inch, 1.4 * inch, 1.3 * inch]
            tabla_blanca = Table(datos_blanca, colWidths=col_widths_b, repeatRows=1)
            tabla_blanca.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#AED6F1")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1A5276")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 8),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 1), (-1, -1), 8),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#EBF5FB"), colors.white]),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#1A5276")),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]))
            elementos.append(tabla_blanca)
        else:
            elementos.append(Paragraph(
                "No se detectaron episodios de helada blanca en el período analizado.",
                estilo_normal
            ))

        elementos.append(Spacer(1, 0.2 * inch))

        # --- Heladas negras ---
        elementos.append(Paragraph("Heladas Negras (T ≤ 0°C + HR < 60%)", estilo_subtitulo))

        if heladas_negras:
            cabecera_negra = ["Fecha", "Temperatura (°C)", "Estación"]
            datos_negra = [cabecera_negra]

            for h in heladas_negras:
                datos_negra.append([
                    str(h.get("timestamp", "—")),
                    f"{h.get('temperatura', 0):.3f}",
                    str(h.get("estacion_id_temp", "—")),
                ])

            col_widths_n = [2.0 * inch, 2.0 * inch, 2.5 * inch]
            tabla_negra = Table(datos_negra, colWidths=col_widths_n, repeatRows=1)
            tabla_negra.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#C0392B")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 8),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 1), (-1, -1), 8),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#FADBD8"), colors.white]),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#C0392B")),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]))
            elementos.append(tabla_negra)
        else:
            elementos.append(Paragraph(
                "No se detectaron episodios de helada negra en el período analizado.",
                estilo_normal
            ))

        return elementos

    # ------------------------------------------------------------------ #
    # GRÁFICO: EVOLUCIÓN DE TEMPERATURAS EN EPISODIOS DE HELADA BLANCA   #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _grafico_heladas_blancas(heladas_blancas: list) -> Optional[Drawing]:
        """
        Gráfico de barras con las temperaturas mínimas registradas
        en cada episodio de helada blanca detectado.
        """
        if not heladas_blancas:
            return None

        fechas = [str(h.get("timestamp", "")) for h in heladas_blancas]
        temperaturas = [round(h.get("temperatura", 0), 3) for h in heladas_blancas]

        d = Drawing(420, 180)

        bc = VerticalBarChart()
        bc.x = 50
        bc.y = 40
        bc.height = 110
        bc.width = 340
        bc.data = [temperaturas]
        bc.fillColor = colors.HexColor("#AED6F1")
        bc.bars[0].fillColor = colors.HexColor("#2E86C1")
        bc.valueAxis.valueMin = min(temperaturas) - 0.5 if temperaturas else -1
        bc.valueAxis.valueMax = max(max(temperaturas) + 0.5, 2.5)
        bc.valueAxis.valueSteps = None
        bc.categoryAxis.categoryNames = fechas
        bc.categoryAxis.labels.angle = 45
        bc.categoryAxis.labels.boxAnchor = 'e'
        bc.categoryAxis.labels.fontSize = 6
        bc.categoryAxis.labels.dy = -10

        paso = max(1, len(fechas) // 6)
        bc.categoryAxis.categoryNames = [
            f if i % paso == 0 else "" for i, f in enumerate(fechas)
        ]

        d.add(bc)

        # Etiqueta del eje Y
        etiqueta = String(10, 90, "Temp (°C)", fontSize=7, fillColor=colors.grey)
        etiqueta.textAnchor = "middle"
        d.add(etiqueta)

        return d

    # ------------------------------------------------------------------ #
    # GRÁFICO: PORCENTAJE DE RIESGO POR VARIEDAD                         #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _grafico_riesgo_variedades(evaluaciones: list) -> Optional[Drawing]:
        """
        Gráfico de barras horizontales con el porcentaje de riesgo
        calculado para cada variedad de cultivo evaluada.
        """
        if not evaluaciones:
            return None

        nombres = [ev.get("variedad", "—") for ev in evaluaciones]
        riesgos = [round(ev.get("porcentaje_riesgo", 0), 1) for ev in evaluaciones]

        d = Drawing(420, max(120, len(nombres) * 30 + 40))

        bc = VerticalBarChart()
        bc.x = 50
        bc.y = 40
        bc.height = max(80, len(nombres) * 25)
        bc.width = 340
        bc.data = [riesgos]
        bc.bars[0].fillColor = COLOR_RIESGO_ALTO
        bc.valueAxis.valueMin = 0
        bc.valueAxis.valueMax = 100
        bc.valueAxis.valueSteps = [0, 25, 50, 75, 100]
        bc.categoryAxis.categoryNames = nombres
        bc.categoryAxis.labels.fontSize = 8

        d.add(bc)

        # Etiqueta del eje Y
        etiqueta = String(10, 90, "Riesgo (%)", fontSize=7, fillColor=colors.grey)
        etiqueta.textAnchor = "middle"
        d.add(etiqueta)

        return d

    # ------------------------------------------------------------------ #
    # MÉTODO PRINCIPAL: crear_informe                                     #
    # ------------------------------------------------------------------ #

    @staticmethod
    def crear_informe(
        predicciones: dict,
        zona: Optional[str] = None,
        provincia: Optional[str] = None,
    ) -> str:
        """
        Genera un informe PDF autónomo (no acumulativo) para una predicción
        de heladas observadas basada en datos históricos.

        :param predicciones: Diccionario con la respuesta completa del servicio
        :param zona: Zona geográfica del análisis (opcional)
        :param provincia: Código o nombre de provincia (opcional)
        :return: Ruta absoluta al PDF generado
        """
        if not isinstance(predicciones, dict):
            raise ValueError("predicciones debe ser un diccionario válido")

        directorio = Path(__file__).resolve().parent / "reports"
        directorio.mkdir(parents=True, exist_ok=True)
        ruta_pdf = directorio / NOMBRE_ARCHIVO

        # Extraer período para encabezado
        fecha_inicio = predicciones.get("fecha_comiezo_registros", "")
        fecha_fin = predicciones.get("fecha_fin_registros", "")
        tipo_prediccion = predicciones.get("tipo_prediccion", "observada")

        doc = SimpleDocTemplate(
            str(ruta_pdf),
            pagesize=letter,
            topMargin=1.2 * inch,
            bottomMargin=0.9 * inch,
            leftMargin=1 * inch,
            rightMargin=1 * inch,
            title=f"{TITULO_INFORME} — {fecha_inicio} / {fecha_fin}",
            author=AUTOR,
        )

        # Metadatos para encabezado/pie dinámico
        doc.periodo_analisis = f"{fecha_inicio} → {fecha_fin}" if fecha_inicio and fecha_fin else "—"
        doc.tipo_prediccion = tipo_prediccion

        styles = getSampleStyleSheet()

        estilo_titulo_seccion = ParagraphStyle(
            "TituloSeccion",
            parent=styles["Heading1"],
            fontSize=12,
            textColor=COLOR_PRIMARIO,
            spaceAfter=6,
            spaceBefore=14,
        )
        estilo_normal = ParagraphStyle(
            "NormalDoc",
            parent=styles["Normal"],
            fontSize=10,
            leading=14,
            spaceAfter=6,
        )

        story = []

        # ── PORTADA ──────────────────────────────────────────────────── #
        story.append(Spacer(1, 0.4 * inch))
        story.append(Paragraph(
            "INFORME DE HELADAS OBSERVADAS",
            ParagraphStyle("Portada", parent=estilo_titulo_seccion, fontSize=17, alignment=1)
        ))
        story.append(Paragraph(
            "Análisis Histórico de Datos Agrometeorológicos",
            ParagraphStyle("SubPortada", parent=styles["Normal"], fontSize=11,
                           textColor=colors.grey, alignment=1, spaceAfter=4)
        ))
        story.append(Spacer(1, 0.1 * inch))

        # Ficha de portada
        datos_portada = [
            ["Período analizado", f"{fecha_inicio} → {fecha_fin}"],
            ["Zona / Provincia", f"{zona or '—'}  /  {provincia or '—'}"],
            ["Nivel de riesgo global", predicciones.get("nivel", "—").upper().replace("_", " ")],
            ["Tipo de predicción", tipo_prediccion.capitalize()],
            ["Fecha del informe", FECHA],
        ]
        tabla_portada = Table(datos_portada, colWidths=[2.3 * inch, 4.2 * inch])
        tabla_portada.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [COLOR_FONDO_TABLA, colors.white]),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
            ("BOX", (0, 0), (-1, -1), 1, COLOR_PRIMARIO),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(tabla_portada)
        story.append(Spacer(1, 0.15 * inch))

        # ── 1. CONTEXTO DE CÁLCULO ───────────────────────────────────── #
        story.append(KeepTogether([
            Paragraph("1. CONTEXTO DE CÁLCULO", estilo_titulo_seccion),
            HRFlowable(width="100%", thickness=1, color=COLOR_SECUNDARIO, spaceAfter=6),
            Spacer(1, 6),
        ]))
        story.extend(InformeHeladaObservadaService._seccion_contexto(predicciones, styles))
        story.append(Spacer(1, 0.2 * inch))

        # ── 2. RESUMEN EJECUTIVO ─────────────────────────────────────── #
        story.append(KeepTogether([
            Paragraph("2. RESUMEN EJECUTIVO", estilo_titulo_seccion),
            HRFlowable(width="100%", thickness=1, color=COLOR_SECUNDARIO, spaceAfter=6),
            Spacer(1, 6),
        ]))
        story.extend(InformeHeladaObservadaService._seccion_resumen(predicciones, styles))
        story.append(Spacer(1, 0.2 * inch))

        # ── 3. ALERTAS DETECTADAS ────────────────────────────────────── #
        story.append(KeepTogether([
            Paragraph("3. ALERTAS DETECTADAS", estilo_titulo_seccion),
            HRFlowable(width="100%", thickness=1, color=COLOR_SECUNDARIO, spaceAfter=6),
            Spacer(1, 6),
        ]))
        story.extend(InformeHeladaObservadaService._seccion_alertas(predicciones, styles))
        story.append(Spacer(1, 0.2 * inch))

        # ── 4. EPISODIOS DE HELADA ───────────────────────────────────── #
        story.append(PageBreak())
        story.append(Paragraph("4. EPISODIOS DE HELADA REGISTRADOS", estilo_titulo_seccion))
        story.append(HRFlowable(width="100%", thickness=1, color=COLOR_SECUNDARIO, spaceAfter=6))
        story.append(Spacer(1, 6))
        story.extend(InformeHeladaObservadaService._seccion_tipos_helada(predicciones, styles))
        story.append(Spacer(1, 0.2 * inch))

        # Gráfico de temperaturas en episodios de helada blanca
        heladas_blancas = predicciones.get("riesgos_heladas_blancas", [])
        grafico_blancas = InformeHeladaObservadaService._grafico_heladas_blancas(heladas_blancas)
        if grafico_blancas:
            story.append(Paragraph(
                "Evolución de temperaturas — Episodios de helada blanca",
                ParagraphStyle("GraficoTitulo", parent=styles["Normal"],
                               fontSize=9, textColor=colors.grey, spaceAfter=4)
            ))
            story.append(grafico_blancas)
            story.append(Spacer(1, 0.15 * inch))

        # ── 5. EVALUACIÓN DE VARIEDADES ──────────────────────────────── #
        eval_variedades = predicciones.get("evaluaciones_variedades")
        if eval_variedades:
            story.append(PageBreak())
            story.append(Paragraph("5. EVALUACIÓN DE VARIEDADES DE CULTIVO", estilo_titulo_seccion))
            story.append(HRFlowable(width="100%", thickness=1, color=COLOR_SECUNDARIO, spaceAfter=6))
            story.append(Spacer(1, 6))
            story.extend(InformeHeladaObservadaService._seccion_variedades(predicciones, styles))
            story.append(Spacer(1, 0.2 * inch))

            # Gráfico de riesgo por variedad
            evaluaciones = eval_variedades.get("evaluaciones", [])
            grafico_variedades = InformeHeladaObservadaService._grafico_riesgo_variedades(evaluaciones)
            if grafico_variedades:
                story.append(Paragraph(
                    "Porcentaje de riesgo por variedad evaluada",
                    ParagraphStyle("GraficoTituloVar", parent=styles["Normal"],
                                   fontSize=9, textColor=colors.grey, spaceAfter=4)
                ))
                story.append(grafico_variedades)

        # Construir PDF
        doc.build(
            story,
            onFirstPage=InformeHeladaObservadaService._encabezado_pie,
            onLaterPages=InformeHeladaObservadaService._encabezado_pie,
        )

        print(f"Informe de heladas observadas generado: {ruta_pdf}")
        return str(ruta_pdf)