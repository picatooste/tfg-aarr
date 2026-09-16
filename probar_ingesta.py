from src.ingest_excel import cargar_ficha_excel

ficha = cargar_ficha_excel("data/plantillas/appejemplo.xlsx")

print(f"Nombre: {ficha.nombre}")
print(f"Modelo: {ficha.modelo_servicio.value} en {ficha.host.value}")
print(f"Servicios IT: {[s.nombre for s in ficha.servicios_it]}")
print(f"Grupos de usuarios: {len(ficha.grupos_usuarios)}")
print(f"  - Total usuarios: {sum(g.numero_usuarios for g in ficha.grupos_usuarios)}")
print(f"Dependencias: {[d.nombre_app for d in ficha.dependencias]}")
print(f"Obsolescencia: {ficha.estado_tecnico.porcentaje_obsolescencia}%")
print(f"\nFicha cargada correctamente desde Excel.")