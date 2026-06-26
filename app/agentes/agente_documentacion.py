from .base_agent import BaseAgent
from app.servicios.documentacion_service import DocumentacionService
from app.servicios.ollama_service import llamar_ollama

class AgenteDocumentacion(BaseAgent):

    def __init__(self):
        self.doc_service = DocumentacionService()

    def execute(self, pregunta, memoria=""):
        print("\n===== AGENTE DOCUMENTACION =====")
        
        doc = self.doc_service.buscar(pregunta)

        if not doc:
            return "No encontré documentación relacionada."

        # Extraemos el contenido
        contenido_completo = doc["contenido"]
        contexto = contenido_completo[:8000]

        # Llamada a Ollama usando la estructura que espera tu servicio
        return llamar_ollama(
            pregunta=pregunta,
            contexto=f"Documento: {doc['archivo']}\n\nContenido: {contexto}",
            memoria=memoria[-2000:]
        )