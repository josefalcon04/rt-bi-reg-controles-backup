from app.servicios.bases.netezza import conectar_netezza
from app.servicios.bases.teradata import conectar_teradata


class ConnectionManager:

    @staticmethod
    def get_netezza():
        return conectar_netezza()


    @staticmethod
    def get_teradata():
        return conectar_teradata()