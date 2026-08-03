"""
Carga y acceso a los catalogos de amenazas, salvaguardas y matriz de
mitigacion desde ficheros JSON.

Se cargan una sola vez al importar el modulo. Si los JSON estan mal
formados, falla en tiempo de import (fail-fast), no en tiempo de uso.
"""

import json
from pathlib import Path
from src.models import Amenaza, Salvaguarda, MitigacionAmenaza


RUTA_CATALOGOS = Path(__file__).parent.parent / "data" / "catalogos"


def _cargar_json(nombre_fichero: str) -> list:
    ruta = RUTA_CATALOGOS / nombre_fichero
    if not ruta.exists():
        raise FileNotFoundError(f"No se encuentra el catalogo: {ruta}")
    with ruta.open(encoding="utf-8") as f:
        return json.load(f)


# --- Carga y validacion en tiempo de import (fail-fast) ---

AMENAZAS: list[Amenaza] = [
    Amenaza(**item) for item in _cargar_json("amenazas.json")
]

SALVAGUARDAS: list[Salvaguarda] = [
    Salvaguarda(**item) for item in _cargar_json("salvaguardas.json")
]

MATRIZ_MITIGACION: list[MitigacionAmenaza] = [
    MitigacionAmenaza(**item) for item in _cargar_json("matriz_mitigacion.json")
]


# --- Indexado para consultas O(1) ---

_amenazas_por_id: dict[str, Amenaza] = {a.id: a for a in AMENAZAS}
_salvaguardas_por_id: dict[str, Salvaguarda] = {s.id: s for s in SALVAGUARDAS}


# --- API publica del modulo ---

def amenaza(amenaza_id: str) -> Amenaza:
    """Devuelve la amenaza por id o lanza KeyError si no existe."""
    if amenaza_id not in _amenazas_por_id:
        raise KeyError(f"Amenaza no encontrada: {amenaza_id}")
    return _amenazas_por_id[amenaza_id]


def salvaguarda(salvaguarda_id: str) -> Salvaguarda:
    """Devuelve la salvaguarda por id o lanza KeyError si no existe."""
    if salvaguarda_id not in _salvaguardas_por_id:
        raise KeyError(f"Salvaguarda no encontrada: {salvaguarda_id}")
    return _salvaguardas_por_id[salvaguarda_id]


def salvaguardas_que_mitigan(amenaza_id: str) -> list[MitigacionAmenaza]:
    """Devuelve todas las mitigaciones aplicables a una amenaza."""
    return [m for m in MATRIZ_MITIGACION if m.amenaza_id == amenaza_id]


def resumen_catalogos() -> dict:
    """Devuelve estadisticas de los catalogos cargados."""
    return {
        "amenazas": len(AMENAZAS),
        "salvaguardas": len(SALVAGUARDAS),
        "filas_matriz": len(MATRIZ_MITIGACION),
        "amenazas_con_alguna_salvaguarda": len(
            {m.amenaza_id for m in MATRIZ_MITIGACION}
        ),
        "salvaguardas_activas_en_matriz": len(
            {m.salvaguarda_id for m in MATRIZ_MITIGACION}
        ),
    }