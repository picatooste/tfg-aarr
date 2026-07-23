from dotenv import load_dotenv
load_dotenv()

from src.llm_client import LLMClient, Tarea

client = LLMClient()
resultado = client.call(
    tarea=Tarea.clasificacion,
    prompt="Clasifica este riesgo segun MAGERIT: fallo de cifrado en base de datos de clientes.",
    system="Eres un analista de riesgos de ciberseguridad experto en MAGERIT.",
)
print(resultado)