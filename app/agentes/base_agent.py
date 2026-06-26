from abc import ABC, abstractmethod

class BaseAgent:
    def execute(self, pregunta):
        raise NotImplementedError("Cada agente debe implementar el método execute")