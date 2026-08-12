from datetime import datetime


class EventBus:

    listeners = []

    @classmethod
    def subscribe(cls, callback):
        cls.listeners.append(callback)


    @classmethod
    def emit(cls, event, data=None):

        mensaje = {
            "evento": event,
            "fecha": datetime.now().strftime("%H:%M:%S"),
            "data": data
        }

        for listener in cls.listeners:
            listener(mensaje)