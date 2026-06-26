from .base_agent import BaseAgent
from app.servicios.netezza_service import ejecutar_query
from app.servicios.tendencias_service import buscar_consulta_tendencia
from app.servicios.ollama_service import llamar_ollama

class AgenteTendencias(BaseAgent):

    def execute(self, pregunta):
        print("[AGENTE] Tendencias ejecutando:", pregunta)

        # 1. Buscar catálogo
        consulta = buscar_consulta_tendencia(pregunta)
        if not consulta:
            return "No encontré una tendencia relacionada en el catálogo."

        # 2. Ejecutar query
        datos = ejecutar_query(consulta["QUERY_SQL"])
        if not datos:
            return "La consulta de tendencias no retornó datos en Netezza."

        # 3. Convertir datos a formato compacto
        datos_txt = "\n".join(
            f"{d.get('PERIODO')} | {d.get('MODALIDAD')} | {d.get('CANTIDAD')}"
            for d in datos
        )

        # 4. Prompt analítico
        prompt = f"""
        Analiza esta serie temporal:
        {datos_txt}
        
        Devuelve: Tendencia general, comparación PREPAGO vs POSTPAGO, cambios relevantes y conclusión ejecutiva breve.
        """

        analisis = llamar_ollama(
            pregunta=prompt,
            system_prompt="Eres un analista de datos empresarial. Responde en texto plano, sin markdown."
        )

        # 5. Respuesta formateada como string (para que el chatbox pueda procesarla)
        titulo = consulta["NOMBRE_CONSULTA"].replace("TENDENCIA_", "").replace("_", " ").title()
        
        return f"--- {titulo} ---\n\n{analisis}"