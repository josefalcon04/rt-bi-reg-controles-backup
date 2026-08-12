# app/agentes/agente_tendencias.py

from .base_agent import BaseAgent
from app.servicios.tendencias_service import buscar_consulta_tendencia
from app.servicios.netezza_service import ejecutar_query
from app.servicios.ollama_service import OllamaService


class AgenteTendencias(BaseAgent):

    nombre = "AgenteTendencias"

    descripcion = """
    Agente especializado en análisis histórico,
    evolución de indicadores y comportamiento
    de métricas BI.
    """

    def __init__(self):

        self.ollama = OllamaService()


    def execute(self, pregunta):

        print(
            "[AGENTE TENDENCIAS]",
            pregunta
        )

        try:

            # Buscar consulta certificada

            consulta = buscar_consulta_tendencia(
                pregunta
            )

            if not consulta:

                return {

                    "tipo": "sin_tendencia",

                    "agente": self.nombre,

                    "respuesta":
                    "No encontré una tendencia relacionada en el catálogo."

                }


            # Ejecutar SQL

            datos = ejecutar_query(
                consulta["QUERY_SQL"]
            )


            if not datos:

                return {

                    "tipo": "sin_datos",

                    "agente": self.nombre,

                    "respuesta":
                    "La consulta no retornó información."

                }


            # Compactar datos

            datos_txt = "\n".join(

                f"{d.get('PERIODO')} | "
                f"{d.get('MODALIDAD')} | "
                f"{d.get('CANTIDAD')}"

                for d in datos[:200]

            )


            analisis = self.ollama.llamar(

                pregunta=pregunta,

                contexto=datos_txt,

                system_prompt="""

                Eres un analista senior BI.

                Analiza la serie histórica entregada.

                Devuelve:

                1. Tendencia general.

                2. Comparación PREPAGO vs POSTPAGO.

                3. Cambios relevantes.

                4. Conclusión ejecutiva.

                Responde en español.

                """

            )


            titulo = (

                consulta["NOMBRE_CONSULTA"]

                .replace("TENDENCIA_", "")

                .replace("_", " ")

                .title()

            )


            return {

                "tipo": "tendencia",

                "agente": self.nombre,

                "titulo": titulo,

                "respuesta": analisis,

                "registros_analizados": len(datos)

            }


        except Exception as e:

            print(
                f"[ERROR AGENTE TENDENCIAS] {str(e)}"
            )

            return {

                "tipo": "error",

                "agente": self.nombre,

                "respuesta":
                f"Error analizando tendencia: {str(e)}"

            }