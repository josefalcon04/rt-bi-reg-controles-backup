# app/servicios/ollama_service.py

import os
from click import prompt
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
- Nunca completes información con conocimiento general cuando se trate de documentación.
- Si no encuentras la respuesta en el documento, responde:
  "No encontré esa información en la documentación cargada."
"""


def llamar_ollama(
    pregunta,
    contexto="",
    memoria="",
    conocimiento="",
    system_prompt=PROMPT_BASE
):

    prompt = f"""
{system_prompt}

=== MEMORIA DE CONVERSACIÓN ===
{memoria}

=== CONOCIMIENTO APRENDIDO ===
{conocimiento}

=== CONTEXTO ACTUAL ===
{contexto}

=== PREGUNTA ===
{pregunta}
"""
    print(f"[OLLAMA] Modelo: {MODELO}")
    print(f"[OLLAMA] Longitud prompt: {len(prompt)}")
    print(prompt[:1000])

    r = requests.post(
        OLLAMA_URL,
        json={
            "model": MODELO,
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