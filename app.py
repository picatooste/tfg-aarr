"""
Interfaz Streamlit para la herramienta AARR.

Tres secciones en una sola pagina:
1. Ficha de la aplicacion (formulario + carga de ejemplo)
2. Analisis: seleccion de salvaguardas + ejecucion del pipeline
3. Resultados: tabla + top 3 con justificacion + grafico

Streamlit recarga el script en cada interaccion; usamos session_state
para no perder la ficha entre re-ejecuciones.
"""

from dotenv import load_dotenv
load_dotenv()

import time
import pandas as pd
import streamlit as st

from src.models import (
    FichaAplicacion, ServicioIT, GrupoUsuarios, DependenciaApp,
    EstadoTecnico, ModeloServicio, TipoHost, TipoUsuario,
    NivelPermisos, GradoDependencia, SalvaguardaImplantada,
)
from src.catalogos import AMENAZAS, SALVAGUARDAS, amenaza as get_amenaza
from src.pipeline import analizar_aplicacion


# =============================================================================
# CONFIGURACION DE LA PAGINA
# =============================================================================

st.set_page_config(
    page_title="AARR con IA",
    page_icon="🛡️",
    layout="wide",
)

st.title("Herramienta de Automatizacion del Analisis de Riesgos")
st.caption("TFG — AARR con IA aplicado al proceso empresarial")


# =============================================================================
# ESTADO PERSISTENTE (para no perder datos al re-ejecutar)
# =============================================================================

if "ficha" not in st.session_state:
    st.session_state.ficha = None
if "informe" not in st.session_state:
    st.session_state.informe = None


# =============================================================================
# UTILIDAD: FICHA DE EJEMPLO
# =============================================================================

def crear_ficha_ejemplo() -> FichaAplicacion:
    """La misma ficha que usamos en probar_pipeline.py, para demos rapidas."""
    return FichaAplicacion(
        nombre="AppEjemplo",
        descripcion=(
            "Aplicacion web interna de gestion documental usada por "
            "empleados y algunos clientes externos autorizados."
        ),
        area_responsable="Tecnologia",
        service_manager="Rol X",
        arquitecto="Rol Y",
        modelo_servicio=ModeloServicio.paas,
        proveedor="Proveedor Generico",
        host=TipoHost.cloud,
        servicios_it=[
            ServicioIT(nombre="WAS", utiliza=True,
                       dependencia=GradoDependencia.total),
        ],
        tiene_usuarios_internos=True,
        tiene_usuarios_proveedores=False,
        tiene_usuarios_clientes=True,
        grupos_usuarios=[
            GrupoUsuarios(nombre="Empleados", tipo=TipoUsuario.interno,
                          numero_usuarios=200,
                          permisos=NivelPermisos.sin_admin),
            GrupoUsuarios(nombre="Clientes autorizados",
                          tipo=TipoUsuario.externo,
                          numero_usuarios=50,
                          permisos=NivelPermisos.sin_admin),
        ],
        dependencias=[
            DependenciaApp(nombre_app="AppSecundaria",
                           grado=GradoDependencia.parcial),
        ],
        estado_tecnico=EstadoTecnico(
            amenazas_dast_identificadas=5, amenazas_dast_corregidas=3,
            amenazas_sast_identificadas=8, amenazas_sast_corregidas=6,
            porcentaje_obsolescencia=15.0,
            uso_memoria_porcentaje=60.0,
            uso_almacenamiento_porcentaje=45.0,
        ),
    )


# =============================================================================
# SECCION 1: FICHA
# =============================================================================

st.header("1. Ficha de la aplicacion")

col1, col2 = st.columns([1, 3])
with col1:
    if st.button("Cargar ficha de ejemplo", type="primary"):
        st.session_state.ficha = crear_ficha_ejemplo()
        st.session_state.informe = None  # invalidamos analisis previo
        st.rerun()

with col2:
    if st.session_state.ficha is None:
        st.info(
            "Carga una ficha de ejemplo o (en versiones futuras) sube "
            "un Excel con la ficha rellena."
        )
    else:
        f = st.session_state.ficha
        st.success(f"Ficha cargada: **{f.nombre}**")

if st.session_state.ficha is not None:
    with st.expander("Ver ficha completa", expanded=False):
        f = st.session_state.ficha
        st.markdown(f"**{f.nombre}** — _{f.descripcion}_")
        c1, c2, c3 = st.columns(3)
        c1.metric("Modelo", f.modelo_servicio.value)
        c2.metric("Host", f.host.value)
        c3.metric("Area", f.area_responsable)

        st.markdown("**Usuarios:**")
        st.write({
            "internos": f.tiene_usuarios_internos,
            "proveedores": f.tiene_usuarios_proveedores,
            "clientes": f.tiene_usuarios_clientes,
        })

        st.markdown("**Estado tecnico:**")
        et = f.estado_tecnico
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Obsolescencia", f"{et.porcentaje_obsolescencia}%")
        c2.metric("DAST id/corr",
                  f"{et.amenazas_dast_identificadas}/{et.amenazas_dast_corregidas}")
        c3.metric("SAST id/corr",
                  f"{et.amenazas_sast_identificadas}/{et.amenazas_sast_corregidas}")
        c4.metric("Uso memoria", f"{et.uso_memoria_porcentaje}%")


# =============================================================================
# SECCION 2: ANALISIS
# =============================================================================

st.header("2. Analisis de riesgos")

if st.session_state.ficha is None:
    st.warning("Carga una ficha primero para poder ejecutar el analisis.")
else:
    st.markdown("**Salvaguardas implantadas en esta app** "
                "(marca las que apliquen)")

    # Checkboxes de salvaguardas
    ids_seleccionadas = []
    cols = st.columns(2)
    for idx, sal in enumerate(SALVAGUARDAS):
        col = cols[idx % 2]
        label = f"**{sal.id}** — {sal.nombre}"
        # Por defecto marcamos SAL-002, SAL-003, SAL-005 (como en el script de prueba)
        default = sal.id in {"SAL-002", "SAL-003", "SAL-005"}
        if col.checkbox(label, value=default, key=f"sal_{sal.id}",
                        help=sal.descripcion):
            ids_seleccionadas.append(sal.id)

    st.divider()

    coste_estimado = len(AMENAZAS) * 0.008  # ~$0.008 por amenaza con Claude
    st.caption(
        f"Se ejecutaran **{len(AMENAZAS)}** llamadas al LLM "
        f"(~{len(AMENAZAS) * 20}s, ~${coste_estimado:.2f})."
    )

    if st.button("Ejecutar analisis", type="primary"):
        salvaguardas_implantadas = [
            SalvaguardaImplantada(salvaguarda_id=sid)
            for sid in ids_seleccionadas
        ]

        progreso = st.progress(0.0)
        estado = st.empty()

        # Contenedor para ir mostrando los resultados en vivo
        # (Streamlit no expone facilmente el callback del pipeline;
        # como alternativa simple, ejecutamos y luego pintamos.)
        estado.info("Ejecutando analisis... esto puede tardar 2-3 minutos.")
        t0 = time.time()

        try:
            informe = analizar_aplicacion(
                st.session_state.ficha,
                salvaguardas_implantadas,
                mostrar_progreso=False,  # el print no se ve en Streamlit
            )
            progreso.progress(1.0)
            t = time.time() - t0
            estado.success(
                f"Analisis completado en {t:.1f}s "
                f"({len(informe.valoraciones)}/{len(AMENAZAS)} amenazas)."
            )
            st.session_state.informe = informe
        except Exception as e:
            estado.error(f"Error en el analisis: {e}")


# =============================================================================
# SECCION 3: RESULTADOS
# =============================================================================

st.header("3. Resultados")

informe = st.session_state.informe

if informe is None:
    st.info("Ejecuta un analisis para ver los resultados.")
else:
    # Cabecera con metadatos
    c1, c2, c3 = st.columns(3)
    c1.metric("Aplicacion", informe.aplicacion)
    c2.metric("Modelo IA", informe.modelo_ia)
    c3.metric("Amenazas evaluadas", len(informe.riesgos_residuales))

    # --- Tabla de resultados ---
    st.subheader("Ranking por riesgo residual")

    filas = []
    for res in informe.riesgos_residuales:
        filas.append({
            "id": res.amenaza_id,
            "amenaza": get_amenaza(res.amenaza_id).nombre,
            "inherente": res.valor_inherente,
            "residual": res.valor_residual,
            "reduccion (%)": round(res.reduccion_total * 100, 1),
            "nivel": res.nivel.value,
        })

    df = pd.DataFrame(filas).sort_values("residual", ascending=False)

    # Colorear por nivel
    def color_nivel(v):
        colores = {
            "critico": "background-color: #ffcccc",
            "alto": "background-color: #ffe0b3",
            "medio": "background-color: #fff2cc",
            "bajo": "background-color: #d9ead3",
        }
        return colores.get(v, "")

    styled = df.style.map(color_nivel, subset=["nivel"])
    st.dataframe(styled, use_container_width=True, hide_index=True)

    # --- Grafico simple ---
    st.subheader("Grafico: riesgo inherente vs residual")
    df_plot = df.set_index("amenaza")[["inherente", "residual"]]
    st.bar_chart(df_plot, height=350)

    # --- Top 3 con justificacion ---
    st.subheader("Top 3 riesgos residuales: justificacion del LLM")
    top3 = df.head(3)
    val_por_id = {v.amenaza_id: v for v in informe.valoraciones}

    for _, row in top3.iterrows():
        aid = row["id"]
        val = val_por_id[aid]
        with st.expander(
            f"**{row['amenaza']}** — residual={row['residual']} "
            f"({row['nivel']})",
            expanded=True,
        ):
            c1, c2, c3 = st.columns(3)
            c1.metric("Ocurrencia", val.ocurrencia.value)
            c2.metric("Impacto econ.", val.impacto_economico.value)
            c3.metric("Impacto op.", val.impacto_operacional.value)
            st.markdown("**Justificacion:**")
            st.write(val.justificacion)