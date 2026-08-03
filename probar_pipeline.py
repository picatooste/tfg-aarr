from dotenv import load_dotenv
load_dotenv()

from src.models import (
    FichaAplicacion, ServicioIT, GrupoUsuarios, DependenciaApp,
    EstadoTecnico, ModeloServicio, TipoHost, TipoUsuario,
    NivelPermisos, GradoDependencia, SalvaguardaImplantada,
)
from src.pipeline import analizar_aplicacion
from src.catalogos import amenaza as get_amenaza


# --- Ficha de la aplicacion (misma que en probar_modelos.py) ---
ficha = FichaAplicacion(
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
        ServicioIT(nombre="WAS", utiliza=True, dependencia=GradoDependencia.total),
    ],
    tiene_usuarios_internos=True,
    tiene_usuarios_proveedores=False,
    tiene_usuarios_clientes=True,
    grupos_usuarios=[
        GrupoUsuarios(
            nombre="Empleados", tipo=TipoUsuario.interno,
            numero_usuarios=200, permisos=NivelPermisos.sin_admin,
        ),
        GrupoUsuarios(
            nombre="Clientes autorizados", tipo=TipoUsuario.externo,
            numero_usuarios=50, permisos=NivelPermisos.sin_admin,
        ),
    ],
    dependencias=[
        DependenciaApp(nombre_app="AppSecundaria", grado=GradoDependencia.parcial),
    ],
    estado_tecnico=EstadoTecnico(
        amenazas_dast_identificadas=5, amenazas_dast_corregidas=3,
        amenazas_sast_identificadas=8, amenazas_sast_corregidas=6,
        porcentaje_obsolescencia=15.0,
        uso_memoria_porcentaje=60.0,
        uso_almacenamiento_porcentaje=45.0,
    ),
)


# --- Salvaguardas implantadas en esta app ---
salvaguardas_implantadas = [
    SalvaguardaImplantada(salvaguarda_id="SAL-002"),  # Cifrado en reposo
    SalvaguardaImplantada(salvaguarda_id="SAL-003"),  # Plan de contingencia
    SalvaguardaImplantada(salvaguarda_id="SAL-005"),  # Backup y restauracion
]


# --- Ejecutar el pipeline ---
informe = analizar_aplicacion(ficha, salvaguardas_implantadas)


# --- Presentacion del informe ---
print("\n" + "=" * 72)
print(f"INFORME AARR: {informe.aplicacion}")
print(f"Fecha: {informe.fecha_analisis.strftime('%Y-%m-%d %H:%M')} | Modelo IA: {informe.modelo_ia}")
print("=" * 72)

# Ordenar por riesgo residual descendente
riesgos_ordenados = sorted(
    informe.riesgos_residuales,
    key=lambda r: r.valor_residual,
    reverse=True,
)

print(f"\n{'AMENAZA':<40} {'INH':>6} {'RES':>6} {'NIVEL':>10}")
print("-" * 72)
for res in riesgos_ordenados:
    nombre = get_amenaza(res.amenaza_id).nombre[:38]
    print(
        f"{nombre:<40} {res.valor_inherente:>6.2f} "
        f"{res.valor_residual:>6.2f} {res.nivel.value:>10}"
    )

# Top 3 con justificacion completa
print("\n" + "=" * 72)
print("TOP 3 RIESGOS RESIDUALES: DETALLE Y JUSTIFICACION DEL LLM")
print("=" * 72)
val_por_amenaza = {v.amenaza_id: v for v in informe.valoraciones}
for res in riesgos_ordenados[:3]:
    nombre = get_amenaza(res.amenaza_id).nombre
    val = val_por_amenaza[res.amenaza_id]
    print(f"\n[{res.amenaza_id}] {nombre}")
    print(f"  Ocurrencia: {val.ocurrencia.value}")
    print(f"  Impacto economico: {val.impacto_economico.value}")
    print(f"  Impacto operacional: {val.impacto_operacional.value}")
    print(f"  Riesgo inherente: {res.valor_inherente} -> Residual: {res.valor_residual} ({res.nivel.value})")
    print(f"  Salvaguardas aplicadas: {res.salvaguardas_aplicadas or 'ninguna'}")
    print(f"  Justificacion: {val.justificacion}")