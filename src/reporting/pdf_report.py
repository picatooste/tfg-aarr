"""
Generacion de informes PDF profesionales a partir de un InformeAARR.

Paleta corporativa (azul oscuro + ambar) coherente con informes del
sector ciberseguridad. Incluye portada, cabecera y pie en todas las
paginas, KPIs tipo dashboard, badges de nivel y bandas alternas.
"""

from datetime import datetime
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
    KeepTogether,
)
from reportlab.pdfgen import canvas

from src.catalogos import amenaza as get_amenaza, salvaguarda as get_salvaguarda
from src.models import FichaAplicacion, InformeAARR


# =============================================================================
# PALETA CORPORATIVA
# =============================================================================

AZUL_PRIMARIO = colors.HexColor("#0f2846")   # azul marino profundo
AZUL_SECUNDARIO = colors.HexColor("#1e3a5f")  # azul medio
AMBAR = colors.HexColor("#d97706")            # ambar/naranja de alerta
AMBAR_CLARO = colors.HexColor("#fef3c7")

GRIS_TEXTO = colors.HexColor("#1f2937")
GRIS_MUTED = colors.HexColor("#6b7280")
GRIS_BORDE = colors.HexColor("#d1d5db")
GRIS_BANDA = colors.HexColor("#f9fafb")
BLANCO = colors.HexColor("#ffffff")

COLOR_NIVEL = {
    "critico": colors.HexColor("#991b1b"),  # rojo oscuro
    "alto": colors.HexColor("#c2410c"),     # naranja
    "medio": colors.HexColor("#a16207"),    # ambar oscuro
    "bajo": colors.HexColor("#15803d"),     # verde oscuro
}


# =============================================================================
# ESTILOS DE TEXTO
# =============================================================================

_styles = getSampleStyleSheet()

_TITULO_PORTADA = ParagraphStyle(
    "TituloPortada", parent=_styles["Heading1"],
    fontSize=28, leading=34, textColor=BLANCO,
    alignment=TA_LEFT, spaceAfter=0,
)
_SUBTITULO_PORTADA = ParagraphStyle(
    "SubtituloPortada", parent=_styles["Heading2"],
    fontSize=14, textColor=AMBAR_CLARO, spaceAfter=0,
)
_META_PORTADA = ParagraphStyle(
    "MetaPortada", parent=_styles["BodyText"],
    fontSize=10, textColor=BLANCO, leading=14,
)
_H1 = ParagraphStyle(
    "H1", parent=_styles["Heading1"],
    fontSize=16, leading=20, textColor=AZUL_PRIMARIO,
    spaceBefore=12, spaceAfter=8,
    borderPadding=0,
)
_H2 = ParagraphStyle(
    "H2", parent=_styles["Heading2"],
    fontSize=12, leading=16, textColor=AZUL_SECUNDARIO,
    spaceBefore=8, spaceAfter=6, fontName="Helvetica-Bold",
)
_H3 = ParagraphStyle(
    "H3", parent=_styles["Heading3"],
    fontSize=10, leading=13, textColor=AZUL_PRIMARIO,
    spaceBefore=6, spaceAfter=4, fontName="Helvetica-Bold",
)
_CUERPO = ParagraphStyle(
    "Cuerpo", parent=_styles["BodyText"],
    fontSize=9.5, leading=13, textColor=GRIS_TEXTO,
    alignment=TA_JUSTIFY, spaceAfter=6,
)
_MUTED = ParagraphStyle(
    "Muted", parent=_styles["BodyText"],
    fontSize=8, textColor=GRIS_MUTED, leading=11,
)
_KPI_LABEL = ParagraphStyle(
    "KpiLabel", parent=_styles["BodyText"],
    fontSize=8, textColor=GRIS_MUTED, alignment=TA_CENTER,
    fontName="Helvetica", spaceAfter=2,
)
_KPI_VALUE = ParagraphStyle(
    "KpiValue", parent=_styles["BodyText"],
    fontSize=22, textColor=AZUL_PRIMARIO, alignment=TA_CENTER,
    fontName="Helvetica-Bold", leading=26, spaceAfter=0,
)
# Estilos para texto DENTRO de celdas de tabla (permiten wrap)
_CELDA_LABEL = ParagraphStyle(
    "CeldaLabel", parent=_styles["BodyText"],
    fontSize=9, leading=12, textColor=BLANCO,
    fontName="Helvetica-Bold", alignment=TA_LEFT,
)
_CELDA_VALOR = ParagraphStyle(
    "CeldaValor", parent=_styles["BodyText"],
    fontSize=9, leading=12, textColor=GRIS_TEXTO,
    alignment=TA_LEFT,
)


# =============================================================================
# CABECERA Y PIE DE PAGINA (en todas las hojas excepto portada)
# =============================================================================

def _crear_cabecera_pie(nombre_app: str):
    """Devuelve una funcion que reportlab usa para pintar cada pagina."""
    def _dibujar(canv: canvas.Canvas, doc):
        canv.saveState()

        # Cabecera: linea fina con el nombre de la app y "Informe AARR"
        canv.setStrokeColor(GRIS_BORDE)
        canv.setLineWidth(0.5)
        canv.line(2 * cm, A4[1] - 1.2 * cm, A4[0] - 2 * cm, A4[1] - 1.2 * cm)
        canv.setFont("Helvetica-Bold", 8)
        canv.setFillColor(AZUL_PRIMARIO)
        canv.drawString(2 * cm, A4[1] - 1 * cm, "INFORME AARR")
        canv.setFont("Helvetica", 8)
        canv.setFillColor(GRIS_MUTED)
        canv.drawRightString(A4[0] - 2 * cm, A4[1] - 1 * cm, nombre_app)

        # Pie: linea fina + marca + numero de pagina
        canv.line(2 * cm, 1.2 * cm, A4[0] - 2 * cm, 1.2 * cm)
        canv.setFont("Helvetica", 7)
        canv.setFillColor(GRIS_MUTED)
        canv.drawString(
            2 * cm, 0.8 * cm,
            "Generado automaticamente por la Herramienta AARR con IA (TFG)",
        )
        canv.drawRightString(
            A4[0] - 2 * cm, 0.8 * cm,
            f"Pagina {doc.page}",
        )

        canv.restoreState()

    def _primera_pagina(canv: canvas.Canvas, doc):
        """La portada no lleva cabecera ni pie."""
        pass

    return _dibujar, _primera_pagina


# =============================================================================
# SECCIONES
# =============================================================================

def _seccion_portada(ficha: FichaAplicacion, informe: InformeAARR) -> list:
    """Portada con bloque de color azul y texto en blanco."""
    # Bloque de color de la portada (tabla con fondo que ocupa la pagina)
    contenido_portada = [
        [Paragraph("Analisis de Riesgos de Aplicacion", _SUBTITULO_PORTADA)],
        [Spacer(1, 0.3 * cm)],
        [Paragraph(ficha.nombre, _TITULO_PORTADA)],
        [Spacer(1, 1.5 * cm)],
        [Paragraph(
            f"<b>Fecha de emision:</b> {informe.fecha_analisis.strftime('%d de %B de %Y')}<br/>"
            f"<b>Area responsable:</b> {ficha.area_responsable}<br/>"
            f"<b>Service Manager:</b> {ficha.service_manager}<br/>"
            f"<b>Arquitecto:</b> {ficha.arquitecto}<br/>"
            f"<br/>"
            f"<b>Metodologia:</b> MAGERIT (cualitativo escalado)<br/>"
            f"<b>Motor de inteligencia:</b> {informe.modelo_ia}",
            _META_PORTADA,
        )],
    ]

    bloque = Table(
        contenido_portada,
        colWidths=[17 * cm],
        rowHeights=[None] * len(contenido_portada),
    )
    bloque.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), AZUL_PRIMARIO),
        ("LEFTPADDING", (0, 0), (-1, -1), 2 * cm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2 * cm),
        ("TOPPADDING", (0, 0), (0, 0), 5 * cm),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 5 * cm),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))

    # Marca ambar a modo de "acento" al pie de la portada
    marca = Table(
        [[" "]],
        colWidths=[17 * cm],
        rowHeights=[0.4 * cm],
    )
    marca.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), AMBAR),
    ]))

    return [bloque, marca, PageBreak()]


def _kpi_card(label: str, valor: str, color_valor=None) -> Table:
    """Tarjeta tipo KPI (metrica grande + etiqueta pequena)."""
    estilo_valor = ParagraphStyle(
        "V", parent=_KPI_VALUE,
        textColor=color_valor or AZUL_PRIMARIO,
    )
    t = Table(
        [[Paragraph(label.upper(), _KPI_LABEL)],
         [Paragraph(str(valor), estilo_valor)]],
        colWidths=[4 * cm],
        rowHeights=[0.6 * cm, 1.4 * cm],
    )
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), GRIS_BANDA),
        ("BOX", (0, 0), (-1, -1), 0.5, GRIS_BORDE),
        ("LINEBELOW", (0, 0), (-1, 0), 2, AMBAR),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def _seccion_resumen_ejecutivo(informe: InformeAARR) -> list:
    total = len(informe.riesgos_residuales)
    conteo = {"critico": 0, "alto": 0, "medio": 0, "bajo": 0}
    for r in informe.riesgos_residuales:
        conteo[r.nivel.value] += 1
    ajustes = sum(
        1 for v in informe.valoraciones if v.fuente == "llm_ajustado_humano"
    )

    # Fila de 4 KPIs principales
    fila_kpis = Table(
        [[
            _kpi_card("Amenazas evaluadas", str(total)),
            _kpi_card("Nivel critico", str(conteo["critico"]), COLOR_NIVEL["critico"]),
            _kpi_card("Nivel alto", str(conteo["alto"]), COLOR_NIVEL["alto"]),
            _kpi_card("Nivel medio", str(conteo["medio"]), COLOR_NIVEL["medio"]),
        ]],
        colWidths=[4.25 * cm] * 4,
    )
    fila_kpis.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
    ]))

    fila_secundaria = Table(
        [[
            _kpi_card("Nivel bajo", str(conteo["bajo"]), COLOR_NIVEL["bajo"]),
            _kpi_card("Salvaguardas", str(len(informe.salvaguardas_implantadas))),
            _kpi_card("Ajustes del analista", f"{ajustes}/{total}"),
            _kpi_card("Motor IA", informe.modelo_ia.split("-")[0].title()),
        ]],
        colWidths=[4.25 * cm] * 4,
    )
    fila_secundaria.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
    ]))

    return [
        Paragraph("Resumen ejecutivo", _H1),
        fila_kpis,
        Spacer(1, 0.3 * cm),
        fila_secundaria,
        Spacer(1, 0.6 * cm),
    ]

def _seccion_ficha(ficha: FichaAplicacion) -> list:
    datos = [
        ("Descripcion", ficha.descripcion),
        ("Modelo de servicio", ficha.modelo_servicio.value),
        ("Proveedor", ficha.proveedor),
        ("Host", ficha.host.value),
        ("Total usuarios",
         str(sum(g.numero_usuarios for g in ficha.grupos_usuarios))),
        ("Obsolescencia",
         f"{ficha.estado_tecnico.porcentaje_obsolescencia}%"),
        ("Vulnerabilidades DAST (identif./correg.)",
         f"{ficha.estado_tecnico.amenazas_dast_identificadas} / "
         f"{ficha.estado_tecnico.amenazas_dast_corregidas}"),
        ("Vulnerabilidades SAST (identif./correg.)",
         f"{ficha.estado_tecnico.amenazas_sast_identificadas} / "
         f"{ficha.estado_tecnico.amenazas_sast_corregidas}"),
    ]
    filas = [
        [Paragraph(etiqueta, _CELDA_LABEL), Paragraph(str(valor), _CELDA_VALOR)]
        for etiqueta, valor in datos
    ]

    tabla = Table(filas, colWidths=[6 * cm, 11 * cm])
    estilo = TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 0), (0, -1), AZUL_SECUNDARIO),
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, GRIS_BORDE),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ])
    for i in range(len(filas)):
        if i % 2 == 0:
            estilo.add("BACKGROUND", (1, i), (1, i), GRIS_BANDA)
    tabla.setStyle(estilo)

    return [
        Paragraph("Ficha de la aplicacion", _H1),
        tabla,
        Spacer(1, 0.5 * cm),
    ]


def _seccion_salvaguardas(informe: InformeAARR) -> list:
    if not informe.salvaguardas_implantadas:
        return [
            Paragraph("Salvaguardas implantadas", _H1),
            Paragraph("No hay salvaguardas implantadas registradas para esta aplicacion.", _CUERPO),
            Spacer(1, 0.5 * cm),
        ]

    filas = [[
        Paragraph("ID", _CELDA_LABEL),
        Paragraph("Salvaguarda", _CELDA_LABEL),
        Paragraph("Descripcion", _CELDA_LABEL),
    ]]
    for s in informe.salvaguardas_implantadas:
        sal = get_salvaguarda(s.salvaguarda_id)
        filas.append([
            Paragraph(sal.id, _CELDA_VALOR),
            Paragraph(sal.nombre, _CELDA_VALOR),
            Paragraph(sal.descripcion, _CELDA_VALOR),
        ])

    tabla = Table(filas, colWidths=[2 * cm, 5 * cm, 10 * cm], repeatRows=1)
    estilo = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), AZUL_PRIMARIO),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("LINEBELOW", (0, 0), (-1, -1), 0.3, GRIS_BORDE),
    ])
    for i in range(1, len(filas)):
        if i % 2 == 0:
            estilo.add("BACKGROUND", (0, i), (-1, i), GRIS_BANDA)
    tabla.setStyle(estilo)

    return [
        Paragraph("Salvaguardas implantadas", _H1),
        tabla,
        Spacer(1, 0.5 * cm),
    ]


def _badge_nivel(nivel: str) -> Table:
    """Pequena 'etiqueta' con fondo pleno segun nivel."""
    color = COLOR_NIVEL.get(nivel, GRIS_MUTED)
    t = Table([[nivel.upper()]], colWidths=[1.8 * cm], rowHeights=[0.5 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), color),
        ("TEXTCOLOR", (0, 0), (-1, -1), BLANCO),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


def _seccion_tabla_riesgos(informe: InformeAARR) -> list:
    riesgos_ord = sorted(
        informe.riesgos_residuales,
        key=lambda r: r.valor_residual, reverse=True,
    )


    filas = [[
        Paragraph("ID", _CELDA_LABEL),
        Paragraph("Amenaza", _CELDA_LABEL),
        Paragraph("Inherente", _CELDA_LABEL),
        Paragraph("Residual", _CELDA_LABEL),
        Paragraph("Reduccion", _CELDA_LABEL),
        Paragraph("Nivel", _CELDA_LABEL),
    ]]
    for r in riesgos_ord:
        nombre = get_amenaza(r.amenaza_id).nombre
        reduccion_txt = (
            f"{r.reduccion_total * 100:.0f}%" if r.valor_inherente > 0 else "—"
        )
        filas.append([
            Paragraph(r.amenaza_id, _CELDA_VALOR),
            Paragraph(nombre, _CELDA_VALOR),
            Paragraph(f"{r.valor_inherente:.2f}", _CELDA_VALOR),
            Paragraph(f"{r.valor_residual:.2f}", _CELDA_VALOR),
            Paragraph(reduccion_txt, _CELDA_VALOR),
            _badge_nivel(r.nivel.value),
        ])

    tabla = Table(
        filas,
        colWidths=[1.8 * cm, 6.7 * cm, 1.8 * cm, 1.8 * cm, 2 * cm, 2.2 * cm],
        repeatRows=1,
    )
    estilo = TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("BACKGROUND", (0, 0), (-1, 0), AZUL_PRIMARIO),
        ("TEXTCOLOR", (0, 0), (-1, 0), BLANCO),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, 0), "LEFT"),
        ("ALIGN", (2, 1), (4, -1), "RIGHT"),
        ("ALIGN", (5, 1), (5, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("LINEBELOW", (0, 0), (-1, -1), 0.3, GRIS_BORDE),
    ])
    for i in range(1, len(filas)):
        if i % 2 == 0:
            estilo.add("BACKGROUND", (0, i), (-1, i), GRIS_BANDA)
    tabla.setStyle(estilo)

    return [
        Paragraph("Riesgos identificados", _H1),
        Paragraph(
            "Lista completa ordenada por valor de riesgo residual descendente.",
            _MUTED,
        ),
        Spacer(1, 0.3 * cm),
        tabla,
        Spacer(1, 0.5 * cm),
    ]


def _seccion_detalle_top(informe: InformeAARR, n: int = 3) -> list:
    riesgos_ord = sorted(
        informe.riesgos_residuales,
        key=lambda r: r.valor_residual, reverse=True,
    )[:n]
    val_por_id = {v.amenaza_id: v for v in informe.valoraciones}

    elementos = [
        PageBreak(),
        Paragraph(f"Analisis detallado - Top {n} riesgos", _H1),
        Paragraph(
            "Detalle de los riesgos residuales mas significativos con "
            "la justificacion generada por el motor de inteligencia (y "
            "ajustes del analista cuando aplique).",
            _MUTED,
        ),
        Spacer(1, 0.4 * cm),
    ]

    for r in riesgos_ord:
        amenaza = get_amenaza(r.amenaza_id)
        val = val_por_id[r.amenaza_id]
        etiqueta_fuente = (
            "Ajustado por analista" if val.fuente == "llm_ajustado_humano"
            else "Propuesto por LLM"
        )

        # Cabecera de la ficha de riesgo
        cabecera = Table(
            [[
                Paragraph(f"<b>{amenaza.nombre}</b>", _H2),
                _badge_nivel(r.nivel.value),
            ]],
            colWidths=[13 * cm, 2.5 * cm],
        )
        cabecera.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ]))

        # Caja con metricas de la amenaza
        metricas = Table(
            [
                ["Ocurrencia", "Impacto economico", "Impacto operacional", "Valor residual"],
                [val.ocurrencia.value, val.impacto_economico.value,
                 val.impacto_operacional.value, f"{r.valor_residual:.2f}"],
            ],
            colWidths=[4 * cm] * 4,
        )
        metricas.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, 0), 7.5),
            ("FONTSIZE", (0, 1), (-1, 1), 11),
            ("TEXTCOLOR", (0, 0), (-1, 0), GRIS_MUTED),
            ("TEXTCOLOR", (0, 1), (-1, 1), AZUL_PRIMARIO),
            ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BACKGROUND", (0, 0), (-1, -1), GRIS_BANDA),
            ("BOX", (0, 0), (-1, -1), 0.5, GRIS_BORDE),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))

        bloque = KeepTogether([
            cabecera,
            Paragraph(
                f"<font color='#6b7280' size='7.5'>{r.amenaza_id}  ·  {etiqueta_fuente}</font>",
                _MUTED,
            ),
            Spacer(1, 0.2 * cm),
            metricas,
            Spacer(1, 0.2 * cm),
            Paragraph(
                f"<b>Justificacion:</b> {val.justificacion}",
                _CUERPO,
            ),
            Spacer(1, 0.6 * cm),
        ])
        elementos.append(bloque)

    return elementos


def _seccion_metodologia() -> list:
    return [
        PageBreak(),
        Paragraph("Metodologia", _H1),
        Paragraph(
            "El analisis sigue el metodo cualitativo escalado de MAGERIT. "
            "Para cada amenaza del catalogo se estima su Ocurrencia "
            "(N/A, Anual, Mensual, Semanal) y dos dimensiones de Impacto "
            "(economico y operacional; N/A, Limitado, Medio, Relevante). "
            "El motor de calculo aplica las siguientes formulas:",
            _CUERPO,
        ),
        Spacer(1, 0.2 * cm),

        Paragraph("Riesgo inherente", _H3),
        Paragraph(
            "<i>riesgo_inherente = peso(Ocurrencia) &#215; promedio(peso(Imp. Economico), peso(Imp. Operacional))</i>",
            _CUERPO,
        ),

        Paragraph("Reduccion combinada por salvaguardas", _H3),
        Paragraph(
            "<i>reduccion_total = 1 &#8722; &#928;(1 &#8722; grado_mitigacion<sub>i</sub>)</i> "
            "para cada salvaguarda i implantada aplicable",
            _CUERPO,
        ),

        Paragraph("Riesgo residual", _H3),
        Paragraph(
            "<i>riesgo_residual = riesgo_inherente &#215; (1 &#8722; reduccion_total)</i>",
            _CUERPO,
        ),

        Spacer(1, 0.3 * cm),
        Paragraph(
            "<b>Por que la acumulacion probabilistica.</b> El uso de "
            "acumulacion probabilistica para combinar salvaguardas (en lugar "
            "de sumar sus grados) evita valores absurdos: dos salvaguardas "
            "que mitigan el 50% cada una, aplicadas en paralelo, reducen el "
            "riesgo un 75%, no un 100%. Este criterio modela correctamente "
            "la probabilidad de que al menos una salvaguarda actue.",
            _CUERPO,
        ),

        Paragraph(
            "<b>Umbrales de nivel</b> sobre la escala 0-9: bajo [0, 1.5), "
            "medio [1.5, 3.5), alto [3.5, 6.5), critico [6.5, 9]. "
            "Los pesos ordinales (Ocurrencia: 0, 1, 2, 3; Impacto: 0, 1, 2, 3) "
            "y umbrales son parametrizables sin modificar la logica.",
            _CUERPO,
        ),

        Paragraph(
            "<b>Human-in-the-loop.</b> Las valoraciones son propuestas "
            "automaticamente por un modelo de lenguaje a partir de la ficha "
            "de aplicacion. El analista puede ajustar cualquier valoracion "
            "y texto de justificacion antes del calculo definitivo. Cada "
            "valoracion conserva la trazabilidad de su origen "
            "('Propuesto por LLM' o 'Ajustado por analista').",
            _CUERPO,
        ),
    ]


# =============================================================================
# API PUBLICA
# =============================================================================

def generar_informe_pdf(
    ficha: FichaAplicacion,
    informe: InformeAARR,
) -> bytes:
    """Devuelve el PDF completo como bytes."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=1.8 * cm, bottomMargin=1.8 * cm,
        title=f"AARR - {ficha.nombre}",
        author="Herramienta AARR con IA (TFG)",
    )

    elementos = []
    elementos += _seccion_portada(ficha, informe)
    elementos += _seccion_resumen_ejecutivo(informe)
    elementos += _seccion_ficha(ficha)
    elementos += _seccion_salvaguardas(informe)
    elementos += _seccion_tabla_riesgos(informe)
    elementos += _seccion_detalle_top(informe, n=3)
    elementos += _seccion_metodologia()

    dibujar, primera = _crear_cabecera_pie(ficha.nombre)
    doc.build(elementos, onFirstPage=primera, onLaterPages=dibujar)

    return buffer.getvalue()