from app.agentes.base_agent import BaseAgent
from app.servicios.documentacion_service import (
    DocumentacionService
)
from app.servicios.ollama_service import llamar_ollama


class AgenteDocumentacion(BaseAgent):

    def __init__(self):

        self.doc_service = (
            DocumentacionService()
        )

    def procesar(
        self,
        pregunta,
        memoria=""
    ):

        print("\n===== AGENTE DOCUMENTACION =====")
        print("Pregunta:", pregunta)

        doc = self.doc_service.buscar(
            pregunta
        )

        print(
            "Documento encontrado:",
            doc is not None
        )

        if not doc:

            return (
                "No encontré documentación "
                "relacionada."
            )

        contenido_completo = (
            doc["contenido"]
        )

        print(
            f"[DOC] Archivo: "
            f"{doc['archivo']}"
        )

        print(
            f"[DOC] Caracteres: "
            f"{len(contenido_completo)}"
        )

        contexto = (
            contenido_completo[:8000]
        )

        print(
            f"[DOC] Contexto enviado: "
            f"{len(contexto)} caracteres"
        )

        memoria = (
            (memoria or "")[-2000:]
        )

        return llamar_ollama(

            pregunta=pregunta,

            contexto=f"""
Documento:
{doc['archivo']}

Contenido:
{contexto}
""",

            memoria=memoria
        )