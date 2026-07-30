from dotenv import load_dotenv
load_dotenv()

from src.llm_client import LLMClient, Tarea, CONFIG_MODELOS
from src.models import HallazgoLLM

client = LLMClient()

prompt = (
    "Analiza el siguiente riesgo: fallo de cifrado en la base de datos de "
    "clientes de una empresa espanola. Los datos incluyen informacion personal "
    "y financiera de aproximadamente 50.000 clientes."
)

# Probamos con los 3 modelos para ver cual respeta mejor el formato
modelos = [
    {"proveedor": "anthropic", "modelo": "claude-sonnet-5", "temperatura": 0.0},
    {"proveedor": "openai", "modelo": "gpt-5", "temperatura": 0.0},
    {"proveedor": "groq", "modelo": "llama-3.3-70b-versatile", "temperatura": 0.0},
]

for cfg in modelos:
    print(f"\n{'=' * 70}")
    print(f"{cfg['proveedor']} / {cfg['modelo']}")
    print('=' * 70)
    CONFIG_MODELOS[Tarea.clasificacion] = cfg
    try:
        hallazgo = client.call_structured(
            tarea=Tarea.clasificacion,
            prompt=prompt,
            schema=HallazgoLLM,
        )
        print(hallazgo.model_dump_json(indent=2))
    except Exception as e:
        print(f"ERROR: {e}")