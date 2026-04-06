from app.agentes.base_agent import BaseAgent
from app.servicios.ollama_service import llamar_ollama

class AgenteDeveloper(BaseAgent):

    def procesar(
        self,
        pregunta,
        memoria=""
    ):

        return llamar_ollama(
            pregunta=pregunta,
            memoria=memoria
        )