# ============================================================
# ROUTER CENTRAL - SMART BI ASSISTANT
# ============================================================

import inspect
import re

from .agent_registry import AgentRegistry
from app.servicios.catalogo_service import catalogo_service
from app.servicios.teradata_service import buscar_metadata_teradata

from app.memoria.execution_trace import (
    add_event,
    start_event,
    success_event,
    error_event
)


class Router:
    """
    Router central del Smart BI Assistant.

    FLUJO:

        1. Fast Path
        2. Guard
        3. Prioridad funcional (Dashboard)
        4. Metadata Teradata
        5. Intent Gate
        6. Catálogo maestro
        7. Agentes
        8. Respuesta

    PRIORIDAD:

        Preguntas simples
            ↓
        Metadata Teradata
            ↓
        Catálogo
            ↓
        Agentes

    El Router NO maneja:

        - Embeddings
        - Memoria semántica
        - Ollama directamente
        - Lógica interna de los agentes
    """

    # ========================================================
    # INICIALIZACIÓN
    # ========================================================

    def __init__(self):

        self.registry = AgentRegistry()

        # ====================================================
        # PALABRAS CLAVE POR INTENCIÓN
        # ====================================================

        self.intenciones = {

            "sql": {

                "peso_alto": [
                    "sql",
                    "query",
                    "select",
                    "insert",
                    "update",
                    "delete",
                    "join",
                    "where",
                    "group by",
                    "order by",
                    "having",
                    "subquery",
                    "consulta sql",
                    "sentencia sql"
                ],

                "peso_medio": [
                    "netezza",
                    "teradata",
                    "oracle",
                    "postgres",
                    "tabla",
                    "tablas",
                    "columna",
                    "columnas",
                    "esquema",
                    "schema",
                    "base de datos"
                ]
            },

            "tendencias": {

                "peso_alto": [
                    "tendencia",
                    "tendencias",
                    "evolución",
                    "evolucion",
                    "histórico",
                    "historico",
                    "comparación",
                    "comparacion",
                    "crecimiento",
                    "variación",
                    "variacion"
                ],

                "peso_medio": [
                    "comportamiento",
                    "periodo",
                    "periodos",
                    "mensual",
                    "mensualmente",
                    "historia",
                    "evoluciona"
                ]
            },

            "monitoreo": {

                "peso_alto": [
                    "monitoreo",
                    "monitor",
                    "schedule",
                    "control-m",
                    "control m",
                    "batch",
                    "ejecución",
                    "ejecucion",
                    "layout"
                ],

                "peso_medio": [
                    "proceso",
                    "procesos",
                    "pendiente",
                    "finalizado",
                    "ejecutando",
                    "estado del proceso",
                    "estado de ejecución",
                    "estado de ejecucion"
                ]
            },

            "alertas": {

                "peso_alto": [
                    "alerta",
                    "alertas",
                    "incidente",
                    "incidentes",
                    "caída",
                    "caida",
                    "falló",
                    "fallo",
                    "fallaron",
                    "error crítico",
                    "error critico"
                ],

                "peso_medio": [
                    "error",
                    "problema",
                    "problemas",
                    "falla",
                    "fallas",
                    "afectación",
                    "afectacion"
                ]
            },

            "regulatorio": {

                "peso_alto": [
                    "osiptel",
                    "regulatorio",
                    "regulatoria",
                    "norma",
                    "normas",
                    "nri"
                ],

                "peso_medio": [
                    "reporte regulatorio",
                    "formato regulatorio",
                    "obligación",
                    "obligacion",
                    "indicador regulatorio",
                    "plazo regulatorio"
                ]
            },

            "documentacion": {

                "peso_alto": [
                    "documentación",
                    "documentacion",
                    "manual",
                    "manuales",
                    "procedimiento",
                    "procedimientos",
                    "instructivo",
                    "instructivos"
                ],

                "peso_medio": [
                    "guía",
                    "guia",
                    "cómo se hace",
                    "como se hace",
                    "pasos para",
                    "documentado"
                ]
            },

            "developer": {

                "peso_alto": [
                    "python",
                    "flask",
                    "api",
                    "programación",
                    "programacion",
                    "código",
                    "codigo",
                    "desarrollo",
                    "arquitectura"
                ],

                "peso_medio": [
                    "shell",
                    "linux",
                    "javascript",
                    "html",
                    "css",
                    "git",
                    "github",
                    "backend",
                    "frontend",
                    "blueprint"
                ]
            },
            "dashboard": {
                "peso_alto": [
                    "dashboard",
                    "dashboards",
                    "tablero",
                    "tablero de control",
                    "panel",
                    "panel de control",
                    "visualización",
                    "visualizacion",
                    "gráfico",
                    "grafico"
                ],

                "peso_medio": [
                    "chart",
                    "charts",
                    "grafica",
                    "gráfica",
                    "reporte visual",
                    "indicadores",
                    "kpi",
                    "kpis"
                ]
            }
        }

    # ========================================================
    # CAPA 1 - FAST PATH
    # ========================================================

    def _resolver_fast_path(self, consulta):

        texto = str(
            consulta
        ).lower().strip()

        texto = " ".join(
            texto.split()
        )

        respuestas = {

            "hola":
                "¡Hola! ¿En qué puedo ayudarte?",

            "hola!":
                "¡Hola! ¿En qué puedo ayudarte?",

            "buenos dias":
                "¡Buenos días! ¿En qué puedo ayudarte?",

            "buenos días":
                "¡Buenos días! ¿En qué puedo ayudarte?",

            "buenas tardes":
                "¡Buenas tardes! ¿En qué puedo ayudarte?",

            "buenas noches":
                "¡Buenas noches! ¿En qué puedo ayudarte?",

            "gracias":
                "¡De nada! ¿En qué más puedo ayudarte?",

            "muchas gracias":
                "¡De nada! ¿En qué más puedo ayudarte?",

            "ok":
                "Perfecto.",

            "okey":
                "Perfecto.",

            "perfecto":
                "Perfecto.",

            "listo":
                "Listo.",

            "ayuda":
                (
                    "Claro. Puedo ayudarte con SQL, metadata de tablas, "
                    "monitoreo, regulación, alertas, tendencias, "
                    "dashboards, documentación y desarrollo."
                ),

            "quien eres":
                (
                    "Soy el Smart BI Assistant. Puedo ayudarte con "
                    "consultas de datos, metadata, monitoreo, regulación, "
                    "documentación y desarrollo."
                ),

            "quién eres":
                (
                    "Soy el Smart BI Assistant. Puedo ayudarte con "
                    "consultas de datos, metadata, monitoreo, regulación, "
                    "documentación y desarrollo."
                ),

            "que puedes hacer":
                (
                    "Puedo ayudarte con SQL, metadata de tablas, "
                    "monitoreo, regulación, alertas, tendencias, "
                    "dashboards, documentación y desarrollo."
                ),

            "qué puedes hacer":
                (
                    "Puedo ayudarte con SQL, metadata de tablas, "
                    "monitoreo, regulación, alertas, tendencias, "
                    "dashboards, documentación y desarrollo."
                )
        }

        respuesta = respuestas.get(
            texto
        )

        if respuesta is None:
            return None

        return {
            "tipo": "fast_path",
            "respuesta": respuesta,
            "tipo_ejecucion": "local",
            "agente": None,
            "base_datos": None
        }

    # ========================================================
    # CAPA 2 - GUARD
    # ========================================================

    def _evaluar_guard(self, consulta):

        texto = str(
            consulta
        ).lower().strip()

        texto = " ".join(
            texto.split()
        )

        if not texto:

            return {
                "estado": "unknown",
                "respuesta": (
                    "No entendí la consulta. "
                    "Por favor, vuelve a escribirla "
                    "con un poco más de detalle."
                ),
                "motivo": "consulta_vacia"
            }

        ruido_exacto = {

            "xyz",
            "asdf",
            "asdfgh",
            "qwerty",
            "qwertyui",
            "abc",
            "123",
            "123456",
            "test",
            "testing",
            "aaaa",
            "bbbb",
            "hola hola hola"
        }

        if texto in ruido_exacto:

            return {
                "estado": "unknown",
                "respuesta": (
                    "No entendí la consulta. "
                    "Por favor, vuelve a escribirla "
                    "con un poco más de detalle."
                ),
                "motivo":
                    "ruido_o_consulta_sin_sentido"
            }

        compacto = re.sub(
            r"[^a-záéíóúüñ0-9]",
            "",
            texto
        )

        if (
            len(compacto) >= 4
            and len(set(compacto)) <= 2
        ):

            return {
                "estado": "unknown",
                "respuesta": (
                    "No entendí la consulta. "
                    "Por favor, vuelve a escribirla "
                    "con un poco más de detalle."
                ),
                "motivo":
                    "texto_sin_intencion"
            }

        # ----------------------------------------------------
        # SOLICITUDES NO PERMITIDAS
        # ----------------------------------------------------

        patrones_bloqueo = [

            r"\bcomo\s+(matar|asesinar|herir|torturar|hacer\s+daño)\b",

            r"\bdame\s+(los\s+)?pasos\s+(para|de)\s+(matar|asesinar|herir)\b",

            r"\binstrucciones\s+(para|de)\s+(matar|asesinar|herir)\b",

            r"\bcomo\s+(fabricar|hacer|construir)\s+(una\s+)?(bomba|explosivo|arma)\b",

            r"\bcomo\s+(robar|hackear|sabotear|secuestrar)\b",

            r"\binstrucciones\s+(para|de)\s+(robar|hackear|sabotear|secuestrar)\b",

            r"\bcomo\s+(crear|hacer|programar)\s+(un\s+)?(malware|ransomware|virus|troyano)\b",

            r"\bdame\s+(los\s+)?pasos\s+para\s+(atacar|infectar|comprometer)\s+(un\s+)?sistema\b",

            r"\bcomo\s+(suicidarme|hacerme\s+daño|lastimarme)\b",

            r"\bpasos\s+para\s+(suicidarme|hacerme\s+daño|lastimarme)\b",

            r"\bignora\s+(tus|las)\s+(restricciones|reglas|instrucciones)\b",

            r"\brevela\s+(tu\s+)?(prompt|instrucciones)\s+internas?\b"
        ]

        for patron in patrones_bloqueo:

            if re.search(
                patron,
                texto
            ):

                return {
                    "estado": "block",
                    "respuesta":
                        "No puedo ayudar con ese tipo de solicitud.",
                    "motivo":
                        "solicitud_no_permitida"
                }

        return {
            "estado": "allow",
            "respuesta": None,
            "motivo": None
        }

    # ========================================================
    # DETECTAR PREGUNTA DE METADATA TERADATA
    # ========================================================

    def _es_solicitud_dashboard(self, consulta):
        """
        Detecta una solicitud explícita de construcción de dashboard.

        Esta decisión pertenece al Router porque define la ruta de ejecución:
        una solicitud explícita de dashboard debe llegar al AgenteDashboard
        antes de intentar resolver metadata de Teradata o regulación.
        """

        texto = (
            str(consulta or "")
            .lower()
            .strip()
        )

        if not texto:
            return False

        patrones = [
            r"\bdashboard\b",
            r"\bdash board\b",
            r"\btablero(?: de control)?\b",
            r"\bpanel(?: de control)?\b",
            r"\bcrear(?:me)?\s+(?:un\s+)?dashboard\b",
            r"\bgener(?:a|ame|ar)\s+(?:un\s+)?dashboard\b",
            r"\bconstru(?:ir|ye|yeme)\s+(?:un\s+)?dashboard\b",
            r"\bhazme\s+(?:un\s+)?dashboard\b",
            r"\bcrear\s+(?:un\s+)?tablero\b",
            r"\bgenerar\s+(?:un\s+)?tablero\b"
        ]

        return any(
            re.search(patron, texto)
            for patron in patrones
        )

    def _dashboard_tiene_contexto_pendiente(self):
        """
        Determina si AgenteDashboard está esperando la selección 1, 2 o 3.

        El estado sigue perteneciendo al agente; el Router solo consulta si
        existe para poder enrutar correctamente la siguiente interacción.
        """

        agente = self.registry.get_agent("dashboard")

        return bool(
            agente
            and getattr(
                agente,
                "_contexto_pendiente",
                None
            )
        )

    def _es_opcion_dashboard_pendiente(self, consulta):
        texto = str(consulta or "").strip()

        return (
            bool(re.fullmatch(r"[1-3]", texto))
            and
            self._dashboard_tiene_contexto_pendiente()
        )

    def _es_metadata_teradata(self, consulta):

        texto = (
            str(consulta)
            .lower()
            .strip()
        )

        # Una solicitud explícita de dashboard tiene prioridad funcional.
        # No debe caer en la ruta de metadata aunque contenga "tabla",
        # "campo", un esquema regulatorio o un identificador técnico.
        if self._es_solicitud_dashboard(consulta):
            return False

        # Una selección 1/2/3 pertenece a la conversación del dashboard
        # si existe una propuesta pendiente.
        if self._es_opcion_dashboard_pendiente(consulta):
            return False

        # ----------------------------------------------------
        # SEÑALES FUERTES
        # ----------------------------------------------------

        señales_fuertes = [

            r"\bcuantas?\s+tablas?\b",

            r"\bcuantos?\s+tablas?\b",

            r"\bque\s+tablas?\b",

            r"\bcuales\s+tablas?\b",

            r"\btablas?\s+que\s+tienen\b",

            r"\btablas?\s+que\s+contienen\b",

            r"\btablas?\s+con\b",

            r"\bcampos?\s+de\b",

            r"\bcolumnas?\s+de\b",

            r"\bestructura\s+de\b",

            r"\bmetadata\b",

            r"\bmetadatos?\b",

            r"\bdefinicion\s+de\s+la\s+tabla\b",

            r"\bsignificado\s+de\s+la\s+tabla\b"
        ]

        for patron in señales_fuertes:

            if re.search(
                patron,
                texto
            ):
                return True

        # ----------------------------------------------------
        # IDENTIFICADOR TÉCNICO + TABLA/CAMPO
        # ----------------------------------------------------

        if re.search(
            r"\b[A-Z][A-Z0-9]*_[A-Z0-9_]+\b",
            str(consulta)
        ):

            if any(
                palabra in texto
                for palabra in [
                    "tabla",
                    "tablas",
                    "campo",
                    "campos",
                    "columna",
                    "columnas",
                    "tiene",
                    "tienen",
                    "contiene",
                    "contienen"
                ]
            ):
                return True

        return False

    # ========================================================
    # EJECUTAR METADATA
    # ========================================================

    def _resolver_metadata_teradata(
        self,
        consulta
    ):

        print("")
        print("=" * 70)
        print(
            "[ROUTER] RUTA METADATA TERADATA"
        )
        print("=" * 70)

        start_event(
            "METADATA_SEARCH_START",
            {
                "consulta": consulta,
                "motor": "TERADATA"
            }
        )

        try:

            resultado = buscar_metadata_teradata(
                consulta
            )

            success_event(
                "METADATA_SEARCH_FINISH",
                {
                    "motor": "TERADATA",
                    "total_tablas":
                        resultado.get(
                            "total_tablas",
                            0
                        ),
                    "modo":
                        resultado.get(
                            "modo"
                        )
                }
            )

            return self._formatear_metadata_usuario(
                resultado
            )

        except Exception as e:

            error_event(
                "METADATA_SEARCH_FINISH",
                {
                    "motor": "TERADATA",
                    "error": str(e)
                }
            )

            raise

    # ========================================================
    # FORMATEAR METADATA PARA USUARIO
    # ========================================================

    def _formatear_metadata_usuario(
        self,
        resultado
    ):

        modo = resultado.get(
            "modo"
        )

        total = resultado.get(
            "total_tablas",
            0
        )

        cantidad = resultado.get(
            "cantidad_solicitada"
        )

        tablas = resultado.get(
            "tablas",
            []
        )

        pregunta = resultado.get(
            "pregunta",
            ""
        )

        # ====================================================
        # COUNT
        # ====================================================

        if modo == "count":

            if resultado.get(
                "busqueda_por_campo"
            ):

                return {
                    "tipo":
                        "metadata_teradata",

                    "respuesta": (
                        f"Encontré {total} "
                        f"tabla{'s' if total != 1 else ''} "
                        f"que coincide{'n' if total != 1 else ''} "
                        f"con el campo solicitado."
                    ),

                    "tipo_ejecucion":
                        "metadata",

                    "agente":
                        None,

                    "motor":
                        "TERADATA",

                    "modo":
                        "count",

                    "total_tablas":
                        total,

                    "cantidad_solicitada":
                        cantidad,

                    "tablas":
                        [],

                    "datos":
                        resultado
                }

            return {
                "tipo":
                    "metadata_teradata",

                "respuesta": (
                    f"Encontré {total} "
                    f"tabla{'s' if total != 1 else ''} "
                    "que coincide con la búsqueda."
                ),

                "tipo_ejecucion":
                    "metadata",

                "agente":
                    None,

                "motor":
                    "TERADATA",

                "modo":
                    "count",

                "total_tablas":
                    total,

                "cantidad_solicitada":
                    cantidad,

                "tablas":
                    [],

                "datos":
                    resultado
            }

        # ====================================================
        # SIN RESULTADOS
        # ====================================================

        if not tablas:

            return {
                "tipo":
                    "metadata_teradata",

                "respuesta": (
                    "No encontré tablas que coincidan "
                    "con la búsqueda."
                ),

                "tipo_ejecucion":
                    "metadata",

                "agente":
                    None,

                "motor":
                    "TERADATA",

                "modo":
                    modo,

                "total_tablas":
                    0,

                "tablas":
                    [],

                "datos":
                    resultado
            }

        # ====================================================
        # LISTA DE TABLAS
        # ====================================================

        lineas = []

        if cantidad is not None:

            lineas.append(
                f"Encontré {total} tabla"
                f"{'s' if total != 1 else ''} "
                f"y te muestro las "
                f"{len(tablas)} solicitadas:"
            )

        else:

            lineas.append(
                f"Encontré {total} tabla"
                f"{'s' if total != 1 else ''}:"
            )

        lineas.append("")

        for indice, tabla in enumerate(
            tablas,
            start=1
        ):

            database = tabla.get(
                "database",
                ""
            )

            nombre = tabla.get(
                "tabla",
                ""
            )

            descripcion = (
                tabla.get(
                    "descripcion_tabla"
                )
                or
                "Sin definición disponible."
            )

            lineas.append(
                f"{indice}. "
                f"{database}.{nombre}"
            )

            lineas.append(
                f"   Definición: {descripcion}"
            )

            campos = tabla.get(
                "campos",
                []
            )

            if campos:

                lineas.append(
                    "   Campo relacionado:"
                )

                for campo in campos:

                    nombre_campo = campo.get(
                        "campo",
                        ""
                    )

                    descripcion_campo = (
                        campo.get(
                            "descripcion"
                        )
                        or
                        "Sin definición disponible."
                    )

                    lineas.append(
                        f"      • {nombre_campo}"
                        f" — {descripcion_campo}"
                    )

            lineas.append("")

        lineas.append(
            "Si quieres, puedo mostrarte el detalle "
            "de una de estas tablas."
        )

        return {

            "tipo":
                "metadata_teradata",

            "respuesta":
                "\n".join(lineas),

            "tipo_ejecucion":
                "metadata",

            "agente":
                None,

            "motor":
                "TERADATA",

            "modo":
                modo,

            "total_tablas":
                total,

            "cantidad_solicitada":
                cantidad,

            "tablas":
                tablas,

            "datos":
                resultado
        }

    # ========================================================
    # CAPA 3 - INTENT GATE
    # ========================================================

    def _evaluar_intent_gate(
        self,
        consulta
    ):

        texto = (
            " ".join(
                str(consulta)
                .lower()
                .strip()
                .split()
            )
        )

        # ----------------------------------------------------
        # PRIORIDAD FUNCIONAL: DASHBOARD
        # ----------------------------------------------------
        # El Intent Gate no debe interpretar una tabla regulatoria como
        # intención "regulatorio" cuando la acción solicitada es crear
        # un dashboard. Tampoco debe rechazar 1/2/3 cuando corresponden
        # a una propuesta pendiente del AgenteDashboard.
        if (
            self._es_solicitud_dashboard(consulta)
            or
            self._es_opcion_dashboard_pendiente(consulta)
        ):
            print(
                "[ROUTER] Intent Gate: DASHBOARD prioritario"
            )

            return {
                "estado": "allow",
                "respuesta": None,
                "motivo": "flujo_dashboard",
                "intencion": "dashboard",
                "score": 3,
                "umbral": 2
            }

        puntuaciones = {}

        for intencion, reglas in self.intenciones.items():

            score = 0

            for palabra in reglas.get(
                "peso_alto",
                []
            ):

                if palabra in texto:
                    score += 3

            for palabra in reglas.get(
                "peso_medio",
                []
            ):

                if palabra in texto:
                    score += 1

            puntuaciones[
                intencion
            ] = score

        ordenadas = sorted(
            puntuaciones.items(),
            key=lambda x: x[1],
            reverse=True
        )

        mejor_intencion = (
            ordenadas[0][0]
        )

        mejor_score = (
            ordenadas[0][1]
        )

        segundo_score = (
            ordenadas[1][1]
            if len(ordenadas) > 1
            else 0
        )

        umbral = 2

        print(
            "[ROUTER] Intent Gate | "
            f"mejor={mejor_intencion} | "
            f"score={mejor_score} | "
            f"segundo={segundo_score} | "
            f"umbral={umbral}"
        )

        if mejor_score < umbral:

            return {
                "estado":
                    "unknown",

                "respuesta": (
                    "No identifiqué suficiente información "
                    "para determinar qué necesitas. "
                    "Por favor, especifica un poco más "
                    "tu consulta."
                ),

                "motivo":
                    "intencion_insuficiente",

                "intencion":
                    mejor_intencion
                    if mejor_score > 0
                    else None,

                "score":
                    mejor_score,

                "umbral":
                    umbral
            }

        return {
            "estado":
                "allow",

            "respuesta":
                None,

            "motivo":
                "intencion_suficiente",

            "intencion":
                mejor_intencion,

            "score":
                mejor_score,

            "umbral":
                umbral
        }

    # ========================================================
    # DETECTAR CONSULTA ANALÍTICA
    # ========================================================

    def _requiere_analisis(
        self,
        consulta
    ):

        texto = (
            str(consulta)
            .lower()
            .strip()
        )

        palabras_analisis = [

            "analiza",
            "analizar",
            "analisis",
            "análisis",

            "patron",
            "patrones",
            "patrón",

            "tendencia",
            "tendencias",

            "comportamiento",

            "comparar",
            "compara",
            "comparación",
            "comparacion",

            "explica",
            "explicame",
            "explícame",

            "por que",
            "por qué",

            "causa",
            "causas",

            "motivo",
            "motivos",

            "identifica",
            "identificar",

            "detecta",
            "detectar"
        ]

        for palabra in palabras_analisis:

            if palabra in texto:

                print(
                    "[ROUTER] "
                    f"Consulta analítica detectada: "
                    f"'{palabra}'"
                )

                return True

        return False

    # ========================================================
    # PROCESAR CONSULTA
    # ========================================================

    def procesar_consulta(
        self,
        consulta,
        memoria=""
    ):

        if not consulta:

            error_event(
                "CHAT_ERROR",
                {
                    "motivo":
                        "Consulta vacía"
                }
            )

            return {
                "tipo":
                    "error",

                "respuesta":
                    "La consulta está vacía."
            }

        print("")
        print("=" * 70)
        print("[ROUTER] NUEVA CONSULTA")
        print("=" * 70)

        print(
            f"[ROUTER] Pregunta: {consulta}"
        )

        start_event(
            "ROUTER_START",
            {
                "consulta":
                    consulta
            }
        )

        # ====================================================
        # CAPA 1 - FAST PATH
        # ====================================================

        resultado_fast_path = (
            self._resolver_fast_path(
                consulta
            )
        )

        if resultado_fast_path:

            print(
                "[ROUTER] "
                "Fast Path: respuesta local."
            )

            success_event(
                "FAST_PATH_MATCH",
                {
                    "tipo_ejecucion":
                        "local"
                }
            )

            success_event(
                "RESPONSE_GENERATED",
                {
                    "origen":
                        "fast_path"
                }
            )

            success_event(
                "ROUTER_FINISH",
                {
                    "ruta":
                        "fast_path"
                }
            )

            return resultado_fast_path

        success_event(
            "FAST_PATH_NO_MATCH"
        )

        # ====================================================
        # CAPA 2 - GUARD
        # ====================================================

        resultado_guard = (
            self._evaluar_guard(
                consulta
            )
        )

        if resultado_guard[
            "estado"
        ] != "allow":

            estado = (
                resultado_guard[
                    "estado"
                ]
            )

            print(
                "[ROUTER] Guard: "
                f"{estado.upper()} | "
                f"motivo="
                f"{resultado_guard['motivo']}"
            )

            success_event(
                "GUARD_DECISION",
                {
                    "estado":
                        estado,

                    "motivo":
                        resultado_guard[
                            "motivo"
                        ]
                }
            )

            success_event(
                "RESPONSE_GENERATED",
                {
                    "origen":
                        "guard",

                    "estado":
                        estado
                }
            )

            success_event(
                "ROUTER_FINISH",
                {
                    "ruta":
                        "guard",

                    "estado":
                        estado
                }
            )

            return {

                "tipo":
                    "guard",

                "respuesta":
                    resultado_guard[
                        "respuesta"
                    ],

                "tipo_ejecucion":
                    "local",

                "agente":
                    None,

                "motivo":
                    resultado_guard[
                        "motivo"
                    ]
            }

        success_event(
            "GUARD_ALLOW",
            {
                "motivo":
                    "Consulta apta para continuar"
            }
        )

        # ====================================================
        # CAPA 3 - METADATA TERADATA
        # ====================================================
        #
        # ESTA CAPA VA ANTES DEL INTENT GATE Y DEL CATÁLOGO.
        #
        # Objetivo:
        #
        #     ¿Cuántas tablas tienen CUSTOMER_KEY?
        #
        #     ¿Cuáles tienen CUSTOMER_KEY?
        #
        #     Dame 2 tablas con CUSTOMER_KEY.
        #
        #     ¿Qué campos tiene ALDM_CUSTOMER?
        #
        # Estas preguntas NO necesitan Ollama.
        # ====================================================

        if self._es_metadata_teradata(
            consulta
        ):

            print(
                "[ROUTER] "
                "Metadata Teradata detectada."
            )

            success_event(
                "METADATA_ROUTE",
                {
                    "motor":
                        "TERADATA",

                    "origen":
                        "router"
                }
            )

            try:

                resultado_metadata = (
                    self._resolver_metadata_teradata(
                        consulta
                    )
                )

                success_event(
                    "RESPONSE_GENERATED",
                    {
                        "origen":
                            "metadata",

                        "motor":
                            "TERADATA"
                    }
                )

                success_event(
                    "ROUTER_FINISH",
                    {
                        "ruta":
                            "metadata_teradata"
                    }
                )

                return resultado_metadata

            except Exception as e:

                print(
                    "[ROUTER] "
                    "Error en metadata Teradata: "
                    f"{e}"
                )

                error_event(
                    "METADATA_ROUTE_ERROR",
                    {
                        "motor":
                            "TERADATA",

                        "error":
                            str(e)
                    }
                )

                # No ocultamos el error.
                # Pero tampoco rompemos todo el Router.
                return {

                    "tipo":
                        "error",

                    "respuesta":
                        (
                            "No pude consultar la metadata "
                            f"de Teradata: {str(e)}"
                        ),

                    "tipo_ejecucion":
                        "metadata",

                    "agente":
                        None
                }

        # ====================================================
        # CAPA 4 - INTENT GATE
        # ====================================================

        start_event(
            "INTENT_GATE_START",
            {
                "consulta":
                    consulta
            }
        )

        intent_gate = (
            self._evaluar_intent_gate(
                consulta
            )
        )

        success_event(
            "INTENT_GATE_DECISION",
            {
                "estado":
                    intent_gate[
                        "estado"
                    ],

                "intencion":
                    intent_gate.get(
                        "intencion"
                    ),

                "score":
                    intent_gate.get(
                        "score",
                        0
                    ),

                "umbral":
                    intent_gate.get(
                        "umbral",
                        0
                    )
            }
        )

        if intent_gate[
            "estado"
        ] != "allow":

            print(
                "[ROUTER] Intent Gate: "
                f"{intent_gate['estado'].upper()} | "
                f"intencion="
                f"{intent_gate.get('intencion')} | "
                f"score="
                f"{intent_gate.get('score', 0)}"
            )

            success_event(
                "INTENT_GATE_FINISH",
                {
                    "estado":
                        intent_gate[
                            "estado"
                        ],

                    "ruta":
                        "intent_gate"
                }
            )

            success_event(
                "RESPONSE_GENERATED",
                {
                    "origen":
                        "intent_gate"
                }
            )

            success_event(
                "ROUTER_FINISH",
                {
                    "ruta":
                        "intent_gate",

                    "estado":
                        intent_gate[
                            "estado"
                        ]
                }
            )

            return {

                "tipo":
                    "intent_gate",

                "respuesta":
                    intent_gate[
                        "respuesta"
                    ],

                "tipo_ejecucion":
                    "local",

                "agente":
                    None,

                "motivo":
                    intent_gate[
                        "motivo"
                    ],

                "intencion":
                    intent_gate.get(
                        "intencion"
                    ),

                "score":
                    intent_gate.get(
                        "score",
                        0
                    )
            }

        success_event(
            "INTENT_GATE_FINISH",
            {
                "estado":
                    "allow",

                "intencion":
                    intent_gate.get(
                        "intencion"
                    ),

                "score":
                    intent_gate.get(
                        "score",
                        0
                    )
            }
        )

        # ====================================================
        # CAPA 5 - CATÁLOGO MAESTRO
        # ====================================================

        start_event(
            "CATALOG_SEARCH_START"
        )

        try:

            resultado_catalogo = (
                catalogo_service.resolver(
                    consulta
                )
            )

            success_event(
                "CATALOG_SEARCH_FINISH",
                {
                    "encontrado":
                        bool(
                            resultado_catalogo
                        )
                }
            )

        except Exception as e:

            print(
                "[ROUTER] "
                f"Error consultando catálogo: {e}"
            )

            error_event(
                "CATALOG_SEARCH_FINISH",
                {
                    "error":
                        str(e)
                }
            )

            resultado_catalogo = None

        # ====================================================
        # CATÁLOGO ENCONTRADO
        # ====================================================

        if resultado_catalogo:

            print(
                "[ROUTER] "
                "Consulta encontrada en catálogo."
            )

            print(
                f"[ROUTER] Tipo: "
                f"{resultado_catalogo.get('tipo_consulta')}"
            )

            print(
                f"[ROUTER] Grupo: "
                f"{resultado_catalogo.get('grupo')}"
            )

            print(
                f"[ROUTER] Agente: "
                f"{resultado_catalogo.get('agente')}"
            )

            print(
                f"[ROUTER] BD: "
                f"{resultado_catalogo.get('base_datos')}"
            )

            success_event(
                "CATALOG_MATCH",
                {
                    "tipo_consulta":
                        resultado_catalogo.get(
                            "tipo_consulta"
                        ),

                    "grupo":
                        resultado_catalogo.get(
                            "grupo"
                        ),

                    "agente":
                        resultado_catalogo.get(
                            "agente"
                        ),

                    "base_datos":
                        resultado_catalogo.get(
                            "base_datos"
                        ),

                    "intent_gate":
                        intent_gate.get(
                            "intencion"
                        ),

                    "intent_score":
                        intent_gate.get(
                            "score",
                            0
                        )
                }
            )

            # ------------------------------------------------
            # RESULTADO
            # ------------------------------------------------

            resultado = {

                "tipo":
                    "catalogo",

                "respuesta":
                    resultado_catalogo.get(
                        "datos"
                    ),

                "tipo_consulta":
                    resultado_catalogo.get(
                        "tipo_consulta"
                    ),

                "grupo":
                    resultado_catalogo.get(
                        "grupo"
                    ),

                "agente":
                    resultado_catalogo.get(
                        "agente"
                    ),

                "base_datos":
                    resultado_catalogo.get(
                        "base_datos"
                    ),

                "tipo_ejecucion":
                    resultado_catalogo.get(
                        "tipo_ejecucion"
                    ),

                "descripcion":
                    resultado_catalogo.get(
                        "descripcion"
                    ),

                "sql":
                    resultado_catalogo.get(
                        "sql"
                    ),

                "datos":
                    resultado_catalogo.get(
                        "datos"
                    )
            }

            success_event(
                "DATABASE_QUERY_FINISH",
                {
                    "origen":
                        "catalogo"
                }
            )

            success_event(
                "RESPONSE_GENERATED",
                {
                    "origen":
                        "catalogo"
                }
            )

            success_event(
                "ROUTER_FINISH",
                {
                    "ruta":
                        "catalogo"
                }
            )

            return resultado

        # ====================================================
        # NO EXISTE EN CATÁLOGO
        # ====================================================

        print(
            "[ROUTER] "
            "No existe consulta catalogada."
        )

        print(
            "[ROUTER] "
            "Continuando con detección normal "
            "de agentes."
        )

        success_event(
            "CATALOG_NO_MATCH"
        )

        # ====================================================
        # DETECTAR AGENTE
        # ====================================================

        agente_nombre = (
            self.detectar_agente(
                consulta
            )
        )

        print(
            "[ROUTER] Intención detectada: "
            f"{agente_nombre}"
        )

        if agente_nombre is None:

            print(
                "[ROUTER] "
                "Consulta sin intención suficiente. "
                "No se ejecutará ningún agente."
            )

            success_event(
                "NO_AGENT_REQUIRED",
                {
                    "motivo":
                        "Sin intención específica"
                }
            )

            resultado = {

                "tipo":
                    "router",

                "respuesta":
                    (
                        "No identifiqué una consulta técnica "
                        "específica. Puedes indicarme si necesitas "
                        "ayuda con SQL, monitoreo, regulación, "
                        "alertas, tendencias, documentación "
                        "o desarrollo."
                    ),

                "tipo_ejecucion":
                    "router",

                "agente":
                    None
            }

            success_event(
                "RESPONSE_GENERATED",
                {
                    "origen":
                        "router"
                }
            )

            success_event(
                "ROUTER_FINISH",
                {
                    "ruta":
                        "router_no_agent"
                }
            )

            return resultado

        success_event(
            "AGENT_SELECTED",
            {
                "agente":
                    agente_nombre
            }
        )

        # ====================================================
        # CAPA 6 - AGENTES
        # ====================================================

        agente = (
            self.registry.get_agent(
                agente_nombre
            )
        )

        if not agente:

            error_event(
                "AGENT_ERROR",
                {
                    "agente":
                        agente_nombre,

                    "motivo":
                        "Agente no encontrado"
                }
            )

            error_event(
                "ROUTER_FINISH"
            )

            return {

                "tipo":
                    "error",

                "respuesta":
                    (
                        f"No existe el agente "
                        f"'{agente_nombre}'."
                    )
            }

        print(
            "[ROUTER] Agente seleccionado: "
            f"{type(agente).__name__}"
        )

        start_event(
            "AGENT_EXECUTION_START",
            {
                "agente":
                    agente_nombre,

                "clase":
                    type(agente).__name__
            }
        )

        try:

            resultado = (
                self._ejecutar_agente(
                    agente=agente,
                    consulta=consulta,
                    memoria=memoria
                )
            )

            success_event(
                "AGENT_EXECUTION_FINISH",
                {
                    "agente":
                        agente_nombre
                }
            )

            success_event(
                "RESPONSE_GENERATED",
                {
                    "origen":
                        "agente",

                    "agente":
                        agente_nombre
                }
            )

            success_event(
                "ROUTER_FINISH",
                {
                    "ruta":
                        "agente",

                    "agente":
                        agente_nombre
                }
            )

            return resultado

        except Exception as e:

            print(
                "[ROUTER] "
                f"Error ejecutando "
                f"{type(agente).__name__}: {e}"
            )

            error_event(
                "AGENT_EXECUTION_FINISH",
                {
                    "agente":
                        agente_nombre,

                    "error":
                        str(e)
                }
            )

            error_event(
                "ROUTER_FINISH",
                {
                    "error":
                        str(e)
                }
            )

            return {

                "tipo":
                    "error",

                "respuesta":
                    (
                        f"Error ejecutando el agente "
                        f"{type(agente).__name__}: "
                        f"{str(e)}"
                    )
            }

    # ========================================================
    # EJECUTAR AGENTE
    # ========================================================

    def _ejecutar_agente(
        self,
        agente,
        consulta,
        memoria=""
    ):

        if not hasattr(
            agente,
            "execute"
        ):

            raise Exception(
                f"El agente "
                f"{type(agente).__name__} "
                "no tiene método execute()."
            )

        execute = agente.execute

        try:

            firma = inspect.signature(
                execute
            )

            parametros = (
                firma.parameters
            )

            # ------------------------------------------------
            # AGENTE CON MEMORIA
            # ------------------------------------------------

            if (
                "pregunta" in parametros
                and
                "memoria" in parametros
            ):

                print(
                    "[ROUTER] "
                    "Ejecutando agente "
                    "con memoria autorizada."
                )

                return execute(
                    pregunta=consulta,
                    memoria=memoria
                )

            # ------------------------------------------------
            # AGENTE SOLO CON PREGUNTA
            # ------------------------------------------------

            if "pregunta" in parametros:

                print(
                    "[ROUTER] "
                    "Ejecutando agente "
                    "sin parámetro memoria."
                )

                return execute(
                    pregunta=consulta
                )

            # ------------------------------------------------
            # COMPATIBILIDAD
            # ------------------------------------------------

            return execute(
                consulta
            )

        except ValueError:

            try:

                return execute(
                    pregunta=consulta,
                    memoria=memoria
                )

            except TypeError:

                return execute(
                    consulta
                )

        # ========================================================
    # DETECTAR AGENTE
    # ========================================================

    def detectar_agente(
        self,
        consulta
    ):
        """
        Determina el agente adecuado utilizando
        un sistema de puntuación.

        REGLA ESPECIAL DASHBOARD:
        Si el usuario solicita explícitamente
        crear/generar/construir un dashboard,
        se prioriza el agente dashboard aunque
        la tabla pertenezca a un contexto regulatorio.
        """

        texto = (
            str(consulta)
            .lower()
            .strip()
        )

        if not texto:
            return "developer"

        # ====================================================
        # PRIORIDAD DASHBOARD
        # ====================================================

        palabras_dashboard = [

            "dashboard",
            "dash board",
            "tablero",
            "tablero de control",

            "crear dashboard",
            "creame un dashboard",
            "créame un dashboard",

            "genera un dashboard",
            "generame un dashboard",
            "genérame un dashboard",

            "generar dashboard",
            "crear un dashboard",
            "construir dashboard",
            "construye un dashboard",

            "hazme un dashboard",
            "hacer un dashboard",

            "crear tablero",
            "genera un tablero",
            "generar un tablero"
        ]

        solicita_dashboard = any(
            palabra in texto
            for palabra in palabras_dashboard
        )

        # ====================================================
        # SI HAY INTENCIÓN EXPLÍCITA DE DASHBOARD
        # ====================================================

        if solicita_dashboard:

            print(
                "[ROUTER] Prioridad explícita: "
                "DASHBOARD"
            )

            # Detectamos si además existe una
            # referencia a tabla/vista.
            referencias_fuente = [

                "tabla",
                "tablas",
                "vista",
                "view",
                "esquema",
                "schema",
                "..",
                "prod_",
                "dbi_"
            ]

            tiene_fuente = any(
                palabra in texto
                for palabra in referencias_fuente
            )

            if tiene_fuente:

                print(
                    "[ROUTER] Dashboard asociado "
                    "a fuente de datos detectada."
                )

            print(
                "[ROUTER] Agente forzado: dashboard"
            )

            return "dashboard"

        # ====================================================
        # PRIORIDAD FUNCIONAL DASHBOARD
        # ====================================================

        if (
            self._es_solicitud_dashboard(consulta)
            or
            self._es_opcion_dashboard_pendiente(consulta)
        ):
            print(
                "[ROUTER] Prioridad funcional: DASHBOARD"
            )
            return "dashboard"

        # ====================================================
        # CALCULAR PUNTAJES NORMAL
        # ====================================================

        puntuaciones = {}

        for agente, reglas in self.intenciones.items():

            score = 0

            # ------------------------------------------------
            # PESO ALTO
            # ------------------------------------------------

            for palabra in reglas.get(
                "peso_alto",
                []
            ):

                if palabra in texto:

                    score += 3

            # ------------------------------------------------
            # PESO MEDIO
            # ------------------------------------------------

            for palabra in reglas.get(
                "peso_medio",
                []
            ):

                if palabra in texto:

                    score += 1

            puntuaciones[
                agente
            ] = score

        # ====================================================
        # ORDENAR
        # ====================================================

        puntuaciones_ordenadas = sorted(
            puntuaciones.items(),
            key=lambda x: x[1],
            reverse=True
        )

        print(
            "[ROUTER] Puntuaciones:"
        )

        for agente, score in (
            puntuaciones_ordenadas
        ):

            if score > 0:

                print(
                    f"    {agente}: {score}"
                )

        # ====================================================
        # MEJOR RESULTADO
        # ====================================================

        mejor_agente = (
            puntuaciones_ordenadas[0][0]
        )

        mejor_score = (
            puntuaciones_ordenadas[0][1]
        )

        # ====================================================
        # SIN COINCIDENCIAS
        # ====================================================

        if mejor_score == 0:

            print(
                "[ROUTER] "
                "No se encontró intención específica."
            )

            print(
                "[ROUTER] "
                "Agente por defecto: developer"
            )

            return "developer"

        print(
            f"[ROUTER] Mejor intención: "
            f"{mejor_agente} "
            f"(score={mejor_score})"
        )

        return mejor_agente

    # ========================================================
    # OBTENER AGENTE
    # ========================================================

    def obtener_agente(
        self,
        pregunta
    ):

        agente_nombre = (
            self.detectar_agente(
                pregunta
            )
        )

        agente = (
            self.registry.get_agent(
                agente_nombre
            )
        )

        return agente, None


# ============================================================
# INSTANCIA GLOBAL
# ============================================================

router = Router()


# ============================================================
# FUNCIÓN DE COMPATIBILIDAD
# ============================================================

def obtener_agente(
    pregunta
):

    return router.obtener_agente(
        pregunta
    )