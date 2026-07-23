"""
Motor de calculo de riesgo segun MAGERIT (metodo cualitativo escalado).

La logica es deterministica: dados una probabilidad y un impacto, el
valor y el nivel de riesgo son reproducibles. Esto separa la parte
interpretativa (que puede hacer un LLM) de la parte cuantitativa (que
debe ser trazable y auditable).
"""

from src.models import (
    Activo,
    Amenaza,
    Vulnerabilidad,
    Riesgo,
    NivelRiesgo,
)


# Umbrales de nivel de riesgo (MAGERIT cualitativo escalado)
UMBRALES_NIVEL = [
    (2.0, NivelRiesgo.bajo),
    (4.0, NivelRiesgo.medio),
    (7.0, NivelRiesgo.alto),
    (10.01, NivelRiesgo.critico),
]

# Ajuste de probabilidad segun facilidad de explotacion de la vulnerabilidad
FACTOR_EXPLOTACION = {
    "baja": 0.3,
    "media": 0.6,
    "alta": 1.0,
}


def calcular_impacto(activo: Activo) -> float:
    """
    El impacto se deriva del valor del activo en las dimensiones CIAT.
    Usamos el maximo porque en MAGERIT, el peor efecto sobre cualquier
    dimension determina el impacto global (criterio conservador).
    """
    return float(max(
        activo.valor_confidencialidad,
        activo.valor_integridad,
        activo.valor_disponibilidad,
    ))


def calcular_probabilidad(
    amenaza: Amenaza,
    vulnerabilidad: Vulnerabilidad,
) -> float:
    """
    La probabilidad efectiva combina la probabilidad base de la amenaza
    con la facilidad de explotacion de la vulnerabilidad asociada. Un
    activo con vulnerabilidad de facil explotacion aumenta la
    probabilidad; uno con vulnerabilidad dificil de explotar la reduce.
    """
    factor = FACTOR_EXPLOTACION.get(
        vulnerabilidad.facilidad_explotacion.lower(),
        0.6,  # valor por defecto si viene un texto no esperado
    )
    prob = amenaza.probabilidad_base * factor
    return max(0.0, min(1.0, prob))  # aseguramos rango [0, 1]


def determinar_nivel(valor_riesgo: float) -> NivelRiesgo:
    """Mapea el valor numerico al nivel cualitativo."""
    for umbral, nivel in UMBRALES_NIVEL:
        if valor_riesgo < umbral:
            return nivel
    return NivelRiesgo.critico


def calcular_riesgo(
    id_riesgo: str,
    activo: Activo,
    amenaza: Amenaza,
    vulnerabilidad: Vulnerabilidad,
) -> Riesgo:
    """
    Construye un objeto Riesgo completo aplicando el metodo MAGERIT
    cualitativo escalado. Toda la logica es deterministica y trazable.
    """
    probabilidad = calcular_probabilidad(amenaza, vulnerabilidad)
    impacto = calcular_impacto(activo)
    valor_riesgo = probabilidad * impacto
    nivel = determinar_nivel(valor_riesgo)

    return Riesgo(
        id=id_riesgo,
        activo_id=activo.id,
        amenaza_id=amenaza.id,
        vulnerabilidad_id=vulnerabilidad.id,
        probabilidad=round(probabilidad, 3),
        impacto=impacto,
        valor_riesgo=round(valor_riesgo, 3),
        nivel=nivel,
    )