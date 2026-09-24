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
    ValoracionAmenaza, Ocurrencia, NivelImpacto,
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

col1, col2, col3 = st.columns([1, 1, 2])
with col1:
    if st.button("Cargar ficha de ejemplo"):
        st.session_state.ficha = crear_ficha_ejemplo()
        st.session_state.informe = None
        st.rerun()

with col2:
    excel_subido = st.file_uploader(
        "O sube un Excel", type=["xlsx"], label_visibility="collapsed",
    )
    if excel_subido is not None:
        # Solo procesamos si es un archivo nuevo (no en cada rerun)
        if st.session_state.get("excel_procesado") != excel_subido.name:
            from src.ingest_excel import cargar_ficha_excel
            from pathlib import Path
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
                tmp.write(excel_subido.getvalue())
                ruta_tmp = Path(tmp.name)
            try:
                st.session_state.ficha = cargar_ficha_excel(ruta_tmp)
                st.session_state.informe = None
                st.session_state.excel_procesado = excel_subido.name
                st.success(f"Excel cargado: {st.session_state.ficha.nombre}")
            except Exception as e:
                st.error(f"Error cargando el Excel: {e}")

with col3:
    if st.session_state.ficha is None:
        st.info(
            "Carga la ficha de ejemplo o sube un Excel con la ficha rellena. "
            "Puedes generar una plantilla vacia ejecutando "
            "`python generar_plantilla.py`."
        )
    else:
        st.success(f"Ficha cargada: **{st.session_state.ficha.nombre}**")

# --- Envio de plantilla al Service Manager ---
with st.expander("Enviar plantilla Excel al Service Manager", expanded=False):
    from src.mailing import (
        construir_email_service_manager, enviar,
    )
    from src.ingest_excel import generar_plantilla_excel
    from pathlib import Path
    import tempfile

    col_a, col_b = st.columns(2)
    with col_a:
        email_sm = st.text_input(
            "Email del Service Manager",
            placeholder="service.manager@empresa.com",
        )
        nombre_sm = st.text_input(
            "Nombre del Service Manager", placeholder="Nombre y apellidos",
        )
    with col_b:
        nombre_app_email = st.text_input(
            "Nombre de la aplicacion a analizar",
            placeholder="ej. AppX",
        )
        remitente_sm = st.text_input(
            "Firma (tu nombre)", placeholder="Analista de Seguridad",
        )

    if st.button("Preparar correo con plantilla"):
        if not (email_sm and nombre_sm and nombre_app_email and remitente_sm):
            st.error("Rellena todos los campos primero.")
        else:
            # Generamos la plantilla Excel en memoria
            with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
                generar_plantilla_excel(tmp.name)
                plantilla_bytes = Path(tmp.name).read_bytes()

            email = construir_email_service_manager(
                destinatario=email_sm,
                nombre_service_manager=nombre_sm,
                nombre_app=nombre_app_email,
                remitente_visible=remitente_sm,
                plantilla_excel_bytes=plantilla_bytes,
            )
            st.session_state.email_pendiente_sm = email
            st.rerun()

    if "email_pendiente_sm" in st.session_state:
        email = st.session_state.email_pendiente_sm
        st.markdown("**Previsualizacion del correo:**")
        st.code(email.resumen(), language=None)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Confirmar y enviar", type="primary", key="send_sm"):
                exito, msg = enviar(email)
                if exito:
                    st.success(msg)
                else:
                    st.warning(msg)
                del st.session_state.email_pendiente_sm
        with col2:
            if st.button("Cancelar", key="cancel_sm"):
                del st.session_state.email_pendiente_sm
                st.rerun()
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
# SECCION 3: RESULTADOS + AJUSTE HUMANO
# =============================================================================

st.header("3. Resultados")

informe = st.session_state.informe

if informe is None:
    st.info("Ejecuta un analisis para ver los resultados.")
else:
    # --- Cabecera con metadatos ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Aplicacion", informe.aplicacion)
    c2.metric("Modelo IA", informe.modelo_ia)
    c3.metric("Amenazas evaluadas", len(informe.riesgos_residuales))
    ajustadas = sum(
        1 for v in informe.valoraciones
        if v.fuente == "llm_ajustado_humano"
    )
    c4.metric("Ajustes del analista", f"{ajustadas} / {len(informe.valoraciones)}")

    # --- EDITOR DE VALORACIONES (human-in-the-loop) ---
    st.subheader("Valoraciones (puedes ajustar y recalcular)")
    st.caption(
        "Edita ocurrencia y/o impactos si no estas de acuerdo con la "
        "propuesta del LLM. Los valores permitidos siguen el vocabulario "
        "controlado (N/A, Anual, Mensual, Semanal para ocurrencia; N/A, "
        "Limitado, Medio, Relevante para impactos)."
    )

    val_por_id = {v.amenaza_id: v for v in informe.valoraciones}

    # Preparamos DataFrame editable
    filas_edicion = []
    for res in informe.riesgos_residuales:
        val = val_por_id[res.amenaza_id]
        filas_edicion.append({
            "id": res.amenaza_id,
            "amenaza": get_amenaza(res.amenaza_id).nombre,
            "ocurrencia": val.ocurrencia.value,
            "impacto_economico": val.impacto_economico.value,
            "impacto_operacional": val.impacto_operacional.value,
            "residual": res.valor_residual,
            "nivel": res.nivel.value,
            "fuente": val.fuente,
        })
    df_edit = pd.DataFrame(filas_edicion)

    # Opciones permitidas para cada columna editable
    opciones_ocurrencia = ["N/A", "Anual", "Mensual", "Semanal"]
    opciones_impacto = ["N/A", "Limitado", "Medio", "Relevante"]

    edited = st.data_editor(
        df_edit,
        column_config={
            "id": st.column_config.TextColumn("ID", disabled=True),
            "amenaza": st.column_config.TextColumn("Amenaza", disabled=True),
            "ocurrencia": st.column_config.SelectboxColumn(
                "Ocurrencia", options=opciones_ocurrencia, required=True,
            ),
            "impacto_economico": st.column_config.SelectboxColumn(
                "Impacto Econ.", options=opciones_impacto, required=True,
            ),
            "impacto_operacional": st.column_config.SelectboxColumn(
                "Impacto Op.", options=opciones_impacto, required=True,
            ),
            "residual": st.column_config.NumberColumn("Residual", disabled=True, format="%.3f"),
            "nivel": st.column_config.TextColumn("Nivel", disabled=True),
            "fuente": st.column_config.TextColumn("Fuente", disabled=True),
        },
        hide_index=True,
        use_container_width=True,
        key="editor_valoraciones",
    )

    if st.button("Recalcular con mis ajustes", type="primary"):
        # Reconstruimos valoraciones detectando cambios respecto al original
        nuevas_valoraciones = []
        for _, row in edited.iterrows():
            original = val_por_id[row["id"]]
            cambiado = (
                row["ocurrencia"] != original.ocurrencia.value
                or row["impacto_economico"] != original.impacto_economico.value
                or row["impacto_operacional"] != original.impacto_operacional.value
            )
            fuente = "llm_ajustado_humano" if cambiado else original.fuente
            nuevas_valoraciones.append(
                ValoracionAmenaza(
                    amenaza_id=row["id"],
                    ocurrencia=Ocurrencia(row["ocurrencia"]),
                    impacto_economico=NivelImpacto(row["impacto_economico"]),
                    impacto_operacional=NivelImpacto(row["impacto_operacional"]),
                    justificacion=original.justificacion,
                    fuente=fuente,
                )
            )

        # Recalculamos con el motor (sin llamar al LLM)
        from src.pipeline import recalcular_desde_valoraciones
        st.session_state.informe = recalcular_desde_valoraciones(
            aplicacion=informe.aplicacion,
            modelo_ia=informe.modelo_ia,
            valoraciones=nuevas_valoraciones,
            salvaguardas_implantadas=informe.salvaguardas_implantadas,
        )
        st.rerun()

    st.divider()

    # --- Ranking final (usa el informe actualizado en session_state) ---
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

    def color_nivel(v):
        colores = {
            "critico": "background-color: #ffcccc; color: black",
            "alto": "background-color: #ffe0b3; color: black",
            "medio": "background-color: #fff2cc; color: black",
            "bajo": "background-color: #d9ead3; color: black",
        }
        return colores.get(v, "")

    styled = df.style.map(color_nivel, subset=["nivel"])
    st.dataframe(styled, use_container_width=True, hide_index=True)

    # --- Grafico ---
    st.subheader("Riesgo inherente vs residual")
    df_plot = df.set_index("amenaza")[["inherente", "residual"]]
    st.bar_chart(df_plot, height=350)

    # --- Top 3 con justificacion editable ---
    st.subheader("Top 3 riesgos residuales: justificacion (editable)")
    st.caption(
        "Puedes ajustar la redaccion de cualquier justificacion antes de "
        "generar el PDF. Los cambios se aplican al informe descargado."
    )
    top3 = df.head(3)
    val_por_id_actual = {v.amenaza_id: v for v in informe.valoraciones}

    for _, row in top3.iterrows():
        aid = row["id"]
        val = val_por_id_actual[aid]

        etiqueta_fuente = (
            "Ajustado por analista" if val.fuente == "llm_ajustado_humano"
            else "Propuesto por LLM"
        )

        with st.expander(
            f"**{row['amenaza']}** — residual={row['residual']} "
            f"({row['nivel']}) — {etiqueta_fuente}",
            expanded=True,
        ):
            c1, c2, c3 = st.columns(3)
            c1.metric("Ocurrencia", val.ocurrencia.value)
            c2.metric("Impacto econ.", val.impacto_economico.value)
            c3.metric("Impacto op.", val.impacto_operacional.value)

            # Text area editable, guardado en session_state
            texto_editado = st.text_area(
                "Justificacion",
                value=val.justificacion,
                key=f"just_{aid}",
                height=180,
            )

            # Si el usuario ha cambiado el texto respecto al original,
            # actualizamos la valoracion y marcamos como ajustada
            if texto_editado != val.justificacion:
                # Encontramos la valoracion en el informe y actualizamos
                for v in informe.valoraciones:
                    if v.amenaza_id == aid:
                        v.justificacion = texto_editado
                        v.fuente = "llm_ajustado_humano"
                        break
                st.caption("✎ Justificacion editada por el analista")

        # --- Boton de descarga del informe PDF ---
    from src.reporting.pdf_report import generar_informe_pdf
    pdf_bytes = generar_informe_pdf(st.session_state.ficha, informe)
    nombre_pdf = (
        f"AARR_{informe.aplicacion}_"
        f"{informe.fecha_analisis.strftime('%Y%m%d_%H%M')}.pdf"
    )
    st.download_button(
        label="Descargar informe (PDF)",
        data=pdf_bytes,
        file_name=nombre_pdf,
        mime="application/pdf",
        type="primary",
    )

        # --- Enviar informe al cliente por email ---
    with st.expander("Enviar informe al cliente por email", expanded=False):
        from src.mailing import construir_email_cliente, enviar

        col_a, col_b = st.columns(2)
        with col_a:
            email_cli = st.text_input(
                "Email del cliente",
                placeholder="cliente@dominio.com", key="email_cli",
            )
            nombre_cli = st.text_input(
                "Nombre del cliente", placeholder="Nombre y apellidos",
                key="nombre_cli",
            )
        with col_b:
            remitente_cli = st.text_input(
                "Firma (tu nombre)", placeholder="Analista de Seguridad",
                key="remitente_cli",
            )

        if st.button("Preparar correo con el informe"):
            if not (email_cli and nombre_cli and remitente_cli):
                st.error("Rellena todos los campos primero.")
            else:
                # Recontamos niveles del informe actual
                conteo = {"critico": 0, "alto": 0, "medio": 0, "bajo": 0}
                for r in informe.riesgos_residuales:
                    conteo[r.nivel.value] += 1

                email = construir_email_cliente(
                    destinatario=email_cli,
                    nombre_cliente=nombre_cli,
                    nombre_app=informe.aplicacion,
                    remitente_visible=remitente_cli,
                    total_amenazas=len(informe.riesgos_residuales),
                    n_criticos=conteo["critico"],
                    n_altos=conteo["alto"],
                    n_salvaguardas=len(informe.salvaguardas_implantadas),
                    informe_pdf_bytes=pdf_bytes,
                )
                st.session_state.email_pendiente_cli = email
                st.rerun()

        if "email_pendiente_cli" in st.session_state:
            email = st.session_state.email_pendiente_cli
            st.markdown("**Previsualizacion del correo:**")
            st.code(email.resumen(), language=None)
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Confirmar y enviar", type="primary", key="send_cli"):
                    exito, msg = enviar(email)
                    if exito:
                        st.success(msg)
                    else:
                        st.warning(msg)
                    del st.session_state.email_pendiente_cli
            with col2:
                if st.button("Cancelar", key="cancel_cli"):
                    del st.session_state.email_pendiente_cli
                    st.rerun()