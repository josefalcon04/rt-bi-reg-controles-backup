from abc import ABC, abstractmethod

class BaseAgent(ABC):

    @abstractmethod
    def procesar(
        self,
        pregunta,
        memoria="",
        documento=None
    ):
        pass