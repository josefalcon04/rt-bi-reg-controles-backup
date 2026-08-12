# app/agentes/agente_regulatorio.py

from .base_agent import BaseAgent
from app.servicios.ollama_service import OllamaService
from app.servicios.documentacion_service import DocumentacionService


PROMPT_REGULATORIO = """

Eres un asistente senior especializado en regulación
del sector telecomunicaciones.

Tu conocimiento incluye:

- Normativas OSIPTEL
- Reportes regulatorios
- Procedimientos BI
- Validaciones regulatorias
- Definiciones de indicadores


Reglas:

1. Responde siempre en español.

2. Usa primero el contexto documental entregado.

3. No inventes información.

4. Si la información no está disponible responde:

"No encontré esa información en la documentación cargada."


5. Si preguntan quién creó este asistente responde:

"Fui creado por José Luis Falcon Flores,
Especialista en Datos Regulatorios del equipo BI."

"""


class AgenteRegulatorio(BaseAgent):

    nombre = "AgenteRegulatorio"


    descripcion = """
    Agente especializado en normativa regulatoria,
    documentación OSIPTEL y procesos BI regulatorios.
    """


    def __init__(self):

        self.ollama = OllamaService()

        self.doc_service = DocumentacionService()



    def execute(
        self,
        pregunta,
        memoria=""
    ):

        print(
            "[AGENTE REGULATORIO]",
            pregunta
        )


        try:


            # 1. Validar identidad

            if self.es_pregunta_identidad(pregunta):

                return {

                    "tipo": "identidad",

                    "agente": self.nombre,

                    "respuesta":
                    "Fui creado por José Luis Falcon Flores, "
                    "Especialista en Datos Regulatorios del equipo BI."

                }



            # 2. Buscar documentación

            documento = self.doc_service.buscar(
                pregunta
            )



            if not documento:


                return {

                    "tipo": "sin_documentacion",

                    "agente": self.nombre,

                    "respuesta":
                    "No encontré esa información en la documentación cargada."

                }



            # 3. Preparar contexto

            contexto = documento.get(
                "contenido",
                ""
            )[:5000]



            if not contexto:


                return {

                    "tipo": "sin_contenido",

                    "agente": self.nombre,

                    "respuesta":
                    "El documento encontrado no contiene información útil."

                }



            # 4. Consulta IA con RAG

            respuesta = self.ollama.llamar(

                pregunta=pregunta,

                contexto=contexto,

                memoria=memoria,

                system_prompt=PROMPT_REGULATORIO

            )



            return {

                "tipo": "respuesta_regulatoria",

                "agente": self.nombre,

                "documento":
                    documento.get("archivo"),

                "respuesta": respuesta

            }



        except Exception as e:


            print(
                f"[ERROR AGENTE REGULATORIO] {str(e)}"
            )


            return {

                "tipo": "error",

                "agente": self.nombre,

                "respuesta":
                f"Error procesando consulta regulatoria: {str(e)}"

            }



    def es_pregunta_identidad(
        self,
        pregunta
    ):


        palabras = [

            "quien te creo",

            "quien es tu creador",

            "quien te hizo",

            "autor"

        ]


        pregunta = pregunta.lower()


        return any(

            palabra in pregunta

            for palabra in palabras

        )