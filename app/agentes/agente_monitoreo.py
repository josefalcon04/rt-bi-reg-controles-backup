# app/agentes/agente_monitoreo.py

import re

from .base_agent import BaseAgent
from app.servicios.teradata_service import ejecutar_query_teradata
from app.servicios.ollama_service import OllamaService


class AgenteMonitoreo(BaseAgent):

    nombre = "AgenteMonitoreo"

    descripcion = """
    Agente encargado del monitoreo operacional BI.
    Consulta estados de procesos, layouts, ejecuciones batch
    y controles en Teradata.
    """

    TABLA_PRINCIPAL = "PE_REG_P_FG_CONFIG.VW_SCHEDULE_MATRIZ"

    def __init__(self):
        self.ollama = OllamaService()

    def execute(self, pregunta):

        print(
            "[AGENTE MONITOREO]",
            pregunta
        )

        schema_info = f"""
        Tabla principal:
        {self.TABLA_PRINCIPAL}

        Columnas disponibles:
        - NombreLayout
        - TipoSchd
        - FecIniEjec_TS
        - FecFinEjec_TS
        - desEstado
        """

        prompt = f"""
        Eres un especialista en monitoreo operacional BI y Teradata.

        Base de datos destino:
        TERADATA.

        Usa únicamente la siguiente estructura:

        {schema_info}

        Pregunta del usuario:
        {pregunta}

        Genera UNA consulta SQL SELECT compatible con Teradata.

        REGLAS OBLIGATORIAS:

        1. Solo generar SELECT.
        2. No generar INSERT, UPDATE, DELETE, DROP, ALTER,
           CREATE, TRUNCATE, MERGE ni CALL.
        3. No utilizar LIMIT.
        4. No utilizar OFFSET.
        5. NO utilizar FETCH FIRST ni FETCH NEXT.
        6. Para obtener los últimos N registros utiliza:
           QUALIFY ROW_NUMBER() OVER (
               ORDER BY FecIniEjec_TS DESC
           ) <= N
        7. Para consultar cantidades por estado:
           GROUP BY desEstado
        8. Para buscar un proceso específico:
           utilizar NombreLayout.
        9. Para ordenar los últimos procesos:
           ORDER BY FecIniEjec_TS DESC
        10. Utiliza únicamente la tabla indicada.
        11. No inventes columnas.
        12. No expliques el SQL.
        13. Devuelve solamente el SQL.

        Ejemplo para "últimos 10 schedules":

        SELECT
            NombreLayout,
            TipoSchd,
            FecIniEjec_TS,
            FecFinEjec_TS,
            desEstado
        FROM {self.TABLA_PRINCIPAL}
        QUALIFY ROW_NUMBER() OVER (
            ORDER BY FecIniEjec_TS DESC
        ) <= 10
        ORDER BY FecIniEjec_TS DESC;
        """

        try:

            sql = self.ollama.llamar(
                pregunta=prompt,
                system_prompt="""
                Eres experto en Teradata SQL.

                Genera únicamente consultas SELECT.

                IMPORTANTE:
                - El motor es Teradata.
                - No uses LIMIT.
                - No uses OFFSET.
                - No uses FETCH FIRST.
                - Para limitar filas usa QUALIFY con ROW_NUMBER().
                - No inventes tablas ni columnas.
                """
            )

            sql = self.limpiar_sql(sql)

            # ==========================================
            # NORMALIZACIÓN DE SINTAXIS TERADATA
            # ==========================================

            sql = self.normalizar_sql_teradata(sql)

            print(
                f"[MONITOREO SQL]: {sql}"
            )

            # ==========================================
            # VALIDACIÓN DE SEGURIDAD
            # ==========================================

            if not self.validar_sql(sql):

                return {
                    "tipo": "error_seguridad",
                    "agente": self.nombre,
                    "respuesta":
                        "El SQL generado no está permitido."
                }

            # ==========================================
            # EJECUCIÓN
            # ==========================================

            datos = ejecutar_query_teradata(sql)

            # ==========================================
            # SIN RESULTADOS
            # ==========================================

            if not datos:

                return {
                    "tipo": "sin_datos",
                    "agente": self.nombre,
                    "sql": sql,
                    "respuesta":
                        "La consulta fue ejecutada correctamente, "
                        "pero no se encontraron resultados."
                }

            # ==========================================
            # RESULTADO
            # ==========================================

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
                    f"No fue posible ejecutar la consulta de monitoreo: {str(e)}"
            }

    # ==================================================
    # LIMPIAR SQL GENERADO POR OLLAMA
    # ==================================================

    def limpiar_sql(self, sql):

        if not sql:
            return ""

        sql = (
            sql
            .replace("```sql", "")
            .replace("```SQL", "")
            .replace("```", "")
            .strip()
        )

        return sql

    # ==================================================
    # NORMALIZAR SINTAXIS TERADATA
    # ==================================================

    def normalizar_sql_teradata(self, sql):

        if not sql:
            return sql

        sql = sql.strip().rstrip(";")

        # --------------------------------------------------
        # Conversión de:
        #
        # ORDER BY campo DESC
        # FETCH FIRST 10 ROWS ONLY
        #
        # a:
        #
        # QUALIFY ROW_NUMBER() OVER (
        #     ORDER BY campo DESC
        # ) <= 10
        # ORDER BY campo DESC
        #
        # Esto evita que el modelo genere sintaxis FETCH
        # incompatible con el entorno Teradata utilizado.
        # --------------------------------------------------

        patron = re.compile(
            r"ORDER\s+BY\s+"
            r"([A-Za-z_][A-Za-z0-9_.]*"
            r"(?:\s+(?:ASC|DESC))?)"
            r"\s+FETCH\s+"
            r"(?:FIRST|NEXT)\s+"
            r"(\d+)\s+ROWS?\s+ONLY",
            re.IGNORECASE
        )

        match = patron.search(sql)

        if match:

            orden = match.group(1)
            limite = match.group(2)

            reemplazo = (
                f"QUALIFY ROW_NUMBER() OVER "
                f"(ORDER BY {orden}) <= {limite} "
                f"ORDER BY {orden}"
            )

            sql = patron.sub(
                reemplazo,
                sql,
                count=1
            )

            print(
                "[MONITOREO] Sintaxis FETCH FIRST "
                "convertida a QUALIFY."
            )

        return sql + ";"

    # ==================================================
    # VALIDAR SQL
    # ==================================================

    def validar_sql(self, sql):

        if not sql:
            return False

        sql_upper = sql.upper().strip()

        # Debe comenzar con SELECT
        if not sql_upper.startswith("SELECT"):
            return False

        # --------------------------------------------------
        # Operaciones prohibidas
        # --------------------------------------------------

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

        if any(
            palabra in sql_upper
            for palabra in prohibidos
        ):
            return False

        # --------------------------------------------------
        # Sintaxis que no queremos permitir
        # --------------------------------------------------

        if " LIMIT " in f" {sql_upper} ":
            return False

        if " OFFSET " in f" {sql_upper} ":
            return False

        if " FETCH " in f" {sql_upper} ":
            return False

        # --------------------------------------------------
        # Solo permitir la tabla de monitoreo conocida
        # --------------------------------------------------

        if self.TABLA_PRINCIPAL.upper() not in sql_upper:
            print(
                "[MONITOREO] SQL rechazado: "
                "tabla no autorizada."
            )
            return False

        return True

    # ==================================================
    # FORMATEAR RESULTADO
    # ==================================================

    def formatear_resultado(self, datos):

        if not datos:
            return "No se encontraron resultados."

        # --------------------------------------------------
        # Resultado agrupado por estado
        # --------------------------------------------------

        primera_fila = datos[0]

        claves = {
            str(k).upper(): k
            for k in primera_fila.keys()
        }

        if (
            "DESESTADO" in claves
            and "CANTIDADPROCESOS" in claves
        ):

            clave_estado = claves["DESESTADO"]
            clave_cantidad = claves["CANTIDADPROCESOS"]

            return "\n".join(
                [
                    f"- {fila[clave_estado]}: "
                    f"{fila[clave_cantidad]} procesos"
                    for fila in datos
                ]
            )

        # Compatibilidad con alias CANTIDAD
        if (
            "DESESTADO" in claves
            and "CANTIDAD" in claves
        ):

            clave_estado = claves["DESESTADO"]
            clave_cantidad = claves["CANTIDAD"]

            return "\n".join(
                [
                    f"- {fila[clave_estado]}: "
                    f"{fila[clave_cantidad]} procesos"
                    for fila in datos
                ]
            )

        # --------------------------------------------------
        # Resultado general
        # --------------------------------------------------

        return str(datos[:50])

