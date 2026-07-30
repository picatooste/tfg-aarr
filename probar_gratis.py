from dotenv import load_dotenv
load_dotenv()

from src.llm_client import LLMClient, Tarea, CONFIG_MODELOS

client = LLMClient()

PROMPT = "Clasifica este riesgo segun MAGERIT: fallo de cifrado en base de datos de clientes."
SYSTEM = "Eres un analista de riesgos de ciberseguridad experto en MAGERIT."

configs = [
    {"proveedor": "google", "modelo": "gemini-3.6-flash", "temperatura": 0.0},
    {"proveedor": "groq", "modelo": "llama-3.3-70b-versatile", "temperatura": 0.0},
]

for cfg in configs:
    print(f"\n{'=' * 70}")
    print(f"{cfg['proveedor']} / {cfg['modelo']}")
    print('=' * 70)
    CONFIG_MODELOS[Tarea.clasificacion] = cfg
    try:
        r = client.call(Tarea.clasificacion, PROMPT, SYSTEM)
        print(r[:800])  # solo los primeros 800 caracteres para no llenar la consola
        print(f"\n[Total: {len(r)} caracteres]")
    except Exception as e:
        print(f"ERROR: {e}")