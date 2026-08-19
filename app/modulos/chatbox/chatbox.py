from flask import (
    Blueprint,
    render_template,
    request,
    jsonify,
    session
)

import time
import json
import ast
import re


# ============================================================
# ROUTER CENTRAL
# ============================================================

from app.agentes.router import router


# ============================================================
# SERVICIO IA
# ============================================================

from app.servicios.ollama_service import OllamaService


# ============================================================
# SERVICIO DE MEMORIA
# ============================================================

from app.servicios.memoria_service import MemoriaService


# ============================================================
# MEMORIA DE EVENTOS
# ============================================================

from app.memoria.execution_trace import (
    add_event,
    clear_events,
    get_events
)


# ============================================================
# BLUEPRINT
# ============================================================

chatbox_bp = Blueprint(
    "chatbox",
    __name__
)


# ============================================================
# SERVICIOS
# ============================================================

ollama_service = OllamaService()

memoria_service = MemoriaService()


def generar_resumen_ejecutivo(
    respuesta_bruta,
    pregunta,
    contexto_memoria=""
):
    modelo_resumen = "qwen2.5-coder:3b"

    add_event(
        "LLM_SUMMARY_START",
        {
            "modelo": modelo_resumen
        }
    )

    system_prompt = """
Transforma los datos proporcionados en una respuesta ejecutiva, clara,
visual y precisa para un usuario de negocio.

REGLAS OBLIGATORIAS:
1. Responde siempre en español.
2. Usa únicamente los datos proporcionados.
3. No inventes información ni relaciones entre datos.
4. Mantén estrictamente la correspondencia entre cada proceso y su estado.
5. Nunca asignes a un proceso el estado de otro registro.
6. "Schedule en Error" = "Con error".
7. "Schedule en Proceso" = "En proceso".
8. "Schedule Finalizado" = "Finalizado".
9. No interpretes "Error", "Proceso" o "Finalizado" como "Cancelado"
   salvo que los datos indiquen explícitamente esa equivalencia.
10. Si la pregunta pide procesos de un estado específico, incluye únicamente
    los registros que realmente cumplen ese estado.
11. Si existen varios estados, agrúpalos por estado.
12. Conserva exactamente los nombres de los procesos.
13. No agregues causas, recomendaciones ni conclusiones no sustentadas.
14. No muestres estructuras Python, diccionarios, Timestamp, NaT ni JSON.
15. Sé directo y fácil de leer.
16. Usa estos indicadores cuando correspondan:
    🔴 Con error
    🟡 En proceso
    🟢 Finalizado
17. Indica la cantidad de registros por estado cuando pueda calcularse.
18. Termina con el total de registros consultados cuando sea posible.

FORMATO PREFERIDO:

**Estado de los procesos**

🔴 **Con error (N)**
- PROCESO_1
- PROCESO_2

🟡 **En proceso (N)**
- PROCESO_3

🟢 **Finalizados (N)**
- PROCESO_4

**Total consultado: N procesos.**

Si solo existe un estado relevante, muestra únicamente esa categoría.
No agregues categorías que no existan en los datos.
"""

    contexto_completo = respuesta_bruta

    if contexto_memoria:
        contexto_completo = (
            "CONTEXTO DE MEMORIA AUTORIZADO:\n\n"
            + contexto_memoria
            + "\n\nRESULTADO ACTUAL:\n\n"
            + str(respuesta_bruta)
        )

    respuesta = ollama_service.llamar(
        pregunta=f"""
Pregunta del usuario:

{pregunta}

Genera la respuesta final utilizando exclusivamente
la información proporcionada.

Resultado:

{contexto_completo}
""",
        contexto=contexto_completo,
        system_prompt=system_prompt,
        modelo=modelo_resumen
    )

    add_event(
        "LLM_SUMMARY_FINISH"
    )

    return respuesta


# ============================================================
# PÁGINA PRINCIPAL
# ============================================================

@chatbox_bp.route("/chatbox")
def home():

    return render_template(
        "chatbox.html"
    )


# ============================================================
# EVENTOS DEL AGENT FLOW
# ============================================================

@chatbox_bp.route("/agent_events")
def agent_events():

    return jsonify(
        get_events()
    )


# ============================================================
# RESET DE EVENTOS
# ============================================================

@chatbox_bp.route(
    "/agent_events/reset",
    methods=["POST"]
)
def reset_agent_events():

    clear_events()

    return jsonify({
        "status": "ok"
    })


# ============================================================
# CHAT
# ============================================================

@chatbox_bp.route(
    "/chatbox/ask",
    methods=["POST"]
)
def ask():

    data = request.get_json()

    pregunta = (
        data.get(
            "message",
            ""
        )
        .strip()
    )


    # ========================================================
    # VALIDAR PREGUNTA
    # ========================================================

    if not pregunta:

        return jsonify({
            "response":
                "Por favor, ingresa una pregunta."
        }), 400


    # ========================================================
    # OBTENER USUARIO AUTENTICADO
    # ========================================================

    id_usuario = session.get(
        "usuario_id"
    )

    if not id_usuario:

        return jsonify({
            "response":
                "Tu sesión no contiene un usuario válido."
        }), 401


    # ========================================================
    # INICIALIZAR TRAZA
    # ========================================================

    clear_events()

    add_event(
        "CHAT_RECEIVED",
        {
            "pregunta": pregunta,
            "id_usuario": id_usuario
        }
    )


    print(
        f"\n--- [DEBUG] Nueva consulta: "
        f"'{pregunta}' ---"
    )

    print(
        f"[DEBUG] Usuario autenticado: "
        f"{id_usuario}"
    )


    try:

        inicio = time.time()


        # ====================================================
        # VARIABLES GENERALES
        # ====================================================

        contexto_memoria = ""

        memorias_relevantes = []

        memoria_directa = None

        respuesta_bruta = ""

        respuesta_final = ""

        procesado_por = "Sistema"


        # ====================================================
        # MEMORIA
        # ====================================================

        add_event(
            "MEMORY_SEARCH_START",
            {
                "id_usuario": id_usuario
            }
        )


        try:

            # ------------------------------------------------
            # BUSCAR MEMORIAS AUTORIZADAS Y RELEVANTES
            # ------------------------------------------------

            memorias_relevantes = (
                memoria_service.buscar_memorias_semanticas(
                    pregunta=pregunta,
                    limite=3
                )
            )


            # ------------------------------------------------
            # CONSTRUIR CONTEXTO
            # ------------------------------------------------

            contexto_memoria = (
                memoria_service.construir_contexto(
                    memorias_relevantes
                )
            )


            # ------------------------------------------------
            # EVALUAR MEJOR MEMORIA
            #
            # La búsqueda semántica ya aplica:
            #
            # ESTADO = A
            # SIMILITUD >= UMBRAL_SIMILITUD
            #
            # Luego evaluar_memoria() valida:
            #
            # similitud
            # confianza
            # utilidad
            # score_final
            # ------------------------------------------------

            if memorias_relevantes:

                mejor_memoria = (
                    memorias_relevantes[0]
                )

                evaluacion = (
                    memoria_service.evaluar_memoria(
                        mejor_memoria
                    )
                )


                print(
                    "[DEBUG] Mejor memoria:",
                    mejor_memoria.get(
                        "id_memoria"
                    )
                )


                print(
                    "[DEBUG] Similitud:",
                    evaluacion.get(
                        "similitud_semantica"
                    )
                )


                print(
                    "[DEBUG] Score final:",
                    evaluacion.get(
                        "score_final"
                    )
                )


                print(
                    "[DEBUG] Confianza:",
                    evaluacion.get(
                        "confianza"
                    )
                )


                print(
                    "[DEBUG] Utilidad:",
                    evaluacion.get(
                        "utilidad"
                    )
                )


                if evaluacion.get(
                    "aprobada"
                ):

                    memoria_directa = (
                        mejor_memoria
                    )


            # ------------------------------------------------
            # EVENTO DE MEMORIA
            # ------------------------------------------------

            add_event(
                "MEMORY_SEARCH_FINISH",
                {
                    "cantidad":
                        len(
                            memorias_relevantes
                        ),

                    "memoria_directa":
                        (
                            memoria_directa
                            is not None
                        )
                }
            )


            print(
                "[DEBUG] Memorias relevantes:",
                len(
                    memorias_relevantes
                )
            )


            if contexto_memoria:

                print(
                    "[DEBUG] Contexto de memoria encontrado"
                )

                print(
                    contexto_memoria
                )

            else:

                print(
                    "[DEBUG] No existe memoria relevante"
                )


        except Exception as memoria_error:

            # ------------------------------------------------
            # LA MEMORIA NUNCA DEBE BOTAR EL CHATBOX
            # ------------------------------------------------

            print(
                "[WARNING] Falló búsqueda de memoria:",
                str(memoria_error)
            )


            add_event(
                "MEMORY_SEARCH_ERROR",
                {
                    "mensaje":
                        str(memoria_error)
                }
            )


            # ------------------------------------------------
            # CONTINUAMOS SIN MEMORIA
            # ------------------------------------------------

            memorias_relevantes = []

            contexto_memoria = ""

            memoria_directa = None


        # ====================================================
        # RESPUESTA DIRECTA DESDE MEMORIA
        # ====================================================

        if memoria_directa:

            print(
                "[MEMORIA] RESPUESTA DIRECTA ACTIVADA"
            )


            print(
                "[MEMORIA] ID:",
                memoria_directa.get(
                    "id_memoria"
                )
            )


            print(
                "[MEMORIA] SIMILITUD:",
                memoria_directa.get(
                    "similitud_semantica"
                )
            )


            add_event(
                "MEMORY_DIRECT_RESPONSE",
                {
                    "id_memoria":
                        memoria_directa.get(
                            "id_memoria"
                        ),

                    "score":
                        memoria_directa.get(
                            "similitud_semantica"
                        ),

                    "categoria":
                        memoria_directa.get(
                            "categoria"
                        )
                }
            )


            respuesta_bruta = (
                memoria_directa.get(
                    "contenido",
                    ""
                )
                or ""
            )


            if not respuesta_bruta:

                raise Exception(
                    "La memoria seleccionada "
                    "no contiene información."
                )


            respuesta_final = (
                respuesta_bruta
            )


            procesado_por = (
                "Memoria"
            )


        # ====================================================
        # SI NO HAY MEMORIA DIRECTA
        # CONTINUAMOS CON EL ROUTER CENTRAL
        # ====================================================

        else:

            # =================================================
            # ROUTER CENTRAL
            # =================================================

            add_event(
                "ROUTER_START"
            )

            print(
                "[ROUTER] Enviando consulta al Router central"
            )

            print(
                f"[ROUTER] Pregunta: {pregunta}"
            )

            # El Router es responsable de: 
            #   1. Detectar la intención.
            #   2. Seleccionar el agente.
            #   3. Ejecutar el agente.
            #   4. Pasar memoria autorizada cuando corresponda.

            resultado_router = router.procesar_consulta(
                consulta=pregunta,
                memoria=contexto_memoria
            )

            print(
                "[ROUTER] Resultado recibido"
            )

            print(
                f"[ROUTER] Tipo resultado: "
                f"{type(resultado_router).__name__}"
            )

            if resultado_router is None:

                raise Exception(
                    "El Router no devolvió ningún resultado."
                )

            # =================================================
            # NORMALIZAR RESPUESTA DEL ROUTER
            # =================================================

            if isinstance(
                resultado_router,
                dict
            ):

                if resultado_router.get("tipo") == "error":

                    raise Exception(
                        resultado_router.get(
                            "respuesta",
                            "Error desconocido del Router."
                        )
                    )

                # Preferir primero una estructura real (list/dict/tuple).
                # Evita convertir innecesariamente los datos a texto.
                candidatos_resultado = (
                    resultado_router.get("resultado"),
                    resultado_router.get("respuesta"),
                    resultado_router.get("analisis"),
                    resultado_router.get("contenido"),
                )

                respuesta_bruta = None

                for candidato in candidatos_resultado:

                    if isinstance(
                        candidato,
                        (dict, list, tuple)
                    ):
                        respuesta_bruta = candidato
                        break

                # Si no existe una estructura real, usar el primer
                # valor textual disponible.
                if respuesta_bruta is None:

                    for candidato in candidatos_resultado:

                        if candidato not in (
                            None,
                            ""
                        ):
                            respuesta_bruta = candidato
                            break

                if respuesta_bruta is None:
                    respuesta_bruta = str(resultado_router)

            else:

                respuesta_bruta = str(
                    resultado_router
                )

            # El Chatbox ya no selecciona ni ejecuta agentes.
            # El responsable de esa decisión es el Router.
            procesado_por = "Router"

            add_event(
                "ROUTER_FINISH",
                {
                    "tipo_resultado":
                        type(
                            resultado_router
                        ).__name__
                }
            )

            print(
                "[ROUTER] Consulta procesada correctamente"
            )

        # ====================================================
        # SEGURIDAD POR RESPUESTA VACÍA
        # ====================================================

        if not respuesta_bruta:

            respuesta_bruta = (
                "El agente no generó respuesta."
            )


        # ==========================================================
        # ==========================================================
        # SÍNTESIS IA DE RESPUESTA
        #
        # El Router puede devolver:
        #   1) dict/list/tuple directamente
        #   2) una lista/dict serializada como texto
        #   3) texto normal
        #
        # Si una estructura llega como texto, se convierte de forma
        # segura con ast.literal_eval() para que también pueda pasar
        # por la síntesis ejecutiva.
        # ==========================================================

        resultado_estructurado = respuesta_bruta

        if isinstance(
            respuesta_bruta,
            str
        ):

            texto_resultado = respuesta_bruta.strip()

            parece_estructura = (
                (
                    texto_resultado.startswith("[")
                    and texto_resultado.endswith("]")
                )
                or
                (
                    texto_resultado.startswith("{")
                    and texto_resultado.endswith("}")
                )
            )

            if parece_estructura:

                try:

                    texto_parseable = texto_resultado

                    # Pandas imprime los resultados como:
                    # Timestamp('2026-08-19 10:22:51')
                    # y NaT.
                    #
                    # ast.literal_eval() no permite ejecutar Timestamp(...),
                    # por lo que primero convertimos esos valores a literales.
                    texto_parseable = re.sub(
                        r"Timestamp\((['\"])(.*?)\1\)",
                        lambda m: (
                            m.group(1)
                            + m.group(2)
                            + m.group(1)
                        ),
                        texto_parseable
                    )

                    texto_parseable = re.sub(
                        r"\bNaT\b",
                        "None",
                        texto_parseable
                    )

                    resultado_parseado = ast.literal_eval(
                        texto_parseable
                    )

                    if isinstance(
                        resultado_parseado,
                        (dict, list, tuple)
                    ):

                        resultado_estructurado = resultado_parseado

                        print(
                            "[DEBUG] Resultado textual convertido "
                            "a estructura Python para síntesis"
                        )

                        add_event(
                            "RESULT_NORMALIZED",
                            {
                                "origen": "texto",
                                "tipo_resultado": type(
                                    resultado_parseado
                                ).__name__,
                                "timestamp_normalizado": (
                                    "Timestamp/NaT"
                                    in texto_resultado
                                )
                            }
                        )

                except (
                    ValueError,
                    SyntaxError
                ) as normalizacion_error:

                    print(
                        "[DEBUG] No se pudo convertir resultado textual "
                        "a estructura:",
                        str(normalizacion_error)
                    )

                    add_event(
                        "RESULT_NORMALIZED",
                        {
                            "origen": "texto",
                            "convertido": False
                        }
                    )

        # ==========================================================
        # RESULTADO ESTRUCTURADO → RESUMEN EJECUTIVO
        # ==========================================================

        if isinstance(
            resultado_estructurado,
            (dict, list, tuple)
        ):

            try:

                print(
                    "[DEBUG] Generando síntesis ejecutiva "
                    "para resultado estructurado"
                )

                respuesta_final = generar_resumen_ejecutivo(
                    resultado_estructurado,
                    pregunta,
                    contexto_memoria
                )

                if not respuesta_final:

                    raise Exception(
                        "El generador de resumen no devolvió respuesta."
                    )

            except Exception as resumen_error:

                # La síntesis nunca debe botar una respuesta que ya
                # fue obtenida correctamente por el Router.
                print(
                    "[WARNING] Falló síntesis ejecutiva:",
                    str(resumen_error)
                )

                add_event(
                    "LLM_SUMMARY_ERROR",
                    {
                        "mensaje": str(resumen_error)
                    },
                    estado="ERROR"
                )

                # Fallback: nunca perder la respuesta original.
                respuesta_final = str(
                    respuesta_bruta
                )

        else:

            # ======================================================
            # RESULTADO YA ES TEXTO → NO LLAMAR AL LLM
            # ======================================================

            respuesta_final = str(
                respuesta_bruta
            )

            add_event(
                "LLM_SUMMARY_SKIPPED",
                {
                    "motivo":
                        "resultado ya es texto"
                }
            )

        # ====================================================
        # SEGURIDAD FINAL
        # ====================================================

        if not respuesta_final:

            respuesta_final = (
                "No se pudo generar una respuesta."
            )


        # ====================================================
        # TIEMPO TOTAL
        # ====================================================

        tiempo_total = round(
            time.time() - inicio,
            2
        )


        # ====================================================
        # EVENTO RESPONSE GENERATED
        # ====================================================

        add_event(
            "RESPONSE_GENERATED",
            {
                "tiempo_segundos":
                    tiempo_total,

                "memorias_usadas":
                    len(
                        memorias_relevantes
                    ),

                "respuesta_desde_memoria":
                    (
                        memoria_directa
                        is not None
                    )
            }
        )


        add_event(
            "CHAT_FINISHED"
        )


        print(
            get_events()
        )


        # ====================================================
        # META DE RESPUESTA
        # ====================================================

        respuesta_final_con_meta = (
            f"{respuesta_final}"
            f"\n\n*Procesado por "
            f"{procesado_por}"
            f" en {tiempo_total}s*"
        )


        # ====================================================
        # RESPUESTA JSON
        # ====================================================

        return jsonify({
            "response":
                respuesta_final_con_meta
        })


    except Exception as e:

        add_event(
            "ERROR",
            {
                "mensaje":
                    str(e)
            },
            estado="ERROR"
        )


        print(
            f"[ERROR] Falló flujo "
            f"chatbox.py: {str(e)}"
        )


        return jsonify({
            "response":
                "Ocurrió un error al "
                "procesar tu solicitud: "
                f"{str(e)}"
        }), 500