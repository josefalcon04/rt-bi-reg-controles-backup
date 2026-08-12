# app/agentes/base_agent.py

from abc import ABC, abstractmethod


class BaseAgent(ABC):

    nombre = "BaseAgent"
    descripcion = ""

    @abstractmethod
    def execute(self, pregunta, **kwargs):
        pass