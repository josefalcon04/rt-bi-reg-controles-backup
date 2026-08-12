# app/agentes/agente_sql.py

from .base_agent import BaseAgent
from app.servicios.ollama_service import OllamaService
from app.servicios.netezza_service import ejecutar_query
import re


class AgenteSQL(BaseAgent):

    nombre = "AgenteSQL"

    descripcion = """
    Agente especializado en generación,
    análisis y ejecución controlada de SQL.

    Maneja Netezza, Teradata y Oracle.
    """



    def __init__(self):

        self.ollama = OllamaService()



    def execute(self, pregunta):

        print(
            "[AGENTE SQL]",
            pregunta
        )


        system_prompt = """

        Eres un experto en SQL empresarial.

        Dominas:

        - Netezza
        - Teradata
        - Oracle


        Reglas:

        1. Si solicitan información de base de datos,
           genera SQL válido.


        2. Si solicitan optimización:

           - analiza el SQL existente.
           - devuelve una versión optimizada.


        3. Si solicitan explicación:

           explica la lógica.


        4. Cuando generes SQL:

           - devuelve únicamente SQL.
           - no uses markdown.
           - no agregues comentarios.


        Prioriza:

        - SELECT
        - WITH CTE
        - buenas prácticas SQL
        - rendimiento sobre grandes volúmenes.

        """



        try:


            respuesta_llm = self.ollama.llamar(

                pregunta=pregunta,

                system_prompt=system_prompt

            )


            sql = (
                respuesta_llm
                .replace("```sql", "")
                .replace("```", "")
                .strip()
            )



            if self.es_sql(sql):


                if not self.sql_permitido(sql):

                    return {

                        "tipo": "error_seguridad",

                        "agente": self.nombre,

                        "respuesta":
                        "El SQL contiene operaciones no permitidas."

                    }



                datos = ejecutar_query(
                    sql
                )


                return {

                    "tipo": "resultado_sql",

                    "agente": self.nombre,

                    "sql": sql,

                    "filas":
                        len(datos),

                    "resultado":
                        str(datos[:50])

                }



            return {

                "tipo": "respuesta_sql",

                "agente": self.nombre,

                "respuesta": sql

            }



        except Exception as e:


            print(
                f"[ERROR AGENTE SQL] {str(e)}"
            )


            return {

                "tipo": "error",

                "agente": self.nombre,

                "respuesta":
                f"Error ejecutando SQL: {str(e)}"

            }



    def es_sql(self, texto):

        if not texto:

            return False


        patrones = [

            r"^\s*SELECT",

            r"^\s*WITH"

        ]


        return any(

            re.search(
                patron,
                texto.upper()
            )

            for patron in patrones

        )



    def sql_permitido(self, sql):


        bloqueados = [

            "DROP",

            "DELETE",

            "UPDATE",

            "INSERT",

            "ALTER",

            "TRUNCATE",

            "CREATE",

            "MERGE",

            "CALL"

        ]


        sql_upper = sql.upper()


        return not any(

            palabra in sql_upper

            for palabra in bloqueados

        )