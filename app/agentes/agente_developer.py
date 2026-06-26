from .base_agent import BaseAgent
from app.servicios.ollama_service import llamar_ollama

class AgenteDeveloper(BaseAgent):
    # La firma del método debe coincidir con lo que llama el chatbox
    def execute(self, pregunta):
        system_prompt = """
        Eres el asistente técnico del equipo BI.
        Responde preguntas sobre quién te creó, sobre el equipo o sobre desarrollo técnico.
        Si preguntan por el creador, responde: "Fui creado por Jose Luis Falcon Flores, 
        Especialista en Datos Regulatorios del equipo BI."
        """
        return llamar_ollama(pregunta=pregunta, system_prompt=system_prompt)