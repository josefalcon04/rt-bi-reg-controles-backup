from .agente_monitoreo import AgenteMonitoreo
from .agente_regulatorio import AgenteRegulatorio
from .agente_sql import AgenteSQL
from .agente_alertas import AgenteAlertas
from .agente_developer import AgenteDeveloper
from .agente_tendencias import AgenteTendencias
#from app.servicios.documentacion_service import DocumentacionService
from app.servicios.ollama_service import llamar_ollama

def clasificar_agente_con_ia(pregunta):
    system_prompt = """
    Eres un clasificador de agentes.
    - Si la pregunta es sobre "quién te creó", "quién es tu autor", o datos de identidad del BI Assistant, clasifícalo como AgenteRegulatorio.
    - Agentes disponibles: [AgenteSQL, AgenteTendencias, AgenteMonitoreo, AgenteAlertas, AgenteRegulatorio, AgenteDeveloper]
    """
    
    # Llamamos a Ollama con una temperatura muy baja (determinista)
    # No necesitamos contexto ni memoria para clasificar
    resultado = llamar_ollama(
        pregunta=pregunta, 
        system_prompt=system_prompt
    )
    
    return resultado.strip()

def obtener_agente(pregunta):
    p = pregunta.lower().strip()
    
    # 1. Bypass para Identidad (Crítico)
    if any(x in p for x in ["creador", "quien te creo", "quien te hizo"]):
        return AgenteDeveloper(), None
    
    # 2. Prioridad de Monitoreo (Nueva capa obligatoria)
    # Si detectamos palabras clave de Teradata, forzamos AgenteMonitoreo
    palabras_monitoreo = ["teradata", "procesos", "log", "finalizaron", "pendiente", "error"]
    if any(keyword in p for keyword in palabras_monitoreo):
        print(f"[ROUTER] Prioridad detectada: AgenteMonitoreo por keyword")
        return AgenteMonitoreo(), None

    # 3. Prioridad: Documentación (Solo si el score es alto)
    # doc_service = DocumentacionService()
    # documento = doc_service.buscar(pregunta)
    # if documento and documento.get('score', 0) > 5: 
    #     return AgenteRegulatorio(), documento

    # 4. Clasificación mediante LLM (Como respaldo si no es nada de lo anterior)
    nombre_agente = clasificar_agente_con_ia(pregunta)
    
    # 5. Mapeo seguro
    mapeo = {
        "AgenteSQL": AgenteSQL(),
        "AgenteTendencias": AgenteTendencias(),
        "AgenteMonitoreo": AgenteMonitoreo(),
        "AgenteAlertas": AgenteAlertas(),
        "AgenteDeveloper": AgenteDeveloper()
    }
    
    agente_final = mapeo.get(nombre_agente, AgenteDeveloper())
    print(f"[ROUTER] IA clasificó como: {nombre_agente}")
    
    return agente_final, None