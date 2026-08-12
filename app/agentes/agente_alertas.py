# app/agentes/agente_alertas.py

from .base_agent import BaseAgent
from app.servicios.regulatorio_service import RegulatorioService


class AgenteAlertas(BaseAgent):

    nombre = "AgenteAlertas"

    def __init__(self):
        self.service = RegulatorioService()

    def execute(self, pregunta):

        respuesta = self.service.consultar_alertas_norma(
            pregunta
        )

        return {
            "tipo": "alerta",
            "agente": self.nombre,
            "respuesta": respuesta
        }