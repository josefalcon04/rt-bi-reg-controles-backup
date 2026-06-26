from .base_agent import BaseAgent
from app.servicios.ollama_service import llamar_ollama

PROMPT_REGULATORIO = """
Eres un asistente ejecutivo senior, experto en documentación regulatoria y normas del sector.

Reglas:
1. Si la pregunta es sobre tu identidad, quién te creó o quién es tu autor, responde:
   "Fui creado por Jose Falcon, Especialista en Datos Regulatorios del equipo BI."
2. Si la pregunta no es sobre tu identidad, sigue estas reglas:
   - Revisa primero la sección MEMORIA.
   - Si la pregunta hace referencia a "eso", "lo anterior", usa la MEMORIA.
   - Solo si no está en MEMORIA, busca en DOCUMENTACION.
   - Si no encuentras la respuesta, responde exactamente: "No encontré esa información en la documentación cargada."
"""

class AgenteRegulatorio(BaseAgent):

    def execute(self, pregunta, memoria="", documento=None):
        # 1. Filtro de Identidad Institucional
        pregunta_lower = pregunta.lower()
        if any(x in pregunta_lower for x in ["quien te creo", "quien es tu creador", "quien te hizo", "autor"]):
            return "Fui creado por José Luis Falcon Flores, Especialista en Datos Regulatorios del equipo BI."

        # 2. Lógica para RAG (Si llega un documento del router)
        if not documento:
            return "No encontré documentación relacionada para tu consulta."

        contexto = documento.get("contenido", "")[:3000]

        # 3. Llamada al servicio con el prompt especializado
        # Nota: llamamos a llamar_ollama pasando la pregunta formateada en el prompt
        return llamar_ollama(
            pregunta=pregunta,
            contexto=contexto,
            memoria=memoria,
            system_prompt=PROMPT_REGULATORIO
        )