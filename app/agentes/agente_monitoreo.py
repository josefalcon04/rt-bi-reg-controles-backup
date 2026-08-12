# app/agentes/agente_monitoreo.py

from .base_agent import BaseAgent
from app.servicios.teradata_service import ejecutar_query_teradata
from app.servicios.ollama_service import OllamaService


class AgenteMonitoreo(BaseAgent):

    nombre = "AgenteMonitoreo"

    descripcion = """
    Agente encargado del monitoreo operacional.
    Consulta estados de procesos, layouts,
    ejecuciones batch y controles en Teradata.
    """


    def __init__(self):

        self.ollama = OllamaService()



    def execute(self, pregunta):

        print(
            "[AGENTE MONITOREO]",
            pregunta
        )


        schema_info = """
        Tabla:
        PE_REG_P_FG_CONFIG.VW_SCHEDULE_MATRIZ

        Columnas:
        - NombreLayout
        - TipoSchd
        - FecIniEjec_TS
        - FecFinEjec_TS
        - desEstado
        """


        prompt = f"""

        Eres un especialista en monitoreo operacional BI.

        Usa únicamente esta estructura:

        {schema_info}

        Pregunta:
        {pregunta}

        Genera solamente SQL Teradata.

        Reglas:

        - Para cantidades por estado:
          usar GROUP BY desEstado.

        - Para buscar procesos:
          usar WHERE NombreLayout.

        - Para últimos procesos:
          ordenar por FecIniEjec_TS DESC.

        - Solo consultas SELECT.

        Devuelve solo SQL.
        """



        try:


            sql = self.ollama.llamar(

                pregunta=prompt,

                system_prompt="""
                Eres experto en Teradata SQL.
                Genera únicamente consultas SELECT.
                """

            )


            sql = (
                sql
                .replace("```sql", "")
                .replace("```", "")
                .strip()
            )



            print(
                f"[MONITOREO SQL]: {sql}"
            )



            if not self.validar_sql(sql):

                return {

                    "tipo": "error_seguridad",

                    "agente": self.nombre,

                    "respuesta":
                    "El SQL generado no está permitido."

                }



            datos = ejecutar_query_teradata(
                sql
            )



            if not datos:

                return {

                    "tipo": "sin_datos",

                    "agente": self.nombre,

                    "respuesta":
                    "La consulta no devolvió resultados."

                }



            return {

                "tipo": "monitoreo",

                "agente": self.nombre,

                "sql": sql,

                "respuesta":
                    self.formatear_resultado(datos)

            }



        except Exception as e:


            print(
                f"[ERROR MONITOREO] {str(e)}"
            )


            return {

                "tipo": "error",

                "agente": self.nombre,

                "respuesta":
                    f"Error ejecutando monitoreo: {str(e)}"

            }



    def validar_sql(self, sql):


        if not sql:

            return False



        sql_upper = sql.upper().strip()



        if not sql_upper.startswith(
            "SELECT"
        ):

            return False



        prohibidos = [

            "DROP",
            "DELETE",
            "UPDATE",
            "INSERT",
            "ALTER",
            "TRUNCATE",
            "CREATE",
            "CALL",
            "MERGE"

        ]


        return not any(

            x in sql_upper

            for x in prohibidos

        )



    def formatear_resultado(self, datos):


        if (

            "desEstado" in datos[0]

            and "CANTIDAD" in datos[0]

        ):


            return "\n".join(

                [

                    f"- {x['desEstado']}: {x['CANTIDAD']} procesos"

                    for x in datos

                ]

            )


        return str(
            datos[:50]
        )