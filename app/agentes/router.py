# app/agentes/router.py

from .agent_registry import AgentRegistry


class Router:

    def __init__(self):

        self.registry = AgentRegistry()


    def procesar_consulta(self, consulta, memoria=""):

        agente_nombre = self.detectar_agente(
            consulta
        )

        agente = self.registry.get_agent(
            agente_nombre
        )

        if not agente:

            return {

                "tipo": "error",

                "respuesta":
                f"No existe el agente '{agente_nombre}'."

            }


        try:

            return agente.execute(

                pregunta=consulta,

                memoria=memoria

            )


        except TypeError:

            # Compatibilidad con agentes que no usan memoria
            return agente.execute(
                consulta
            )


    def detectar_agente(self, consulta):

        texto = consulta.lower()


        # ------------------------
        # SQL
        # ------------------------

        if any(x in texto for x in [

            "sql",
            "query",
            "select",
            "from",
            "join",
            "where",
            "group by",
            "netezza",
            "teradata",
            "oracle"

        ]):

            return "sql"


        # ------------------------
        # Tendencias
        # ------------------------

        if any(x in texto for x in [

            "tendencia",
            "evolucion",
            "histórico",
            "historico",
            "comparacion",
            "crecimiento",
            "comportamiento"

        ]):

            return "tendencias"


        # ------------------------
        # Monitoreo
        # ------------------------

        if any(x in texto for x in [

            "monitoreo",
            "proceso",
            "batch",
            "control-m",
            "control m",
            "schedule",
            "layout",
            "ejecucion",
            "estado"

        ]):

            return "monitoreo"


        # ------------------------
        # Alertas
        # ------------------------

        if any(x in texto for x in [

            "alerta",
            "caida",
            "caída",
            "fallo",
            "incidente",
            "error"

        ]):

            return "alertas"


        # ------------------------
        # Regulatorio
        # ------------------------

        if any(x in texto for x in [

            "osiptel",
            "norma",
            "regulatorio",
            "reporte",
            "formato",
            "nri"

        ]):

            return "regulatorio"


        # ------------------------
        # Documentación
        # ------------------------

        if any(x in texto for x in [

            "manual",
            "documentacion",
            "documentación",
            "procedimiento",
            "instructivo",
            "guía",
            "guia"

        ]):

            return "documentacion"


        # ------------------------
        # Developer
        # ------------------------

        if any(x in texto for x in [

            "python",
            "flask",
            "api",
            "codigo",
            "código",
            "desarrollo",
            "arquitectura",
            "shell",
            "linux"

        ]):

            return "developer"


        # Agente por defecto

        return "developer"


router = Router()


def obtener_agente(pregunta):

    agente_nombre = router.detectar_agente(
        pregunta
    )

    agente = router.registry.get_agent(
        agente_nombre
    )

    return agente, None