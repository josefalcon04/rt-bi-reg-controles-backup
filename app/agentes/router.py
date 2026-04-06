from .agente_monitoreo import AgenteMonitoreo
from .agente_regulatorio import AgenteRegulatorio
from .agente_sql import AgenteSQL
from .agente_alertas import AgenteAlertas
from .agente_developer import AgenteDeveloper
from .agente_tendencias import AgenteTendencias

from app.servicios.documentacion_service import (
    DocumentacionService
)


def obtener_agente(pregunta):

    p = pregunta.lower()

    # =====================
    # SQL / DESARROLLO
    # =====================
    if any(x in p for x in [
        "sql", "netezza", "oracle", "python",
        "flask", "shell", "script", "codigo",
        "código", "query", "procedure",
        "optimiza", "convierte"
    ]):
        return AgenteSQL(), None

    # =====================
    # TENDENCIAS
    # =====================
    if any(x in p for x in [
        "tendencia", "tendencias",
        "evolución", "proyección",
        "proyeccion", "planta", "mtc"
    ]):
        return AgenteTendencias(), None

    # =====================
    # MONITOREO
    # =====================
    if any(x in p for x in [
        "log", "logs", "error", "fallo",
        "estado", "ejecución", "ejecuto"
    ]):
        return AgenteMonitoreo(), None

    # =====================
    # ALERTAS
    # =====================
    if any(x in p for x in [
        "alerta", "alertas",
        "notificacion", "notificación"
    ]):
        return AgenteAlertas(), None

    # =====================
    # DOCUMENTACIÓN (REGULATORIO)
    # =====================

    doc_service = DocumentacionService()
    documento = doc_service.buscar(pregunta)

    if documento:

        print(
            f"[ROUTER] Documento encontrado: "
            f"{documento['archivo']}"
        )

        return AgenteRegulatorio(), documento

    # =====================
    # DEFAULT
    # =====================
    return AgenteDeveloper(), None