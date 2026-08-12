# app/servicios/auditoria_service.py

from datetime import datetime


def registrar_evento(
    agente,
    pregunta,
    respuesta=None,
    estado="OK",
    tiempo_ms=None
):
    """
    Registra la interacción de un agente.

    Futuro:
    - Insertar en tabla de auditoría
    - Guardar usuario
    - Guardar sesión
    - Guardar tokens consumidos
    """

    evento = {

        "fecha": datetime.now(),

        "agente": agente,

        "pregunta": pregunta,

        "respuesta": respuesta,

        "estado": estado,

        "tiempo_ms": tiempo_ms

    }


    print(
        "[AUDITORIA]",
        evento
    )


    return evento



def registrar_error(
    agente,
    pregunta,
    error
):

    """
    Registra errores generados
    por agentes o servicios.
    """


    return registrar_evento(

        agente=agente,

        pregunta=pregunta,

        respuesta=str(error),

        estado="ERROR"

    )