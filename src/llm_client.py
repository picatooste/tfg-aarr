from enum import Enum
import os
import json
import re
from typing import Type
from pydantic import BaseModel, ValidationError
from anthropic import Anthropic
from openai import OpenAI
from google import genai
from groq import Groq


class Tarea(str, Enum):
    extraccion = "extraccion"
    clasificacion = "clasificacion"
    generacion_informe = "generacion_informe"


# Configuracion central: que proveedor/modelo se usa para cada tarea.
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
        "modelo": "gpt-5",
        "temperatura": 0.3,
    },
}


class LLMClient:
    def __init__(self):
        self._anthropic = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        self._openai = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        self._gemini = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
        self._groq = Groq(api_key=os.environ["GROQ_API_KEY"])

    def call(self, tarea: Tarea, prompt: str, system: str = "") -> str:
        config = CONFIG_MODELOS[tarea]
        proveedor = config["proveedor"]
        if proveedor == "anthropic":
            return self._call_anthropic(config, prompt, system)
        elif proveedor == "openai":
            return self._call_openai(config, prompt, system)
        elif proveedor == "google":
            return self._call_gemini(config, prompt, system)
        elif proveedor == "groq":
            return self._call_groq(config, prompt, system)
        raise ValueError(f"Proveedor no soportado: {proveedor}")

    def _call_anthropic(self, config, prompt, system):
        params = {
            "model": config["modelo"],
            "max_tokens": 2000,
            "system": system,
            "messages": [{"role": "user", "content": prompt}],
        }
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
        # Los modelos con razonamiento devuelven ThinkingBlock antes del TextBlock
        for bloque in response.content:
            if hasattr(bloque, 'text'):
                return bloque.text
        return ""

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

    def _call_gemini(self, config, prompt, system):
        contenido = f"{system}\n\n{prompt}" if system else prompt
        response = self._gemini.models.generate_content(
            model=config["modelo"],
            contents=contenido,
        )
        return response.text

    def _call_groq(self, config, prompt, system):
        response = self._groq.chat.completions.create(
            model=config["modelo"],
            temperature=config.get("temperatura", 0.0),
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content

    def call_structured(
        self,
        tarea: Tarea,
        prompt: str,
        schema: Type[BaseModel],
        max_reintentos: int = 2,
    ) -> BaseModel:
        """
        Llama al modelo forzando salida JSON validada contra un schema
        Pydantic. Si el modelo devuelve JSON malformado, reintenta pasando
        el error como contexto al propio modelo (self-repair).
        """
        schema_json = json.dumps(schema.model_json_schema(), indent=2, ensure_ascii=False)
        system_estructurado = (
            "Eres un analista cibersefuridad de riesgos experto en MAGERIT. "
            "Debes devolver UNICAMENTE un JSON valido que cumpla el esquema dado. "
            "No incluyas texto antes ni despues del JSON. No uses bloques de codigo Markdown. "
            "IMPORTANTE: los codigos MAGERIT deben ser reales del catalogo oficial "
            "(ej. E.2, E.19, A.5, A.11, A.18). Si no estas seguro de un codigo, "
            "deja la lista vacia en vez de inventar."
        )
        prompt_estructurado = (
            f"{prompt}\n\n"
            f"Devuelve un JSON que cumpla EXACTAMENTE este esquema Pydantic:\n\n"
            f"{schema_json}"
        )

        ultimo_error = None
        for intento in range(max_reintentos + 1):
            respuesta_texto = self.call(tarea, prompt_estructurado, system_estructurado)
            json_extraido = self._extraer_json(respuesta_texto)
            try:
                datos = json.loads(json_extraido)
                return schema.model_validate(datos)
            except (json.JSONDecodeError, ValidationError) as e:
                ultimo_error = e
                if intento < max_reintentos:
                    prompt_estructurado = (
                        f"{prompt}\n\n"
                        f"El JSON anterior fue invalido. Error: {str(e)[:300]}\n\n"
                        f"Devuelve un JSON valido que cumpla EXACTAMENTE este esquema:\n\n"
                        f"{schema_json}"
                    )

        raise ValueError(
            f"Modelo no genero JSON valido tras {max_reintentos + 1} intentos. "
            f"Ultimo error: {ultimo_error}"
        )

    @staticmethod
    def _extraer_json(texto: str) -> str:
        """
        Extrae el JSON de la respuesta, tolerando bloques de codigo Markdown
        o texto adicional que el modelo pueda incluir.
        """
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", texto, re.DOTALL)
        if match:
            return match.group(1)
        match = re.search(r"\{.*\}", texto, re.DOTALL)
        if match:
            return match.group(0)
        return texto