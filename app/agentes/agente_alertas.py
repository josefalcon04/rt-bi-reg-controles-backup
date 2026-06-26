# ANTES: from app.chatbox.chatbox import consultar_alertas_norma
# AHORA:
from app.servicios.regulatorio_service import consultar_alertas_norma
from .base_agent import BaseAgent

class AgenteAlertas(BaseAgent):
    def execute(self, pregunta):
        return consultar_alertas_norma(pregunta)