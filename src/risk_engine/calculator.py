"""
Motor determinista de calculo de riesgo.

Implementa la formula usada por la macro de Excel corporativa:

    riesgo_inherente = ocurrencia * promedio(imp_economico, imp_operacional)
    riesgo_residual  = riesgo_inherente * (1 - reduccion_total)

Donde reduccion_total se calcula por acumulacion probabilistica de todas
las salvaguardas implantadas que mitigan la amenaza.

Los pesos de las etiquetas ordinales son configurables (PESOS_ORDINALES)
para poder alinear el sistema con distintas parametrizaciones de la
macro sin tocar la logica.
"""

from src.models import (
    Ocurrencia,
    NivelImpacto,
    NivelRiesgo,
    ValoracionAmenaza,
    SalvaguardaImplantada,
    MitigacionAmenaza,
    RiesgoInherente,
    RiesgoResidual,
)


# =============================================================================
# PARAMETROS DE CALCULO (configurables)
# =============================================================================

# Pesos lineales para etiquetas ordinales.
# Si la macro real usa otros pesos, solo hay que cambiar aqui.
PESOS_ORDINALES = {
    Ocurrencia.no_aplica: 0,
    Ocurrencia.anual: 1,
    Ocurrencia.mensual: 2,
    Ocurrencia.semanal: 3,
    NivelImpacto.no_aplica: 0,
    NivelImpacto.limitado: 1,
    NivelImpacto.medio: 2,
    NivelImpacto.relevante: 3,
}

# Umbrales de nivel de riesgo sobre la escala 0-9.
# Cambiar si la empresa usa otra clasificacion.
UMBRALES_NIVEL = [
    (1.5, NivelRiesgo.bajo),
    (3.5, NivelRiesgo.medio),
    (6.5, NivelRiesgo.alto),
    (9.01, NivelRiesgo.critico),
]


# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

def _determinar_nivel(valor: float) -> NivelRiesgo:
    """Mapea un valor numerico al nivel cualitativo segun los umbrales."""
    for umbral, nivel in UMBRALES_NIVEL:
        if valor < umbral:
            return nivel
    return NivelRiesgo.critico


# =============================================================================
# CALCULO DE RIESGO INHERENTE
# =============================================================================

def calcular_riesgo_inherente(valoracion: ValoracionAmenaza) -> RiesgoInherente:
    """
    Calcula el riesgo inherente (sin salvaguardas) para una amenaza
    valorada sobre una aplicacion.
    """
    peso_ocu = PESOS_ORDINALES[valoracion.ocurrencia]
    peso_imp_econ = PESOS_ORDINALES[valoracion.impacto_economico]
    peso_imp_oper = PESOS_ORDINALES[valoracion.impacto_operacional]
    peso_imp_prom = (peso_imp_econ + peso_imp_oper) / 2

    valor = peso_ocu * peso_imp_prom
    nivel = _determinar_nivel(valor)

    return RiesgoInherente(
        amenaza_id=valoracion.amenaza_id,
        peso_ocurrencia=peso_ocu,
        peso_impacto_promedio=peso_imp_prom,
        valor=round(valor, 3),
        nivel=nivel,
    )


# =============================================================================
# CALCULO DE RIESGO RESIDUAL
# =============================================================================

def calcular_riesgo_residual(
    inherente: RiesgoInherente,
    salvaguardas_implantadas: list[SalvaguardaImplantada],
    matriz_mitigacion: list[MitigacionAmenaza],
) -> RiesgoResidual:
    """
    Aplica el efecto conjunto de las salvaguardas implantadas que
    mitigan la amenaza. Usa acumulacion probabilistica para evitar
    valores absurdos:

        reduccion_total = 1 - Producto(1 - grado_mitigacion_i)

    Ejemplo: dos salvaguardas de 50% cada una dan 75% combinado, no 100%.
    """
    ids_implantadas = {
        s.salvaguarda_id for s in salvaguardas_implantadas if s.implantada
    }

    # Filtramos las mitigaciones relevantes: que apunten a esta amenaza
    # y provengan de salvaguardas que si estan implantadas.
    mitigaciones_activas = [
        m for m in matriz_mitigacion
        if m.amenaza_id == inherente.amenaza_id
        and m.salvaguarda_id in ids_implantadas
    ]

    # Acumulacion probabilistica de la reduccion
    factor_no_mitigado = 1.0
    for m in mitigaciones_activas:
        factor_no_mitigado *= (1 - m.grado_mitigacion)
    reduccion_total = 1 - factor_no_mitigado

    valor_residual = inherente.valor * (1 - reduccion_total)
    nivel_residual = _determinar_nivel(valor_residual)

    return RiesgoResidual(
        amenaza_id=inherente.amenaza_id,
        valor_inherente=inherente.valor,
        reduccion_total=round(reduccion_total, 3),
        valor_residual=round(valor_residual, 3),
        nivel=nivel_residual,
        salvaguardas_aplicadas=[m.salvaguarda_id for m in mitigaciones_activas],
    )