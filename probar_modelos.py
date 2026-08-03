from src.models import (
    FichaAplicacion, ServicioIT, GrupoUsuarios, DependenciaApp,
    EstadoTecnico, ModeloServicio, TipoHost, TipoUsuario,
    NivelPermisos, GradoDependencia, Amenaza, TipoAmenaza,
    Salvaguarda, MitigacionAmenaza,
)

# Ficha de ejemplo minima
ficha = FichaAplicacion(
    nombre="AppEjemplo",
    descripcion="Aplicacion generica para probar el modelo",
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
        GrupoUsuarios(nombre="Empleados", tipo=TipoUsuario.interno,
                      numero_usuarios=200, permisos=NivelPermisos.sin_admin),
    ],
    dependencias=[
        DependenciaApp(nombre_app="AppSecundaria", grado=GradoDependencia.parcial),
    ],
    estado_tecnico=EstadoTecnico(
        amenazas_dast_identificadas=5, amenazas_dast_corregidas=3,
        porcentaje_obsolescencia=15.0, uso_memoria_porcentaje=60.0,
    ),
)

# Amenazas y salvaguardas de ejemplo
amenaza = Amenaza(
    id="AME-001",
    nombre="Manipulacion de programas",
    tipo=TipoAmenaza.ataques_intencionados,
)
salvaguarda = Salvaguarda(
    id="SAL-001",
    nombre="Plan de contingencia global",
)
mitigacion = MitigacionAmenaza(
    salvaguarda_id="SAL-001", amenaza_id="AME-001", grado_mitigacion=0.5,
)

print("Ficha creada:", ficha.nombre)
print("Amenaza:", amenaza.nombre, "-", amenaza.tipo.value)
print("Salvaguarda:", salvaguarda.nombre)
print("Mitigacion:", mitigacion.grado_mitigacion)
print("\nModelos importan y validan correctamente.")