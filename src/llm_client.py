from enum import Enum
import os
from anthropic import Anthropic
from openai import OpenAI


class Tarea(str, Enum):
    extraccion = "extraccion"                  # leer/extraer datos de informes
    clasificacion = "clasificacion"             # priorizar riesgos segun MAGERIT
    generacion_informe = "generacion_informe"   # redactar el informe final


# Configuracion central: que proveedor/modelo se usa para cada tarea.
# Cambiar un modelo para el benchmark es editar solo esto.
CONFIG_MODELOS = {
    Tarea.extraccion: {
        "proveedor": "anthropic",
        "modelo": "claude-sonnet-5",
        "temperatura": 0.0,
    },
    Tarea.clasificacion: {
        "proveedor": "anthropic",
        "modelo": "claude-sonnet-5",
        "temperatura": 0.0,
    },
    Tarea.generacion_informe: {
        "proveedor": "openai",
        "modelo": "gpt-5",  # ajusta al identificador vigente cuando lo pruebes
        "temperatura": 0.3,
    },
}


class LLMClient:
    def __init__(self):
        self._anthropic = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        self._openai = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    def call(self, tarea: Tarea, prompt: str, system: str = "") -> str:
        config = CONFIG_MODELOS[tarea]
        if config["proveedor"] == "anthropic":
            return self._call_anthropic(config, prompt, system)
        elif config["proveedor"] == "openai":
            return self._call_openai(config, prompt, system)
        raise ValueError(f"Proveedor no soportado: {config['proveedor']}")

    def _call_anthropic(self, config, prompt, system):
        params = {
            "model": config["modelo"],
            "max_tokens": 2000,
            "system": system,
            "messages": [{"role": "user", "content": prompt}],
        }
        # Algunos modelos nuevos ya no aceptan temperature; solo lo enviamos si esta definido
        if config.get("temperatura") is not None:
            try:
                response = self._anthropic.messages.create(
                    temperature=config["temperatura"], **params
                )
            except Exception as e:
                if "temperature" in str(e).lower() and "deprecated" in str(e).lower():
                    response = self._anthropic.messages.create(**params)
                else:
                    raise
        else:
            response = self._anthropic.messages.create(**params)
        return response.content[0].text

    def _call_openai(self, config, prompt, system):
        params = {
            "model": config["modelo"],
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        }
        if config.get("temperatura") is not None:
            try:
                response = self._openai.chat.completions.create(
                    temperature=config["temperatura"], **params
                )
            except Exception as e:
                msg = str(e).lower()
                if "temperature" in msg and ("unsupported" in msg or "deprecated" in msg or "not support" in msg):
                    response = self._openai.chat.completions.create(**params)
                else:
                    raise
        else:
            response = self._openai.chat.completions.create(**params)
        return response.choices[0].message.content