from .base_agent import BaseAgent
from app.servicios.ollama_service import llamar_ollama

PROMPT_SQL = """
Eres un experto en:

- Netezza
- Oracle
- SQL
- Shell
- Python

Genera código optimizado.
"""

class AgenteSQL(BaseAgent):

    def procesar(
        self,
        pregunta,
        memoria="",
        documento=None
    ):

        return llamar_ollama(
            pregunta=pregunta,
            system_prompt=PROMPT_SQL
        )