"""
Generacion de informes PDF a partir de un InformeAARR.

Se apoya en reportlab (sin dependencias binarias) y devuelve el PDF
como bytes, listo para descargar desde la UI o guardar a disco.
"""

from datetime import datetime
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
)

from src.catalogos import amenaza as get_amenaza, salvaguarda as get_salvaguarda
from src.models import FichaAplicacion, InformeAARR


# =============================================================================
# ESTILOS
# =============================================================================

_styles = getSampleStyleSheet()

_ESTILO_TITULO = ParagraphStyle(
    "Titulo", parent=_styles["Heading1"],
    fontSize=20, spaceAfter=14, textColor=colors.HexColor("#1f2937"),
)
_ESTILO_SUBTITULO = ParagraphStyle(
    "Subtitulo", parent=_styles["Heading2"],
    fontSize=14, spaceAfter=10, textColor=colors.HexColor("#374151"),
)
_ESTILO_H3 = ParagraphStyle(
    "H3", parent=_styles["Heading3"],
    fontSize=11, spaceAfter=6, textColor=colors.HexColor("#4b5563"),
)
_ESTILO_TEXTO = ParagraphStyle(
    "Texto", parent=_styles["BodyText"],
    fontSize=9, spaceAfter=6, leading=12,
)
_ESTILO_MUTED = ParagraphStyle(
    "Muted", parent=_styles["BodyText"],
    fontSize=8, textColor=colors.HexColor("#6b7280"),
)


# =============================================================================
# COLORES DE NIVEL DE RIESGO (coherentes con la UI)
# =============================================================================

_COLORES_NIVEL = {
    "critico": colors.HexColor("#f8b4b4"),
    "alto": colors.HexColor("#fcd9a8"),
    "medio": colors.HexColor("#fff2cc"),
    "bajo": colors.HexColor("#d9ead3"),
}


# =============================================================================
# CONSTRUCCION DE SECCIONES
# =============================================================================

def _seccion_portada(ficha: FichaAplicacion, informe: InformeAARR) -> list:
    elementos = []
    elementos.append(Paragraph("Informe de Analisis de Riesgos", _ESTILO_TITULO))
    elementos.append(Paragraph(
        f"Aplicacion: <b>{ficha.nombre}</b>", _ESTILO_SUBTITULO,
    ))
    elementos.append(Spacer(1, 0.3 * cm))
    elementos.append(Paragraph(
        f"Fecha del analisis: {informe.fecha_analisis.strftime('%Y-%m-%d %H:%M')}<br/>"
        f"Modelo de IA empleado: {informe.modelo_ia}<br/>"
        f"Metodologia: MAGERIT (metodo cualitativo escalado)",
        _ESTILO_TEXTO,
    ))
    return elementos


def _seccion_resumen_ejecutivo(informe: InformeAARR) -> list:
    total = len(informe.riesgos_residuales)
    conteo = {"critico": 0, "alto": 0, "medio": 0, "bajo": 0}
    for r in informe.riesgos_residuales:
        conteo[r.nivel.value] += 1
    ajustes = sum(1 for v in informe.valoraciones if v.fuente == "llm_ajustado_humano")

    tabla = Table(
        [
            ["Amenazas evaluadas", str(total)],
            ["Nivel critico", str(conteo["critico"])],
            ["Nivel alto", str(conteo["alto"])],
            ["Nivel medio", str(conteo["medio"])],
            ["Nivel bajo", str(conteo["bajo"])],
            ["Ajustes del analista", f"{ajustes} / {total}"],
            ["Salvaguardas implantadas", str(len(informe.salvaguardas_implantadas))],
        ],
        colWidths=[6 * cm, 4 * cm],
    )
    tabla.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f3f4f6")),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d1d5db")),
        ("PADDING", (0, 0), (-1, -1), 4),
    ]))

    return [
        Paragraph("Resumen ejecutivo", _ESTILO_SUBTITULO),
        tabla,
        Spacer(1, 0.5 * cm),
    ]


def _seccion_ficha(ficha: FichaAplicacion) -> list:
    filas = [
        ["Descripcion", ficha.descripcion],
        ["Area responsable", ficha.area_responsable],
        ["Service Manager", ficha.service_manager],
        ["Arquitecto", ficha.arquitecto],
        ["Modelo de servicio", ficha.modelo_servicio.value],
        ["Proveedor", ficha.proveedor],
        ["Host", ficha.host.value],
        ["Total usuarios",
         str(sum(g.numero_usuarios for g in ficha.grupos_usuarios))],
        ["Obsolescencia (%)",
         f"{ficha.estado_tecnico.porcentaje_obsolescencia}%"],
        ["DAST identificadas / corregidas",
         f"{ficha.estado_tecnico.amenazas_dast_identificadas} / "
         f"{ficha.estado_tecnico.amenazas_dast_corregidas}"],
        ["SAST identificadas / corregidas",
         f"{ficha.estado_tecnico.amenazas_sast_identificadas} / "
         f"{ficha.estado_tecnico.amenazas_sast_corregidas}"],
    ]
    tabla = Table(filas, colWidths=[5 * cm, 12 * cm])
    tabla.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f3f4f6")),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d1d5db")),
        ("PADDING", (0, 0), (-1, -1), 4),
    ]))
    return [
        Paragraph("Ficha de la aplicacion", _ESTILO_SUBTITULO),
        tabla,
        Spacer(1, 0.5 * cm),
    ]


def _seccion_salvaguardas(informe: InformeAARR) -> list:
    if not informe.salvaguardas_implantadas:
        return [
            Paragraph("Salvaguardas implantadas", _ESTILO_SUBTITULO),
            Paragraph("No hay salvaguardas implantadas registradas.", _ESTILO_TEXTO),
            Spacer(1, 0.5 * cm),
        ]

    filas = [["ID", "Salvaguarda"]]
    for s in informe.salvaguardas_implantadas:
        sal = get_salvaguarda(s.salvaguarda_id)
        filas.append([sal.id, sal.nombre])

    tabla = Table(filas, colWidths=[2.5 * cm, 14.5 * cm])
    tabla.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e5e7eb")),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d1d5db")),
        ("PADDING", (0, 0), (-1, -1), 4),
    ]))
    return [
        Paragraph("Salvaguardas implantadas", _ESTILO_SUBTITULO),
        tabla,
        Spacer(1, 0.5 * cm),
    ]


def _seccion_tabla_riesgos(informe: InformeAARR) -> list:
    riesgos_ord = sorted(
        informe.riesgos_residuales,
        key=lambda r: r.valor_residual, reverse=True,
    )

    filas = [["ID", "Amenaza", "Inh.", "Res.", "Reduc.", "Nivel"]]
    estilos_extra = []
    for i, r in enumerate(riesgos_ord, start=1):
        nombre = get_amenaza(r.amenaza_id).nombre
        filas.append([
            r.amenaza_id, nombre,
            f"{r.valor_inherente:.2f}", f"{r.valor_residual:.2f}",
            f"{r.reduccion_total * 100:.0f}%" if r.valor_inherente > 0 else "—",
            r.nivel.value,
        ])
        # Colorear la celda de nivel
        if r.nivel.value in _COLORES_NIVEL:
            estilos_extra.append(("BACKGROUND", (5, i), (5, i), _COLORES_NIVEL[r.nivel.value]))

    tabla = Table(
        filas,
        colWidths=[2 * cm, 7 * cm, 1.5 * cm, 1.5 * cm, 1.8 * cm, 2 * cm],
        repeatRows=1,
    )
    estilo = TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e5e7eb")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d1d5db")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (2, 1), (4, -1), "RIGHT"),
        ("PADDING", (0, 0), (-1, -1), 3),
    ])
    for extra in estilos_extra:
        estilo.add(*extra)
    tabla.setStyle(estilo)

    return [
        Paragraph("Tabla completa de riesgos (ordenados por residual)", _ESTILO_SUBTITULO),
        tabla,
        Spacer(1, 0.5 * cm),
    ]


def _seccion_detalle_top(informe: InformeAARR, n: int = 3) -> list:
    riesgos_ord = sorted(
        informe.riesgos_residuales,
        key=lambda r: r.valor_residual, reverse=True,
    )[:n]
    val_por_id = {v.amenaza_id: v for v in informe.valoraciones}

    elementos = [Paragraph(f"Detalle de los {n} riesgos residuales mayores", _ESTILO_SUBTITULO)]

    for r in riesgos_ord:
        amenaza = get_amenaza(r.amenaza_id)
        val = val_por_id[r.amenaza_id]
        etiqueta_fuente = (
            "Ajustado por analista" if val.fuente == "llm_ajustado_humano"
            else "Propuesto por LLM"
        )
        elementos.append(Paragraph(
            f"<b>{amenaza.nombre}</b> "
            f"<font color='#6b7280' size=8>({r.amenaza_id} · residual={r.valor_residual:.2f} · {r.nivel.value})</font>",
            _ESTILO_H3,
        ))
        elementos.append(Paragraph(
            f"<b>Ocurrencia:</b> {val.ocurrencia.value} | "
            f"<b>Impacto econ.:</b> {val.impacto_economico.value} | "
            f"<b>Impacto op.:</b> {val.impacto_operacional.value} "
            f"<font color='#6b7280' size=7>[{etiqueta_fuente}]</font>",
            _ESTILO_TEXTO,
        ))
        elementos.append(Paragraph(
            f"<b>Justificacion:</b> {val.justificacion}",
            _ESTILO_TEXTO,
        ))
        elementos.append(Spacer(1, 0.3 * cm))

    return elementos


def _seccion_metodologia() -> list:
    return [
        PageBreak(),
        Paragraph("Metodologia", _ESTILO_SUBTITULO),
        Paragraph(
            "El analisis sigue el metodo cualitativo escalado de MAGERIT. "
            "Para cada amenaza del catalogo se estima su Ocurrencia "
            "(N/A, Anual, Mensual, Semanal) y dos dimensiones de Impacto "
            "(economico y operacional; N/A, Limitado, Medio, Relevante). "
            "El motor de calculo aplica las siguientes formulas:",
            _ESTILO_TEXTO,
        ),
        Paragraph(
            "<b>Riesgo inherente:</b> peso(Ocurrencia) x promedio(peso(Imp. Economico), peso(Imp. Operacional))",
            _ESTILO_TEXTO,
        ),
        Paragraph(
            "<b>Reduccion combinada:</b> 1 - PRODUCTO(1 - grado_mitigacion_i) para cada salvaguarda implantada aplicable",
            _ESTILO_TEXTO,
        ),
        Paragraph(
            "<b>Riesgo residual:</b> riesgo_inherente x (1 - reduccion_combinada)",
            _ESTILO_TEXTO,
        ),
        Spacer(1, 0.3 * cm),
        Paragraph(
            "El uso de una acumulacion probabilistica para combinar salvaguardas "
            "(en lugar de sumar sus grados) evita valores absurdos: dos salvaguardas "
            "que mitigan el 50% cada una, aplicadas en paralelo, reducen el riesgo "
            "un 75%, no un 100%. Este criterio modela correctamente la probabilidad "
            "de que al menos una salvaguarda actue.",
            _ESTILO_TEXTO,
        ),
        Spacer(1, 0.3 * cm),
        Paragraph(
            "Los umbrales de nivel sobre la escala 0-9 son: bajo [0, 1.5), "
            "medio [1.5, 3.5), alto [3.5, 6.5), critico [6.5, 9]. "
            "Los pesos ordinales (Ocurrencia: 0, 1, 2, 3; Impacto: 0, 1, 2, 3) "
            "y umbrales son parametrizables sin modificar la logica.",
            _ESTILO_TEXTO,
        ),
        Spacer(1, 0.3 * cm),
        Paragraph(
            "Las valoraciones son propuestas por un modelo de lenguaje (LLM) "
            "a partir de la ficha de aplicacion. El analista puede ajustar "
            "cualquier valoracion antes del calculo definitivo (flujo human-in-the-loop). "
            "Cada valoracion conserva la trazabilidad de su origen "
            "('llm' o 'llm_ajustado_humano').",
            _ESTILO_TEXTO,
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
        topMargin=1.5 * cm, bottomMargin=1.5 * cm,
        title=f"AARR - {ficha.nombre}",
        author="Herramienta AARR con IA (TFG)",
    )

    elementos = []
    elementos += _seccion_portada(ficha, informe)
    elementos.append(Spacer(1, 0.6 * cm))
    elementos += _seccion_resumen_ejecutivo(informe)
    elementos += _seccion_ficha(ficha)
    elementos += _seccion_salvaguardas(informe)
    elementos.append(PageBreak())
    elementos += _seccion_tabla_riesgos(informe)
    elementos += _seccion_detalle_top(informe, n=3)
    elementos += _seccion_metodologia()

    doc.build(elementos)
    return buffer.getvalue()