from src.models import (
    ValoracionAmenaza, Ocurrencia, NivelImpacto,
    SalvaguardaImplantada, MitigacionAmenaza,
)
from src.risk_engine.calculator import (
    calcular_riesgo_inherente, calcular_riesgo_residual,
)


def imprimir_escenario(titulo, inherente, residual=None):
    print(f"\n{'=' * 60}")
    print(f"ESCENARIO: {titulo}")
    print('=' * 60)
    print(f"  Ocurrencia: peso {inherente.peso_ocurrencia}")
    print(f"  Impacto promedio: peso {inherente.peso_impacto_promedio}")
    print(f"  -> Riesgo INHERENTE: {inherente.valor} ({inherente.nivel.value})")
    if residual:
        print(f"  Salvaguardas aplicadas: {len(residual.salvaguardas_aplicadas)}")
        print(f"  Reduccion total: {residual.reduccion_total * 100:.1f}%")
        print(f"  -> Riesgo RESIDUAL: {residual.valor_residual} ({residual.nivel.value})")


# --- ESCENARIO 1: sin salvaguardas ---
val_1 = ValoracionAmenaza(
    amenaza_id="AME-001",
    ocurrencia=Ocurrencia.mensual,
    impacto_economico=NivelImpacto.relevante,
    impacto_operacional=NivelImpacto.medio,
    justificacion="Caso critico sin salvaguardas",
)
inh_1 = calcular_riesgo_inherente(val_1)
imprimir_escenario("Amenaza mensual, impacto econ. relevante + op. medio, SIN salvaguardas", inh_1)


# --- ESCENARIO 2: una salvaguarda parcial ---
sal_1 = [SalvaguardaImplantada(salvaguarda_id="SAL-001")]
mat_1 = [MitigacionAmenaza(salvaguarda_id="SAL-001", amenaza_id="AME-001", grado_mitigacion=0.6)]
res_2 = calcular_riesgo_residual(inh_1, sal_1, mat_1)
imprimir_escenario("Mismo caso + 1 salvaguarda al 60%", inh_1, res_2)


# --- ESCENARIO 3: dos salvaguardas (acumulacion probabilistica) ---
sal_2 = [
    SalvaguardaImplantada(salvaguarda_id="SAL-001"),
    SalvaguardaImplantada(salvaguarda_id="SAL-002"),
]
mat_2 = [
    MitigacionAmenaza(salvaguarda_id="SAL-001", amenaza_id="AME-001", grado_mitigacion=0.5),
    MitigacionAmenaza(salvaguarda_id="SAL-002", amenaza_id="AME-001", grado_mitigacion=0.5),
]
res_3 = calcular_riesgo_residual(inh_1, sal_2, mat_2)
imprimir_escenario("Mismo caso + 2 salvaguardas al 50% cada una", inh_1, res_3)


# --- ESCENARIO 4: valoracion N/A ---
val_2 = ValoracionAmenaza(
    amenaza_id="AME-002",
    ocurrencia=Ocurrencia.no_aplica,
    impacto_economico=NivelImpacto.medio,
    impacto_operacional=NivelImpacto.limitado,
    justificacion="Amenaza no aplicable a esta app",
)
inh_2 = calcular_riesgo_inherente(val_2)
imprimir_escenario("Amenaza N/A (no aplica)", inh_2)