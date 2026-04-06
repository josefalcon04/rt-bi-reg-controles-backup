from .base_agent import BaseAgent
from app.servicios.netezza_service import ejecutar_query
from app.servicios.tendencias_service import buscar_consulta_tendencia
from app.servicios.ollama_service import llamar_ollama


class AgenteTendencias(BaseAgent):

    def procesar(
        self,
        pregunta,
        memoria="",
        documento=None
    ):

        print("[AGENTE] Tendencias ejecutando:", pregunta)

        # 1. Buscar catálogo
        consulta = buscar_consulta_tendencia(pregunta)

        if not consulta:
            return {
                "tipo": "tendencia",
                "error": "No encontré una tendencia relacionada en el catálogo."
            }

        # 2. Ejecutar query
        datos = ejecutar_query(consulta["QUERY_SQL"])

        if not datos:
            return {
                "tipo": "tendencia",
                "error": "La consulta no retornó datos."
            }

        # 3. Convertir datos a formato compacto para LLM
        datos_txt = "\n".join(
            f"{d.get('PERIODO')} | {d.get('MODALIDAD')} | {d.get('CANTIDAD')}"
            for d in datos
        )

        # 4. Prompt analítico (sin formato UI)
        prompt = f"""
Eres un analista senior de datos.

Analiza esta serie temporal y responde SOLO en texto plano:

DATOS:
{datos_txt}

Devuelve:

- Tendencia general
- Comparación PREPAGO vs POSTPAGO
- Cambios relevantes
- Conclusión ejecutiva breve (máx 5 líneas)

No uses emojis, ni títulos decorativos, ni markdown.
"""

        # 5. LLM
        analisis = llamar_ollama(
            pregunta=prompt,
            system_prompt="Eres un analista de datos empresarial."
        )

        # 6. Título limpio
        titulo = consulta["NOMBRE_CONSULTA"] \
            .replace("TENDENCIA_", "") \
            .replace("_", " ") \
            .title()

        # 7. RESPUESTA ESTRUCTURADA (IMPORTANTE)
        return {
            "tipo": "tendencia",
            "titulo": titulo,
            "analisis": analisis,
            "datos": datos
        }