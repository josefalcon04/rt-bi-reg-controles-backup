from flask import Blueprint, render_template, request, jsonify
import time

# Router central
from app.agentes.router import obtener_agente

# Servicio IA
from app.servicios.ollama_service import OllamaService

# Memoria de eventos
from app.memoria.execution_trace import (
    add_event,
    clear_events,
    get_events
)

chatbox_bp = Blueprint("chatbox", __name__)

ollama_service = OllamaService()


def generar_resumen_ejecutivo(respuesta_bruta, pregunta):

    add_event(
        "LLM_SUMMARY_START",
        {
            "modelo": "ollama"
        }
    )

    system_prompt = """
    Eres un asistente ejecutivo senior.

    Resume la información recibida
    de forma sólida, profesional y concisa.

    Usa bullet points si hay datos técnicos.
    Destaca impacto de negocio.
    """

    respuesta = ollama_service.llamar(
        pregunta=f"""
Resume esta respuesta para el usuario:

{respuesta_bruta}
""",
        contexto=respuesta_bruta,
        system_prompt=system_prompt
    )

    add_event("LLM_SUMMARY_FINISH")

    return respuesta


@chatbox_bp.route("/chatbox")
def home():

    return render_template("chatbox.html")

@chatbox_bp.route("/agent_events")
def agent_events():

    return jsonify(
        get_events()
    )
@chatbox_bp.route("/agent_events/reset", methods=["POST"])
def reset_agent_events():

    clear_events()

    return jsonify({
        "status": "ok"
    })

@chatbox_bp.route("/chatbox/ask", methods=["POST"])
def ask():

    data = request.get_json()

    pregunta = data.get(
        "message",
        ""
    ).strip()

    clear_events()

    add_event(
        "CHAT_RECEIVED",
        {
            "pregunta": pregunta
        }
    )

    print(
        f"\n--- [DEBUG] Nueva consulta: '{pregunta}' ---"
    )

    try:

        inicio = time.time()

        # ==========================
        # ROUTER
        # ==========================

        add_event("ROUTER_START")

        agente, documento = obtener_agente(
            pregunta
        )

        if not agente:

            raise Exception(
                "No se encontró un agente disponible"
            )

        add_event(
            "AGENT_SELECTED",
            {
                "agente": type(agente).__name__
            }
        )

        print(
            f"[DEBUG] Router eligió: {type(agente).__name__}"
        )

        # ==========================
        # EJECUCIÓN
        # ==========================

        if documento:

            add_event(
                "DOCUMENT_FOUND",
                {
                    "archivo": documento["archivo"]
                }
            )

            respuesta_bruta = (
                f"Documento: {documento['archivo']}\n\n"
                f"{documento['contenido']}"
            )

        else:

            add_event(
                "AGENT_EXECUTION_START",
                {
                    "agente": type(agente).__name__
                }
            )

            print(
                f"[DEBUG] Ejecutando agente: {type(agente).__name__}"
            )

            if not hasattr(agente, "execute"):

                raise Exception(
                    f"El agente {type(agente).__name__} no tiene método execute()"
                )

            respuesta_agente = agente.execute(
                pregunta
            )

            add_event("AGENT_EXECUTION_FINISH")

            add_event(
                "AGENT_RESPONSE",
                {
                    "tipo": type(respuesta_agente).__name__
                }
            )

            # Algunos agentes devuelven diccionario y otros texto

            if isinstance(respuesta_agente, dict):

                respuesta_bruta = (
                    respuesta_agente.get("respuesta")
                    or respuesta_agente.get("resultado")
                    or respuesta_agente.get("analisis")
                    or str(respuesta_agente)
                )

            else:

                respuesta_bruta = str(
                    respuesta_agente
                )

        # Seguridad por si algún agente devuelve vacío

        if not respuesta_bruta:

            respuesta_bruta = (
                "El agente no generó respuesta."
            )

        # ==========================
        # SÍNTESIS IA
        # ==========================

        if len(str(respuesta_bruta)) < 500:

            add_event(
                "LLM_SUMMARY_SKIPPED",
                {
                    "motivo": "respuesta corta"
                }
            )

            respuesta_final = str(
                respuesta_bruta
            )

        else:

            print(
                "[DEBUG] Ejecutando síntesis ejecutiva"
            )

            respuesta_final = generar_resumen_ejecutivo(
                respuesta_bruta,
                pregunta
            )

        # ==========================
        # FIN
        # ==========================

        tiempo_total = round(
            time.time() - inicio,
            2
        )

        add_event(
            "RESPONSE_GENERATED",
            {
                "tiempo_segundos": tiempo_total
            }
        )

        add_event(
            "CHAT_FINISHED"
        )

        print(
            get_events()
        )

        respuesta_final_con_meta = (
            f"{respuesta_final}"
            f"\n\n*Procesado por "
            f"{type(agente).__name__}"
            f" en {tiempo_total}s*"
        )

        return jsonify(
            {
                "response": respuesta_final_con_meta
            }
        )

    except Exception as e:

        add_event(
            "ERROR",
            {
                "mensaje": str(e)
            },
            estado="ERROR"
        )

        print(
            f"[ERROR] Falló flujo chatbox.py: {str(e)}"
        )

        return jsonify(
            {
                "response":
                f"Ocurrió un error al procesar tu solicitud: {str(e)}"
            }
        ), 500