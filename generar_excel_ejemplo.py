"""
Genera un Excel de ejemplo relleno con los datos de AppEjemplo, para
probar el ciclo Excel -> FichaAplicacion.
"""

from pathlib import Path
import pandas as pd


ruta = Path("data/plantillas/appejemplo.xlsx")
ruta.parent.mkdir(parents=True, exist_ok=True)


with pd.ExcelWriter(ruta, engine="openpyxl") as writer:
    # --- Ficha ---
    pd.DataFrame({
        "Campo": [
            "nombre", "descripcion", "area_responsable", "service_manager",
            "arquitecto", "modelo_servicio", "proveedor", "host",
            "tiene_usuarios_internos", "tiene_usuarios_proveedores",
            "tiene_usuarios_clientes",
        ],
        "Valor": [
            "AppEjemplo",
            "Aplicacion web interna de gestion documental",
            "Tecnologia", "Rol X", "Rol Y",
            "PaaS", "Proveedor Generico", "Cloud",
            "SI", "NO", "SI",
        ],
    }).to_excel(writer, sheet_name="Ficha", index=False, header=False)

    # --- Servicios_IT ---
    pd.DataFrame([
        {"nombre": "WAS", "utiliza": "SI", "dependencia": "Total"},
    ]).to_excel(writer, sheet_name="Servicios_IT", index=False)

    # --- Grupos_Usuarios ---
    pd.DataFrame([
        {"nombre": "Empleados", "tipo": "Interno",
         "numero_usuarios": 200, "permisos": "sin admin"},
        {"nombre": "Clientes autorizados", "tipo": "Externo",
         "numero_usuarios": 50, "permisos": "sin admin"},
    ]).to_excel(writer, sheet_name="Grupos_Usuarios", index=False)

    # --- Dependencias ---
    pd.DataFrame([
        {"nombre_app": "AppSecundaria", "grado": "Parcial"},
    ]).to_excel(writer, sheet_name="Dependencias", index=False)

    # --- Estado_Tecnico ---
    pd.DataFrame({
        "Campo": [
            "amenazas_dast_identificadas", "amenazas_dast_corregidas",
            "amenazas_sast_identificadas", "amenazas_sast_corregidas",
            "porcentaje_obsolescencia", "uso_cpu",
            "uso_memoria_porcentaje", "uso_almacenamiento_porcentaje",
        ],
        "Valor": [5, 3, 8, 6, 15.0, 0, 60.0, 45.0],
    }).to_excel(writer, sheet_name="Estado_Tecnico", index=False, header=False)


print(f"Excel de ejemplo creado en: {ruta}")