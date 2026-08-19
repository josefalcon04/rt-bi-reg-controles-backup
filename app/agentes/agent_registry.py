from .agente_monitoreo import AgenteMonitoreo
from .agente_regulatorio import AgenteRegulatorio
from .agente_sql import AgenteSQL
from .agente_alertas import AgenteAlertas
from .agente_developer import AgenteDeveloper
from .agente_tendencias import AgenteTendencias
from .agente_documentacion import AgenteDocumentacion
from .agente_dashboard import AgenteDashboard


class AgentRegistry:

    def __init__(self):

        self.agentes = {

            "monitoreo":
                AgenteMonitoreo(),

            "regulatorio":
                AgenteRegulatorio(),

            "sql":
                AgenteSQL(),

            "alertas":
                AgenteAlertas(),

            "developer":
                AgenteDeveloper(),

            "tendencias":
                AgenteTendencias(),

            "documentacion":
                AgenteDocumentacion(),

            "dashboard":
                AgenteDashboard()

        }


    def get_agent(self, nombre):

        if not nombre:
            return None

        return self.agentes.get(
            nombre.lower()
        )


    def list_agents(self):

        return list(
            self.agentes.keys()
        )