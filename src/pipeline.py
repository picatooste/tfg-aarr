"""
Pipeline end-to-end del AARR.

Flujo: FichaAplicacion + salvaguardas implantadas -> para cada amenaza
del catalogo, LLM valora (Ocurrencia + Impactos) -> motor calcula
riesgo inherente -> motor aplica salvaguardas -> riesgo residual.
Devuelve un InformeAARR completo con trazabilidad.
"""

from datetime import datetime
from src.catalogos import AMENAZAS, MATRIZ_MITIGACION, amenaza as get_amenaza
from src.llm_client import LLMClient, Tarea, CONFIG_MODELOS
from src.models import (
    FichaAplicacion,
    Amenaza,
    ValoracionAmenaza,
    SalvaguardaImplantada,
    RiesgoInherente,
    RiesgoResidual,
    InformeAARR,
    HallazgoLLM_Valoracion,
)
from src.risk_engine.calculator import (
    calcular_riesgo_inherente,
    calcular_riesgo_residual,
)


SYSTEM_PROMPT_VALORACION = (
    "Eres un analista experto de riesgos de ciberseguridad. Tu tarea es "
    "valorar una amenaza concreta contra una aplicacion, usando UNICAMENTE "
    "las etiquetas del vocabulario controlado que se proporciona en el "
    "esquema. Bases tu valoracion exclusivamente en la informacion de la "
    "ficha (arquitectura, usuarios, estado tecnico) y en la naturaleza de "
    "la amenaza. Si la amenaza no aplica a esta aplicacion, usa 'N/A'. "
    "Justifica siempre en 2-3 frases citando datos concretos de la ficha."
)


def analizar_aplicacion(
    ficha: FichaAplicacion,
    salvaguardas_implantadas: list[SalvaguardaImplantada],
    client: LLMClient | None = None,
    mostrar_progreso: bool = True,
) -> InformeAARR:
    """
    Ejecuta el AARR completo sobre una aplicacion.

    Devuelve un InformeAARR con:
    - valoraciones: lista con la puntuacion del LLM por amenaza
    - riesgos_inherentes: uno por amenaza (calculado por el motor)
    - riesgos_residuales: uno por amenaza (tras aplicar salvaguardas)
    - trazabilidad: modelo usado y fuente ("llm") en cada valoracion
    """
    if client is None:
        client = LLMClient()

    modelo = CONFIG_MODELOS[Tarea.clasificacion]["modelo"]
    ficha_serializada = ficha.model_dump_json(indent=2)

    valoraciones: list[ValoracionAmenaza] = []
    riesgos_inh: list[RiesgoInherente] = []
    riesgos_res: list[RiesgoResidual] = []
    errores: list[tuple[str, str]] = []

    total = len(AMENAZAS)
    for idx, amenaza in enumerate(AMENAZAS, start=1):
        if mostrar_progreso:
            print(
                f"[{idx}/{total}] Valorando {amenaza.id} - {amenaza.nombre}...",
                end=" ", flush=True,
            )

        try:
            valoracion = _valorar_amenaza(client, amenaza, ficha_serializada)
            inherente = calcular_riesgo_inherente(valoracion)
            residual = calcular_riesgo_residual(
                inherente=inherente,
                salvaguardas_implantadas=salvaguardas_implantadas,
                matriz_mitigacion=MATRIZ_MITIGACION,
            )
            valoraciones.append(valoracion)
            riesgos_inh.append(inherente)
            riesgos_res.append(residual)

            if mostrar_progreso:
                print(
                    f"OK (inh={inherente.valor}/{inherente.nivel.value}, "
                    f"res={residual.valor_residual}/{residual.nivel.value})"
                )

        except Exception as e:
            errores.append((amenaza.id, str(e)[:200]))
            if mostrar_progreso:
                print(f"ERROR: {str(e)[:80]}")

    informe = InformeAARR(
        aplicacion=ficha.nombre,
        fecha_analisis=datetime.now(),
        modelo_ia=modelo,
        valoraciones=valoraciones,
        riesgos_inherentes=riesgos_inh,
        salvaguardas_implantadas=salvaguardas_implantadas,
        riesgos_residuales=riesgos_res,
    )

    if mostrar_progreso and errores:
        print(f"\n[WARN] {len(errores)} amenazas no pudieron valorarse:")
        for aid, err in errores:
            print(f"  - {aid}: {err}")

    return informe


def _valorar_amenaza(
    client: LLMClient,
    amenaza: Amenaza,
    ficha_serializada: str,
) -> ValoracionAmenaza:
    """Pide al LLM que valore una amenaza concreta contra la ficha."""
    prompt = (
        f"FICHA DE APLICACION:\n{ficha_serializada}\n\n"
        f"AMENAZA A VALORAR:\n"
        f"- id: {amenaza.id}\n"
        f"- nombre: {amenaza.nombre}\n"
        f"- tipo: {amenaza.tipo.value}\n"
        f"- descripcion: {amenaza.descripcion}\n\n"
        f"Valora esta amenaza usando el vocabulario del esquema."
    )

    llm_val: HallazgoLLM_Valoracion = client.call_structured(
        tarea=Tarea.clasificacion,
        prompt=prompt,
        schema=HallazgoLLM_Valoracion,
    )

    return ValoracionAmenaza(
        amenaza_id=amenaza.id,
        ocurrencia=llm_val.ocurrencia,
        impacto_economico=llm_val.impacto_economico,
        impacto_operacional=llm_val.impacto_operacional,
        justificacion=llm_val.justificacion,
        fuente="llm",
    )