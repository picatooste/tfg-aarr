from src.models import (
    Activo, TipoActivo, Amenaza, Vulnerabilidad,
)
from src.risk_engine.calculator import calcular_riesgo


# Escenario: fallo de cifrado en BD de clientes (el mismo del benchmark)
activo = Activo(
    id="ACT-001",
    nombre="Base de datos de clientes",
    tipo=TipoActivo.datos,
    propietario="Departamento IT",
    valor_confidencialidad=9,  # datos personales -> muy alto
    valor_integridad=7,
    valor_disponibilidad=5,
)

amenaza = Amenaza(
    id="AME-A11",
    nombre="Acceso no autorizado",
    categoria="ataques_deliberados",
    probabilidad_base=0.6,
)

vulnerabilidad = Vulnerabilidad(
    id="VUL-001",
    activo_id="ACT-001",
    descripcion="Cifrado en reposo mal configurado",
    facilidad_explotacion="alta",
)

riesgo = calcular_riesgo(
    id_riesgo="RIE-001",
    activo=activo,
    amenaza=amenaza,
    vulnerabilidad=vulnerabilidad,
)

print(f"Riesgo calculado:")
print(f"  Probabilidad efectiva: {riesgo.probabilidad}")
print(f"  Impacto:               {riesgo.impacto}")
print(f"  Valor de riesgo:       {riesgo.valor_riesgo}")
print(f"  Nivel:                 {riesgo.nivel.value}")