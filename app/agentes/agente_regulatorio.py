from .base_agent import BaseAgent
from app.servicios.ollama_service import llamar_ollama


PROMPT_REGULATORIO = """
Eres un asistente experto en documentación regulatoria.

Reglas:

1. Revisa primero la sección MEMORIA.

2. Si la pregunta hace referencia a:
- ese valor
- eso
- aquello
- lo anterior
- mencionado anteriormente

usa la información de MEMORIA.

3. Solo si la respuesta no existe en MEMORIA,
busca en DOCUMENTACION.

4. Si no encuentras la respuesta en ninguno de los dos lugares responde:

"No encontré esa información en la documentación cargada."
"""


class AgenteRegulatorio(BaseAgent):

    def procesar(
        self,
        pregunta,
        memoria="",
        documento=None
    ):

        if not documento:

            return (
                "No encontré documentación "
                "relacionada."
            )

        contexto = documento["contenido"][:3000]

        prompt = f"""
MEMORIA:

{memoria}

DOCUMENTACION:

{contexto}

PREGUNTA:
{pregunta}
"""

        print("\n=== MEMORIA RECIBIDA ===")
        print(memoria)
        print("========================\n")

        return llamar_ollama(
            pregunta=prompt,
            system_prompt=PROMPT_REGULATORIO
        )