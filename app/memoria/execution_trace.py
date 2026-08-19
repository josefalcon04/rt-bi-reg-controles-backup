# ============================================================
# EXECUTION TRACE
# Monitor de ejecución de agentes IA
# ============================================================

from datetime import datetime
from threading import Lock


# ============================================================
# ALMACENAMIENTO DE EVENTOS
# ============================================================

events = []

_events_lock = Lock()


# ============================================================
# AGREGAR EVENTO
# ============================================================

def add_event(nombre, detalle=None, estado="SUCCESS"):
    """
    Registra un evento de ejecución.

    Parámetros:
        nombre  : nombre del evento
        detalle : información adicional
        estado  : RUNNING / SUCCESS / ERROR
    """

    evento = {
        "hora": datetime.now().strftime("%H:%M:%S"),
        "evento": nombre,
        "estado": estado,
        "detalle": detalle or {}
    }

    with _events_lock:
        events.append(evento)

    return evento


# ============================================================
# OBTENER EVENTOS
# ============================================================

def get_events():
    """
    Devuelve una copia de los eventos actuales.

    Se devuelve una copia para evitar problemas cuando
    Flask está leyendo mientras otro proceso agrega eventos.
    """

    with _events_lock:
        return list(events)


# ============================================================
# LIMPIAR EVENTOS
# ============================================================

def clear_events():
    """
    Limpia todos los eventos de ejecución.
    """

    with _events_lock:
        events.clear()


# ============================================================
# EVENTOS AUXILIARES
# ============================================================

def start_event(nombre, detalle=None):
    """
    Evento que indica inicio de una operación.
    """

    return add_event(
        nombre,
        detalle,
        "RUNNING"
    )


def success_event(nombre, detalle=None):
    """
    Evento que indica operación completada correctamente.
    """

    return add_event(
        nombre,
        detalle,
        "SUCCESS"
    )


def error_event(nombre, detalle=None):
    """
    Evento que indica error.
    """

    return add_event(
        nombre,
        detalle,
        "ERROR"
    )