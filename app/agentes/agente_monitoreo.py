from .base_agent import BaseAgent
from app.servicios.netezza_service import ejecutar_query
from app.servicios.teradata_service import ejecutar_query_teradata
from app.servicios.ollama_service import llamar_ollama

class AgenteMonitoreo(BaseAgent):
    
    def execute(self, pregunta):
        pregunta_limpia = pregunta.lower().strip()
        
        # 1. Definición del contexto de datos (El "Schema" de tu tabla)
        # Esto le da al modelo las herramientas para generar el SQL correcto
        schema_info = {
            "tabla": "PE_REG_P_FG_CONFIG.VW_SCHEDULE_MATRIZ",
            "columnas": "NombreLayout, TipoSchd, FecIniEjec_TS, FecFinEjec_TS, desEstado"
        }
        
        # 2. IA Genera el SQL específico y optimizado
        prompt = f"""
        Eres un experto en bases de datos Teradata. 
        Tabla: {schema_info['tabla']}
        Columnas disponibles: {schema_info['columnas']}
        
        Pregunta del usuario: "{pregunta_limpia}"
        
        Genera un único query SQL de Teradata que responda exactamente a la pregunta.
        - Si pide resumen/cantidad por estado, usa GROUP BY desEstado.
        - Si pide detalle, usa WHERE.
        - IMPORTANTE: Devuelve SOLO el código SQL, sin explicaciones ni formato Markdown.
        """
        
        sql_dinamico = llamar_ollama(pregunta=prompt, system_prompt="Eres un experto SQL.")
        # Limpieza básica por si el modelo devuelve marcas de código
        sql_dinamico = sql_dinamico.replace("```sql", "").replace("```", "").strip()
        
        print(f"[DEBUG MONITOR] SQL Generado por IA: {sql_dinamico}")
        
        # 3. Ejecución Directa (Sin descargar toda la tabla)
        try:
            datos = ejecutar_query_teradata(sql_dinamico)
            
            if not datos:
                return "La consulta se ejecutó pero no devolvió resultados."

            # 4. Formateo rápido
            # Si el resultado es un resumen (desEstado, CANTIDAD), formateamos como lista
            if 'desEstado' in datos[0] and 'CANTIDAD' in datos[0]:
                resumen = "\n".join([f"- {d.get('desEstado')}: {d.get('CANTIDAD')} procesos" for d in datos])
                return f"Aquí tienes el detalle solicitado:\n\n{resumen}"
            
            # Si es detalle, devolvemos los datos
            return f"Resultado:\n{str(datos)}"

        except Exception as e:
            return f"Error al ejecutar el SQL generado: {str(e)}"