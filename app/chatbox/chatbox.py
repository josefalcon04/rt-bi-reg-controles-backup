from flask import Blueprint, render_template, request, jsonify, session
import time
# Importamos el router central
from app.agentes.router import obtener_agente
# Importamos el servicio de IA
from app.servicios.ollama_service import llamar_ollama

chatbox_bp = Blueprint("chatbox", __name__)

def generar_resumen_ejecutivo(respuesta_bruta, pregunta):
    """Capa de síntesis para dar un tono profesional y resumido."""
    system_prompt = """
    Eres un asistente ejecutivo senior. 
    Resume la información recibida de forma sólida, profesional y concisa.
    Usa bullet points si hay datos técnicos. Destaca el impacto de negocio.
    """
    
    return llamar_ollama(
        pregunta=f"Resume esta respuesta para el usuario: {respuesta_bruta}",
        contexto=respuesta_bruta,
        system_prompt=system_prompt
    )

@chatbox_bp.route("/chatbox")
def home():
    return render_template("chatbox.html")

@chatbox_bp.route("/chatbox/ask", methods=["POST"])
def ask():
    data = request.get_json()
    pregunta = data.get("message", "").strip()
    
    print(f"\n--- [DEBUG] Nueva consulta: '{pregunta}' ---")

    try:
        inicio = time.time()
        
        # 1. El router decide quién es el experto
        agente, documento = obtener_agente(pregunta)
        
        print(f"[DEBUG] Router eligió: {type(agente).__name__}")
        
        # 2. Ejecución
        if documento:
            print("[DEBUG] Se detectó documento, usando vía rápida.")
            respuesta_bruta = f"Documento: {documento['archivo']}\n\n{documento['contenido']}"
        else:
            print(f"[DEBUG] Ejecutando agente: {type(agente).__name__}")
            respuesta_bruta = agente.execute(pregunta)
            
        # 3. Síntesis ejecutiva inteligente
        # OPTIMIZACIÓN: Si la respuesta es corta (ej: resumen de estados), 
        # saltamos la llamada a generar_resumen_ejecutivo para ahorrar 30s.
        if len(respuesta_bruta) < 500:
            print("[DEBUG] Respuesta corta detectada, omitiendo síntesis de Ollama para mayor velocidad.")
            respuesta_final = respuesta_bruta
        else:
            print("[DEBUG] Respuesta larga detectada, iniciando síntesis ejecutiva...")
            respuesta_final = generar_resumen_ejecutivo(respuesta_bruta, pregunta)
        
        fin = time.time()
        tiempo_total = round(fin - inicio, 2)
        print(f"[DEBUG] Tiempo total: {tiempo_total} segundos")
        
        # Pie de página para auditoría
        respuesta_final_con_meta = f"{respuesta_final}\n\n*Procesado por {type(agente).__name__} en {tiempo_total}s*"
        
        return jsonify({"response": respuesta_final_con_meta})

    except Exception as e:
        print(f"[ERROR] Falló el flujo en chatbox.py: {str(e)}")
        return jsonify({"response": f"Ocurrió un error al procesar tu solicitud: {str(e)}"}), 500