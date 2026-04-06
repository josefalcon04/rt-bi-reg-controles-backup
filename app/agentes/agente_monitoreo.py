from .base_agent import BaseAgent

class AgenteMonitoreo(BaseAgent):

    def __init__(self, chatbox_module):
        self.chatbox = chatbox_module

    def procesar(self, pregunta):
        return self.chatbox.consultar_logs_norma(pregunta)