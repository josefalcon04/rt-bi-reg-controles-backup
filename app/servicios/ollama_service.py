# app/servicios/ollama_service.py

import os
import requests


OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://localhost:11434/api/generate"
)

MODELO = os.getenv(
    "OLLAMA_MODEL",
    "qwen2.5-coder:7b"
)


PROMPT_BASE = """
Eres BI Assistant Senior.

Fuiste creado por Jose Luis Falcon Flores.

Especialidades:

- Netezza
- Oracle SQL
- Shell Unix
- Python
- Flask
- ETL
- Data Warehouse
- BI
- Reportes regulatorios

Reglas:

- Responde siempre en español.
- Sé claro y profesional.
- Usa únicamente el contexto proporcionado cuando exista.
- Si la respuesta no aparece en el contexto, indícalo explícitamente.
"""


class OllamaService:


    def __init__(self):
        self.url = OLLAMA_URL
        self.modelo = MODELO


    def llamar(
        self,
        pregunta,
        contexto="",
        memoria="",
        conocimiento="",
        system_prompt=PROMPT_BASE
    ):

        prompt = f"""
{system_prompt}

=== MEMORIA ===
{memoria}

=== CONOCIMIENTO ===
{conocimiento}

=== CONTEXTO ===
{contexto}

=== PREGUNTA ===
{pregunta}
"""


        print(f"[OLLAMA] Modelo: {self.modelo}")
        print(f"[OLLAMA] Prompt: {len(prompt)} caracteres")


        r = requests.post(
            self.url,
            json={
                "model": self.modelo,
                "prompt": prompt,
                "stream": False,
                "keep_alive": "15m",
                "options": {
                    "num_predict": 150,
                    "temperature": 0.1,
                    "top_p": 0.9,
                    "num_ctx": 4096
                }
            },
            timeout=300
        )


        r.raise_for_status()

        return r.json().get("response", "")