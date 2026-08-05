from .base_agent import BaseAgent
from app.servicios.ollama_service import llamar_ollama
from app.servicios.bases.connection_manager import conectar_netezza
import pandas as pd

class AgenteSQL(BaseAgent):
    
    def execute(self, pregunta):
        # 1. Primero, pedimos al LLM que genere o valide el SQL
        system_prompt = """
        Eres un experto en Netezza, teradata y Oracle. 
        Si el usuario pide datos, genera la sentencia SQL. 
        Si el usuario pide optimizar, devuelve el SQL optimizado.
        Responde solo con el bloque de código SQL si es posible.
        """
        
        sql_generado = llamar_ollama(pregunta=pregunta, system_prompt=system_prompt)
        
        # 2. Lógica para ejecutar (opcional: solo si el agente detecta que debe hacerlo)
        # Aquí podrías agregar un filtro de seguridad antes de conectar
        if "SELECT" in sql_generado.upper():
            try:
                conn = conectar_netezza()
                df = pd.read_sql(sql_generado, conn)
                conn.close()
                return f"Consulta ejecutada con éxito. Resultados:\n{df.head().to_string()}"
            except Exception as e:
                return f"Error ejecutando SQL: {str(e)}"
        
        return sql_generado