from datetime import datetime


events = []


def add_event(nombre, detalle=None, estado="SUCCESS"):

    events.append({
        "hora": datetime.now().strftime("%H:%M:%S"),
        "evento": nombre,
        "estado": estado,
        "detalle": detalle or {}
    })


def get_events():

    return events


def clear_events():

    events.clear()