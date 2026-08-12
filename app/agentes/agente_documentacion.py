# app/agentes/agente_documentacion.py

from .base_agent import BaseAgent
from app.servicios.documentacion_service import DocumentacionService
from app.servicios.ollama_service import OllamaService


class AgenteDocumentacion(BaseAgent):

    nombre = "AgenteDocumentacion"

    descripcion = """
    Agente especializado en búsqueda y consulta
    de documentación interna.

    Utiliza documentos, manuales, procedimientos
    y conocimiento corporativo.
    """


    def __init__(self):

        self.doc_service = DocumentacionService()
        self.ollama = OllamaService()



    def execute(self, pregunta, memoria=""):


        print(
            "[AGENTE DOCUMENTACION]",
            pregunta
        )


        try:


            # 1. Buscar documento relacionado

            documento = self.doc_service.buscar(
                pregunta
            )


            if not documento:


                return {

                    "tipo": "sin_documentacion",

                    "agente": self.nombre,

                    "respuesta":
                        "No encontré documentación relacionada."

                }



            # 2. Extraer contexto

            contenido = documento.get(
                "contenido",
                ""
            )


            if not contenido:


                return {

                    "tipo": "sin_contenido",

                    "agente": self.nombre,

                    "respuesta":
                        "Encontré el documento, pero no contiene información."

                }



            contexto = contenido[:8000]



            # 3. Consulta al modelo usando RAG

            respuesta = self.ollama.llamar(

                pregunta=pregunta,

                contexto=contexto,

                memoria=memoria,

                system_prompt="""

                Eres un asistente experto en documentación BI.

                Reglas:

                - Responde únicamente usando el contexto proporcionado.
                - No inventes información.
                - Si no encuentras la respuesta,
                  indica que no existe evidencia suficiente.
                - Responde siempre en español.

                """

            )



            return {

                "tipo": "respuesta_documentacion",

                "agente": self.nombre,

                "documento":
                    documento.get("archivo"),

                "respuesta": respuesta

            }



        except Exception as e:


            print(
                f"[ERROR AGENTE DOCUMENTACION] {str(e)}"
            )


            return {

                "tipo": "error",

                "agente": self.nombre,

                "respuesta":
                    f"Error consultando documentación: {str(e)}"

            }