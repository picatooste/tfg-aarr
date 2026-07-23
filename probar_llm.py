from dotenv import load_dotenv
load_dotenv()

import time
from src.llm_client import LLMClient, Tarea, CONFIG_MODELOS

client = LLMClient()

PROMPT = "Clasifica este riesgo segun MAGERIT: fallo de cifrado en base de datos de clientes."
SYSTEM = "Eres un analista de riesgos de ciberseguridad experto en MAGERIT."

# Guardamos la configuracion original para restaurarla al final
config_original = dict(CONFIG_MODELOS[Tarea.clasificacion])

# Definimos las dos configuraciones que queremos comparar para la misma tarea
configuraciones = [
    {"proveedor": "anthropic", "modelo": "claude-sonnet-5", "temperatura": 0.0},
    {"proveedor": "openai", "modelo": "gpt-5", "temperatura": 0.0},
]

for cfg in configuraciones:
    print("\n" + "=" * 70)
    print(f"MODELO: {cfg['proveedor']} / {cfg['modelo']}")
    print("=" * 70)

    CONFIG_MODELOS[Tarea.clasificacion] = cfg

    t_inicio = time.time()
    try:
        resultado = client.call(tarea=Tarea.clasificacion, prompt=PROMPT, system=SYSTEM)
        t_total = time.time() - t_inicio
        print(f"\n[Tiempo de respuesta: {t_total:.2f} s]")
        print(f"[Longitud de salida: {len(resultado)} caracteres]\n")
        print(resultado)
    except Exception as e:
        print(f"\n[ERROR] {e}")

# Restauramos la configuracion original
CONFIG_MODELOS[Tarea.clasificacion] = config_original