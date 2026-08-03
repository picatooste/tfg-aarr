from src.catalogos import (
    AMENAZAS, SALVAGUARDAS, MATRIZ_MITIGACION,
    amenaza, salvaguarda, salvaguardas_que_mitigan, resumen_catalogos,
)


print("=" * 70)
print("RESUMEN DE CATALOGOS CARGADOS")
print("=" * 70)
for k, v in resumen_catalogos().items():
    print(f"  {k}: {v}")

print("\n" + "=" * 70)
print("AMENAZAS POR TIPO")
print("=" * 70)
from collections import defaultdict
por_tipo = defaultdict(list)
for a in AMENAZAS:
    por_tipo[a.tipo.value].append(a.nombre)
for tipo, nombres in por_tipo.items():
    print(f"\n  {tipo}:")
    for n in nombres:
        print(f"    - {n}")

print("\n" + "=" * 70)
print("PARA UNA AMENAZA CONCRETA: que salvaguardas la mitigan?")
print("=" * 70)
amenaza_id = "AME-002"  # Denegacion de servicios
print(f"\n  Amenaza: {amenaza(amenaza_id).nombre}")
mitigaciones = salvaguardas_que_mitigan(amenaza_id)
for m in mitigaciones:
    nombre = salvaguarda(m.salvaguarda_id).nombre
    print(f"    - {nombre} (mitiga al {m.grado_mitigacion * 100:.0f}%)")

print("\n" + "=" * 70)
print("AMENAZAS SIN NINGUNA SALVAGUARDA EN LA MATRIZ (huecos de cobertura)")
print("=" * 70)
ids_con_mitigacion = {m.amenaza_id for m in MATRIZ_MITIGACION}
huecos = [a for a in AMENAZAS if a.id not in ids_con_mitigacion]
if huecos:
    for a in huecos:
        print(f"  - {a.id}: {a.nombre}")
else:
    print("  Todas las amenazas tienen al menos una salvaguarda aplicable.")