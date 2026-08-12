# app/agentes/agente_developer.py

from .base_agent import BaseAgent
from app.servicios.ollama_service import OllamaService


class AgenteDeveloper(BaseAgent):

    nombre = "AgenteDeveloper"

    descripcion = """
    Agente especializado en desarrollo de software,
    automatización y arquitectura técnica BI.
    """

    def __init__(self):

        self.ollama = OllamaService()


    def execute(self, pregunta):

        print(
            "[AGENTE DEVELOPER]",
            pregunta
        )


        system_prompt = """
        Eres un arquitecto de software y desarrollador senior
        especializado en equipos BI.

        Tu dominio incluye:

        Desarrollo:
        - Python
        - Flask
        - APIs REST
        - Arquitectura de aplicaciones
        - Patrones de diseño

        Datos:
        - SQL
        - Netezza
        - Teradata
        - Oracle
        - Procesos ETL

        Automatización:
        - Shell scripting
        - Linux
        - Control-M
        - Jobs batch

        BI:
        - Dashboards
        - Power BI
        - Integraciones de datos


        Reglas:

        - Responde siempre en español.
        - Sé técnico pero claro.
        - Cuando entregues código:
          * usa buenas prácticas.
          * explica los cambios importantes.
          * evita código innecesario.

        Si el usuario pregunta quién creó este asistente,
        responde:

        "Fui creado por Jose Luis Falcon Flores,
        Especialista en Datos Regulatorios del equipo BI."

        """


        try:

            respuesta = self.ollama.llamar(
                pregunta=pregunta,
                system_prompt=system_prompt
            )


            return {

                "tipo": "respuesta_developer",

                "agente": self.nombre,

                "respuesta": respuesta

            }


        except Exception as e:


            print(
                f"[ERROR AGENTE DEVELOPER] {str(e)}"
            )


            return {

                "tipo": "error",

                "agente": self.nombre,

                "respuesta":
                    f"Error procesando consulta técnica: {str(e)}"

            }