"""
Ingesta de fichas de aplicacion desde Excel.

Formato esperado (una plantilla Excel con 5 hojas):

- Ficha: campos simples clave/valor (nombre, descripcion, area, etc.)
- Servicios_IT: filas con (nombre, utiliza, dependencia)
- Grupos_Usuarios: filas con (nombre, tipo, numero_usuarios, permisos)
- Dependencias: filas con (nombre_app, grado)
- Estado_Tecnico: campos simples clave/valor (obsolescencia, DAST/SAST, etc.)

El modulo carga el Excel, valida cada hoja y construye una
FichaAplicacion completa. Si algo esta mal, falla con un mensaje claro.
"""

from pathlib import Path
import pandas as pd
from src.models import (
    FichaAplicacion, ServicioIT, GrupoUsuarios, DependenciaApp,
    EstadoTecnico, ModeloServicio, TipoHost, TipoUsuario,
    NivelPermisos, GradoDependencia,
)


# =============================================================================
# UTILIDADES DE LECTURA
# =============================================================================

def _leer_hoja_clave_valor(ruta: Path, hoja: str) -> dict:
    """Lee una hoja con dos columnas (Campo, Valor) y devuelve un dict."""
    df = pd.read_excel(ruta, sheet_name=hoja, header=None, names=["campo", "valor"])
    df = df.dropna(subset=["campo"])  # descartamos filas vacias
    return {str(row["campo"]).strip(): row["valor"] for _, row in df.iterrows()}


def _leer_hoja_tabla(ruta: Path, hoja: str) -> pd.DataFrame:
    """Lee una hoja como tabla con primera fila = cabecera."""
    df = pd.read_excel(ruta, sheet_name=hoja)
    df.columns = [str(c).strip() for c in df.columns]
    return df.dropna(how="all")  # descarta filas totalmente vacias


def _bool_desde_excel(valor) -> bool:
    """Convierte los strings 'SI'/'NO' o booleanos nativos a bool."""
    if isinstance(valor, bool):
        return valor
    if isinstance(valor, str):
        return valor.strip().upper() in {"SI", "SÍ", "TRUE", "1", "X"}
    if isinstance(valor, (int, float)):
        return bool(valor)
    return False


# =============================================================================
# CARGA DE LA FICHA COMPLETA
# =============================================================================

def cargar_ficha_excel(ruta: Path | str) -> FichaAplicacion:
    """
    Lee un Excel con 5 hojas y devuelve una FichaAplicacion validada.
    Lanza ValueError si el fichero no cumple el formato esperado.
    """
    ruta = Path(ruta)
    if not ruta.exists():
        raise FileNotFoundError(f"No existe el fichero: {ruta}")

    try:
        campos_ficha = _leer_hoja_clave_valor(ruta, "Ficha")
        campos_estado = _leer_hoja_clave_valor(ruta, "Estado_Tecnico")
        df_servicios = _leer_hoja_tabla(ruta, "Servicios_IT")
        df_grupos = _leer_hoja_tabla(ruta, "Grupos_Usuarios")
        df_dependencias = _leer_hoja_tabla(ruta, "Dependencias")
    except Exception as e:
        raise ValueError(
            f"Error leyendo el Excel. Comprueba que tiene las 5 hojas "
            f"esperadas (Ficha, Estado_Tecnico, Servicios_IT, "
            f"Grupos_Usuarios, Dependencias): {e}"
        ) from e

    # Construccion de sub-objetos ---------------------------------------------

    servicios_it = [
        ServicioIT(
            nombre=str(row["nombre"]).strip(),
            utiliza=_bool_desde_excel(row["utiliza"]),
            dependencia=GradoDependencia(str(row.get("dependencia", "N/A")).strip()),
        )
        for _, row in df_servicios.iterrows()
    ]

    grupos = [
        GrupoUsuarios(
            nombre=str(row["nombre"]).strip(),
            tipo=TipoUsuario(str(row["tipo"]).strip()),
            numero_usuarios=int(row["numero_usuarios"]),
            permisos=NivelPermisos(str(row["permisos"]).strip()),
        )
        for _, row in df_grupos.iterrows()
    ]

    dependencias = [
        DependenciaApp(
            nombre_app=str(row["nombre_app"]).strip(),
            grado=GradoDependencia(str(row["grado"]).strip()),
        )
        for _, row in df_dependencias.iterrows()
    ]

    estado = EstadoTecnico(
        amenazas_dast_identificadas=int(campos_estado.get("amenazas_dast_identificadas", 0)),
        amenazas_dast_corregidas=int(campos_estado.get("amenazas_dast_corregidas", 0)),
        amenazas_sast_identificadas=int(campos_estado.get("amenazas_sast_identificadas", 0)),
        amenazas_sast_corregidas=int(campos_estado.get("amenazas_sast_corregidas", 0)),
        porcentaje_obsolescencia=float(campos_estado.get("porcentaje_obsolescencia", 0)),
        uso_cpu=float(campos_estado.get("uso_cpu", 0)),
        uso_memoria_porcentaje=float(campos_estado.get("uso_memoria_porcentaje", 0)),
        uso_almacenamiento_porcentaje=float(campos_estado.get("uso_almacenamiento_porcentaje", 0)),
    )

    # Ficha principal ---------------------------------------------------------

    ficha = FichaAplicacion(
        nombre=str(campos_ficha["nombre"]).strip(),
        descripcion=str(campos_ficha["descripcion"]).strip(),
        area_responsable=str(campos_ficha["area_responsable"]).strip(),
        service_manager=str(campos_ficha["service_manager"]).strip(),
        arquitecto=str(campos_ficha["arquitecto"]).strip(),
        modelo_servicio=ModeloServicio(str(campos_ficha["modelo_servicio"]).strip()),
        proveedor=str(campos_ficha["proveedor"]).strip(),
        host=TipoHost(str(campos_ficha["host"]).strip()),
        servicios_it=servicios_it,
        tiene_usuarios_internos=_bool_desde_excel(campos_ficha["tiene_usuarios_internos"]),
        tiene_usuarios_proveedores=_bool_desde_excel(campos_ficha["tiene_usuarios_proveedores"]),
        tiene_usuarios_clientes=_bool_desde_excel(campos_ficha["tiene_usuarios_clientes"]),
        grupos_usuarios=grupos,
        dependencias=dependencias,
        estado_tecnico=estado,
    )

    return ficha


# =============================================================================
# GENERAR PLANTILLA VACIA (utilidad para el usuario)
# =============================================================================

def generar_plantilla_excel(ruta_salida: Path | str) -> None:
    """
    Crea un fichero Excel vacio con las 5 hojas y los campos esperados.
    Sirve como plantilla que el usuario rellena.
    """
    ruta_salida = Path(ruta_salida)
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(ruta_salida, engine="openpyxl") as writer:
        # Hoja Ficha
        pd.DataFrame({
            "Campo": [
                "nombre", "descripcion", "area_responsable", "service_manager",
                "arquitecto", "modelo_servicio", "proveedor", "host",
                "tiene_usuarios_internos", "tiene_usuarios_proveedores",
                "tiene_usuarios_clientes",
            ],
            "Valor": [""] * 11,
        }).to_excel(writer, sheet_name="Ficha", index=False, header=False)

        # Hoja Servicios_IT
        pd.DataFrame(columns=["nombre", "utiliza", "dependencia"]).to_excel(
            writer, sheet_name="Servicios_IT", index=False,
        )

        # Hoja Grupos_Usuarios
        pd.DataFrame(columns=["nombre", "tipo", "numero_usuarios", "permisos"]).to_excel(
            writer, sheet_name="Grupos_Usuarios", index=False,
        )

        # Hoja Dependencias
        pd.DataFrame(columns=["nombre_app", "grado"]).to_excel(
            writer, sheet_name="Dependencias", index=False,
        )

        # Hoja Estado_Tecnico
        pd.DataFrame({
            "Campo": [
                "amenazas_dast_identificadas", "amenazas_dast_corregidas",
                "amenazas_sast_identificadas", "amenazas_sast_corregidas",
                "porcentaje_obsolescencia", "uso_cpu",
                "uso_memoria_porcentaje", "uso_almacenamiento_porcentaje",
            ],
            "Valor": [0] * 8,
        }).to_excel(writer, sheet_name="Estado_Tecnico", index=False, header=False)