"""
Benchmark comparativo entre proveedores/modelos LLM para la tarea de
clasificacion de riesgos segun MAGERIT.
"""

from dotenv import load_dotenv
load_dotenv()

import csv
import re
import time
from datetime import datetime
from pathlib import Path

from src.llm_client import LLMClient, Tarea, CONFIG_MODELOS
from data.benchmark.casos_prueba import CASOS_PRUEBA


SYSTEM = "Eres un analista de riesgos de ciberseguridad experto en MAGERIT."

MODELOS_A_COMPARAR = [
    {"proveedor": "anthropic", "modelo": "claude-sonnet-5", "temperatura": 0.0},
    {"proveedor": "openai", "modelo": "gpt-5", "temperatura": 0.0},
    {"proveedor": "groq", "modelo": "llama-3.3-70b-versatile", "temperatura": 0.0},
]

RE_CODIGO_MAGERIT = re.compile(r"\[[EAINI]\.\d+\]|\[[A-Z]{1,3}\]")
RE_RGPD = re.compile(r"RGPD|GDPR|LOPD", re.IGNORECASE)
RE_ENS = re.compile(r"\bENS\b|Esquema Nacional de Seguridad", re.IGNORECASE)
RE_NIS2 = re.compile(r"NIS ?2", re.IGNORECASE)


def analizar_respuesta(texto: str) -> dict:
    return {
        "longitud_caracteres": len(texto),
        "num_codigos_magerit": len(RE_CODIGO_MAGERIT.findall(texto)),
        "cita_rgpd": bool(RE_RGPD.search(texto)),
        "cita_ens": bool(RE_ENS.search(texto)),
        "cita_nis2": bool(RE_NIS2.search(texto)),
    }


def ejecutar_benchmark():
    client = LLMClient()
    resultados = []
    total = len(CASOS_PRUEBA) * len(MODELOS_A_COMPARAR)
    idx = 0
    config_original = dict(CONFIG_MODELOS[Tarea.clasificacion])

    for caso in CASOS_PRUEBA:
        for cfg in MODELOS_A_COMPARAR:
            idx += 1
            etiqueta = f"{cfg['proveedor']}/{cfg['modelo']}"
            print(f"[{idx}/{total}] Caso {caso['id']} - {etiqueta}...", end=" ", flush=True)

            CONFIG_MODELOS[Tarea.clasificacion] = cfg
            prompt = f"Clasifica este riesgo segun MAGERIT: {caso['descripcion']}"

            t0 = time.time()
            try:
                respuesta = client.call(Tarea.clasificacion, prompt, SYSTEM)
                t = time.time() - t0
                metricas = analizar_respuesta(respuesta)
                error = None
                print(f"OK ({t:.1f}s)")
            except Exception as e:
                t = time.time() - t0
                respuesta = ""
                metricas = analizar_respuesta("")
                error = str(e)[:200]
                print(f"ERROR: {error}")

            resultados.append({
                "caso_id": caso["id"],
                "categoria_activo": caso["categoria_activo"],
                "categoria_amenaza": caso["categoria_amenaza"],
                "complejidad": caso["complejidad"],
                "proveedor": cfg["proveedor"],
                "modelo": cfg["modelo"],
                "tiempo_segundos": round(t, 2),
                **metricas,
                "error": error or "",
                "respuesta_completa": respuesta,
            })

    CONFIG_MODELOS[Tarea.clasificacion] = config_original
    return resultados


def guardar_csv(resultados, ruta_csv):
    campos = [
        "caso_id", "categoria_activo", "categoria_amenaza", "complejidad",
        "proveedor", "modelo", "tiempo_segundos", "longitud_caracteres",
        "num_codigos_magerit", "cita_rgpd", "cita_ens", "cita_nis2", "error",
    ]
    with ruta_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        for r in resultados:
            writer.writerow({k: r[k] for k in campos})


def guardar_respuestas_completas(resultados, ruta_txt):
    with ruta_txt.open("w", encoding="utf-8") as f:
        for r in resultados:
            f.write(f"{'=' * 80}\n")
            f.write(f"Caso {r['caso_id']} - {r['proveedor']}/{r['modelo']}\n")
            f.write(f"{'=' * 80}\n")
            f.write(r["respuesta_completa"])
            f.write("\n\n")


if __name__ == "__main__":
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    carpeta = Path("data/benchmark/resultados")
    carpeta.mkdir(parents=True, exist_ok=True)

    print(f"\nLanzando benchmark: {len(CASOS_PRUEBA)} casos x {len(MODELOS_A_COMPARAR)} modelos\n")
    resultados = ejecutar_benchmark()

    ruta_csv = carpeta / f"benchmark_{timestamp}.csv"
    ruta_txt = carpeta / f"respuestas_{timestamp}.txt"

    guardar_csv(resultados, ruta_csv)
    guardar_respuestas_completas(resultados, ruta_txt)

    print(f"\nMetricas -> {ruta_csv}")
    print(f"Respuestas -> {ruta_txt}")