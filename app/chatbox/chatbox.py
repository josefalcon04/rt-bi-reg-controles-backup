from flask import Blueprint, render_template, request, jsonify, session
import requests
import os
import re
import pandas as pd
from app.db import conectar_netezza
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from datetime import datetime
import time

chatbox_bp = Blueprint("chatbox", __name__)

OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://localhost:11434/api/generate"
)

MODELO = os.getenv(
    "OLLAMA_MODEL",
    "qwen2.5-coder:7b"
)

print(f"OLLAMA_URL: {OLLAMA_URL}")
print(f"MODELO: {MODELO}")

CREADOR = "Jose Luis Falcon Flores"
ROL_CREADOR = "Especialista en datos regulatorios - BI & BIG DATA"

# =========================
# 📄 BUSCAR DOCUMENTACIÓN
# =========================

def buscar_documentacion(pregunta):
    docs_path = os.path.join(
        os.getcwd(),
        "documentacion",
        "templates",
        "documentos"
    )

    if not os.path.exists(docs_path):
        return ""

    pregunta_limpia = pregunta.lower()

    stopwords = [
        "que", "qué", "hace", "el", "la", "los", "las",
        "proceso", "documento", "documentacion", "documentación",
        "explica", "explícame", "resumen", "resume", "de", "del"
    ]

    palabras = [
        p for p in re.findall(r"\w+", pregunta_limpia)
        if p not in stopwords and len(p) > 2
    ]

    mejores = []

    for archivo in os.listdir(docs_path):
        if archivo.endswith(".md"):
            ruta = os.path.join(docs_path, archivo)

            with open(ruta, "r", encoding="utf-8") as f:
                contenido = f.read()

            nombre_doc = archivo.replace("_", " ").replace(".md", "").lower()
            contenido_limpio = contenido.lower()

            score = 0

            for palabra in palabras:
                if palabra in nombre_doc:
                    score += 10
                elif palabra in contenido_limpio:
                    score += 1

            if score > 0:
                mejores.append({
                    "archivo": archivo,
                    "contenido": contenido,
                    "score": score
                })

    if not mejores:
        return (
            "No encontré documentación relacionada con esa consulta.\n"
            "Puedes revisar el menú: Documentación → Ver Documentos."
        )

    mejores.sort(key=lambda x: x["score"], reverse=True)

    doc = mejores[0]
    contenido = doc["contenido"].strip()

    lineas = [
        linea.strip()
        for linea in contenido.splitlines()
        if linea.strip()
        and not linea.strip().startswith("---")
    ]

    titulo = lineas[0] if lineas else doc["archivo"]
    resumen = " ".join(lineas[1:4]) if len(lineas) > 1 else ""

    if len(resumen) > 450:
        resumen = resumen[:450] + "..."

    return f"""
📄 Documento encontrado:
{doc['archivo']}

📝 Resumen:
{titulo}
{resumen}

📌 Para verlo completo:
Menú → Documentación → Ver Documentos → doble click sobre "{doc['archivo']}"
"""


# =========================
# 🎯 DETECTAR INTENCIÓN
# =========================

def detectar_intencion(pregunta):

    p = pregunta.lower()


    # =========================
    # 👤 CREADOR
    # =========================
    if any(x in p for x in [

        "quien te creo",
        "quién te creó",

        "quien es tu creador",
        "quién es tu creador",

        "quien te hizo",
        "quién te hizo",

        "autor",
        "creador"

    ]):

        return "creador"



    # =========================
    # 💻 CÓDIGO / SQL / SHELL
    # =========================
    if any(x in p for x in [

        "genera",
        "generar",

        "crea",
        "crear",

        "hazme",

        "codigo",
        "código",

        "sql",
        "shell",
        "script",

        "procedimiento",
        "procedure",

        "python",
        "flask",

        "oracle",
        "netezza sql",

        "optimiza query",
        "convierte"

    ]):

        return "codigo"



    # =========================
    # 🧾 LOGS / EJECUCIONES
    # =========================
    if any(x in p for x in [

        "ejecuto",
        "ejecutó",

        "corrio",
        "corrió",

        "fallo",
        "falló",

        "error",

        "log",
        "logs",

        "estado",

        "ultima ejecucion",
        "última ejecución",

        "termino",
        "terminó",

        "finalizo",
        "finalizó",

        "paso",
        "detalle"

    ]):

        return "logs_norma"

    if any(x in p for x in [
        "tendencia",
        "proyeccion",
        "proyección",
        "grafico",
        "gráfico",
        "planta mtc",
        "trafico acumulado",
        "tráfico acumulado"
    ]):
        return "tendencia_planta"

    # =========================
    # 📚 CATÁLOGO NORMAS
    # =========================
    if any(x in p for x in [

        "reporte",
        "reportes",

        "input",
        "inputs",

        "ejecuta",
        "ejecucion",
        "ejecución",

        "calendario",

        "nripo",
        "nrip",

        "norma"

    ]):

        return "catalogo_norma"



    # =========================
    # 📄 DOCUMENTACIÓN
    # =========================
    if any(x in p for x in [

        "documento",
        "documentacion",
        "documentación",

        "manual",

        "proceso",
        "explica"

    ]):

        return "docs"



    # =========================
    # 📊 DASHBOARD / BI
    # =========================
    if any(x in p for x in [

        "devolucion",
        "devolución",

        "candidato",

        "success",
        "reject",

        "monto",

        "dashboard",

        "nok",
        "excluido",

        "netezza"

    ]):

        return "bi"



    return "general"

# =========================
# 🗄️ CONSULTAR NETEZZA - DEVOLUCIONES
# =========================

def consultar_netezza(pregunta):
    p = pregunta.lower()

    if "candidato" in p:
        sql = """
        SELECT 
            SUM(TOT_CANT_REGISTROS) AS CANTIDAD
        FROM CONTROL_MAKO..TMP_JFF_FEATDEVO_2_017
        WHERE UPPER(COMENTARIO) LIKE 'OK%'
        """

    elif "nok" in p or "excluido" in p:
        sql = """
        SELECT 
            SUM(TOT_CANT_REGISTROS) AS CANTIDAD
        FROM CONTROL_MAKO..TMP_JFF_FEATDEVO_2_017
        WHERE UPPER(COMENTARIO) LIKE 'NOK%'
        """

    elif "success" in p:
        sql = """
        SELECT 
            SUM(TOT_CANT_REGISTROS) AS CANTIDAD,
            SUM(MONTO_SOLES) AS MONTO
        FROM CONTROL_MAKO..TMP_JFF_FEATDEVO_2_017
        WHERE UPPER(RESULTADO) LIKE '%SUCCESS%'
        """

    elif "reject" in p:
        sql = """
        SELECT 
            SUM(TOT_CANT_REGISTROS) AS CANTIDAD,
            SUM(MONTO_SOLES) AS MONTO
        FROM CONTROL_MAKO..TMP_JFF_FEATDEVO_2_017
        WHERE UPPER(RESULTADO) LIKE '%REJECT%'
        """

    elif "monto" in p:
        sql = """
        SELECT 
            SUM(TOT_CANT_REGISTROS) AS CANTIDAD,
            SUM(MONTO_SOLES) AS MONTO
        FROM CONTROL_MAKO..TMP_JFF_FEATDEVO_2_017
        """

    else:
        return ""

    try:
        conn = conectar_netezza()
        df = pd.read_sql(sql, conn)
        conn.close()

        if df.empty:
            return "No se encontraron datos en Netezza."

        row = df.iloc[0]

        cantidad = row.get("CANTIDAD", 0)
        monto = row.get("MONTO", None)

        if pd.isna(cantidad):
            cantidad = 0

        if monto is not None and not pd.isna(monto):
            return (
                f"Resultado consultado en Netezza:\n\n"
                f"Cantidad: {int(cantidad):,}\n"
                f"Monto: S/ {float(monto):,.2f}"
            )

        return (
            f"Resultado consultado en Netezza:\n\n"
            f"Cantidad: {int(cantidad):,}"
        )

    except Exception as e:
        return f"Error consultando Netezza: {str(e)}"


# =========================
# 📚 CONSULTAR CATÁLOGO NORMA
# =========================

def consultar_catalogo_norma(pregunta):
    p = pregunta.upper()

    match = re.search(
        r'(NRI[A-Z]*[_ ]?\d+)',
        p
    )

    if not match:
        return ""

    reporte = match.group(1).replace(" ", "_")

    sql = f"""
    SELECT  
        A.NOMBRE_PROCESO_REPO AS NOMBRE_REPORTE, 
        A.TIPO_REPO AS TIPO_REPORTE,
        A.FRECUENCIA_REPO AS FRECUENCIA_REPORTE, 
        CASE 
        WHEN SUBSTRING(A.DIA_EJECUCION_REPO,3,2) = '01' THEN 
            'La ejecución son todos los ' 
            || CAST(SUBSTRING(A.DIA_EJECUCION_REPO,1,2) AS INTEGER)
            || ' de los meses '
            || LPAD(CAST(CAST(SUBSTRING(A.DIA_EJECUCION_REPO,3,2) AS INTEGER) AS VARCHAR(2)),2,'0')
            || ', '
            || LPAD(CAST(CAST(SUBSTRING(A.DIA_EJECUCION_REPO,3,2) AS INTEGER) + 3 AS VARCHAR(2)),2,'0')
            || ', '
            || LPAD(CAST(CAST(SUBSTRING(A.DIA_EJECUCION_REPO,3,2) AS INTEGER) + 6 AS VARCHAR(2)),2,'0')
            || ', '
            || LPAD(CAST(CAST(SUBSTRING(A.DIA_EJECUCION_REPO,3,2) AS INTEGER) + 9 AS VARCHAR(2)),2,'0')
        ELSE 
            'La ejecución son todos los ' 
            || LPAD(CAST(CAST(SUBSTRING(A.DIA_EJECUCION_REPO,1,2) AS INTEGER) AS VARCHAR(2)),2,'0')
            || ' de los meses '
            || LPAD(CAST(CAST(SUBSTRING(A.DIA_EJECUCION_REPO,3,2) AS INTEGER) AS VARCHAR(2)),2,'0')
            || ', '
            || LPAD(CAST(CAST(SUBSTRING(A.DIA_EJECUCION_REPO,3,2) AS INTEGER) + 3 AS VARCHAR(2)),2,'0')
            || ', '
            || LPAD(CAST(CAST(SUBSTRING(A.DIA_EJECUCION_REPO,3,2) AS INTEGER) + 6 AS VARCHAR(2)),2,'0')
            || ', '
            || LPAD(CAST(CAST(SUBSTRING(A.DIA_EJECUCION_REPO,3,2) AS INTEGER) + 9 AS VARCHAR(2)),2,'0')
        END AS DIA_EJECUCION_REPORTE, 
        A.FRAME_EJECUTA_SP AS LAYOUT_REPORTE,
        A.LOG_NOMBRE_SP AS NOMBRE_SP,
        A.ALCANCE_FUNCIONAL,
        A.ALCANCE_TECNICO,
        A.TABLA_HISTORICA,
        B.NOMBRE_INPUT AS NOMBRE_INPUT,
        B.FRECUENCIA_INPUT AS FRECUENCIA_INPUT,
        B.SCHEMA_INPUT AS SCHEMA_INPUT
    FROM CONTROL_MAKO..T_CATA_REPORTES_NORMA A 
    INNER JOIN CONTROL_MAKO..T_CATA_INPUTS_NORMA B 
        ON (
            POSITION(
                '|' || B.SECUENCIA_INPUT || '|'
                IN
                '|' || A.RELACION || '|'
            ) > 0
        )
    WHERE UPPER(A.NOMBRE_PROCESO_REPO) LIKE '%{reporte}%'
    """

    try:
        conn = conectar_netezza()
        df = pd.read_sql(sql, conn)
        conn.close()

        if df.empty:
            return f"No encontré información para el reporte {reporte}."

        row = df.iloc[0]

        inputs = "\n".join(
            [
                f"• {x}"
                for x in df["NOMBRE_INPUT"].dropna().unique()
            ]
        )

        schemas = "\n".join(
            [
                f"• {x}"
                for x in df["SCHEMA_INPUT"].dropna().unique()
            ]
        )

        return f"""
📄 Reporte: {row["NOMBRE_REPORTE"]}

📌 Tipo: {row["TIPO_REPORTE"]}

🔁 Frecuencia: {row["FRECUENCIA_REPORTE"]}

📅 Ejecución: {row["DIA_EJECUCION_REPORTE"]}

⚙ Layout/SP: {row["LAYOUT_REPORTE"]}

🧩 SP: {row["NOMBRE_SP"]}

🗃 Tabla histórica: {row["TABLA_HISTORICA"]}

📥 Inputs relacionados:
{inputs}

📂 Schemas:
{schemas}
"""

    except Exception as e:
        return f"Error consultando catálogo de norma: {str(e)}"


# =========================
# 🧾 CONSULTAR LOGS NORMA
# =========================

def consultar_logs_norma(pregunta):
    p = pregunta.upper()
    p_lower = pregunta.lower()

    match = re.search(
        r'(NRI[A-Z]*[_ ]?\d+)',
        p
    )

    if not match:
        return (
            "Indica el reporte que deseas consultar.\n"
            "Ejemplo: ¿NRIPO_035 ejecutó bien?"
        )

    reporte = match.group(1).replace(" ", "_")
    sp = "SP_NRM_" + reporte

    mostrar_pasos = any(x in p_lower for x in [
        "paso",
        "pasos",
        "detalle",
        "detalles",
        "donde fallo",
        "dónde falló",
        "en que paso",
        "en qué paso",
        "error",
        "fallo",
        "falló"
    ])

    sql = f"""
        SELECT 
            A.LOG_NOMBRE_SP AS NOMBRE_SP,
            A.LOG_PARAMETRO_SP AS PARAMETRO,
            A.LOG_FECHA_INICIO,
            A.LOG_FECHA_FIN,
            A.LOG_ESTADO,
            B.LOG_NRO_PASO AS NUMERO_PASO,
            B.LOG_DETAIL AS DETALLE_PASO
        FROM PROD_REGU_NORMA_DATA..T_NRM_LOG A
        LEFT JOIN PROD_REGU_NORMA_DATA..T_NRM_LOG_DETAIL B
            ON A.LOG_NRO_EJECUCION = B.LOG_NRO_EJECUCION
            AND A.LOG_NOMBRE_SP = B.LOG_NOMBRE_SP
        WHERE A.LOG_NOMBRE_SP = '{sp}'
        AND A.LOG_FECHA_INICIO = (
            SELECT MAX(LOG_FECHA_INICIO)
            FROM PROD_REGU_NORMA_DATA..T_NRM_LOG
            WHERE LOG_NOMBRE_SP = '{sp}'
        )
        ORDER BY B.LOG_NRO_PASO
    """

    try:
        conn = conectar_netezza()
        df = pd.read_sql(sql, conn)
        conn.close()

        if df.empty:
            return f"No encontré logs para {reporte}."

        cab = df.iloc[0]

        estado = str(cab["LOG_ESTADO"]).upper()

        es_exitoso = (
            "OK" in estado
            or "SUCCESS" in estado
            or "FIN" in estado
            or "EXITO" in estado
            or "ÉXITO" in estado
        )

        es_error = (
            "ERR" in estado
            or "FAIL" in estado
            or "NOK" in estado
            or "ERROR" in estado
        )

        if es_exitoso:
            resumen_estado = "El proceso ejecutó correctamente."
            icono_estado = "✅"
        elif es_error:
            resumen_estado = "El proceso presenta error o ejecución no conforme."
            icono_estado = "❌"
        else:
            resumen_estado = "No se pudo determinar claramente si ejecutó correctamente."
            icono_estado = "⚠️"

        respuesta = f"""
📌 Reporte: {reporte}

⚙ SP: {cab["NOMBRE_SP"]}

📊 Estado: {cab["LOG_ESTADO"]} {icono_estado}

🕒 Inicio: {cab["LOG_FECHA_INICIO"]}

🏁 Fin: {cab["LOG_FECHA_FIN"]}

Resumen:
{resumen_estado}
"""

        # Mostrar pasos solo si:
        # 1. El usuario los pide
        # 2. El proceso falló o no está claro
        if mostrar_pasos or not es_exitoso:

            pasos_df = df[
                df["DETALLE_PASO"].notna()
            ].copy()

            if pasos_df.empty:
                pasos = "No se encontró detalle de pasos para la última ejecución."
            else:
                pasos = "\n".join(
                    [
                        f"{int(r['NUMERO_PASO']) if pd.notna(r['NUMERO_PASO']) else '-'}. {r['DETALLE_PASO']}"
                        for _, r in pasos_df.iterrows()
                    ]
                )

            if mostrar_pasos:

                if es_exitoso:

                    titulo_pasos = (
                        "Veo que el proceso ejecutó correctamente ✅.\n"
                        "De todas formas, te comparto los pasos registrados:"
                    )

                else:

                    titulo_pasos = (
                        "El proceso presenta observaciones ❌.\n"
                        "Comparto los pasos para revisión:"
                    )

            else:

                titulo_pasos = (
                    "Detalle para revisión:"
                )

            respuesta += f"""

🧾 {titulo_pasos}

{pasos}
"""

        return respuesta

    except Exception as e:
        return f"Error consultando logs de norma: {str(e)}"


# =========================
# 🤖 LLAMAR OLLAMA
# =========================

def llamar_ollama(pregunta, contexto="", memoria=""):

    prompt = f"""
Eres BI Assistant Senior.

Fuiste creado por Jose Luis Falcon Flores,
Especialista BI en datos regulatorios.

Especialidades:

- Netezza
- Oracle SQL
- Shell Unix
- Procedimientos almacenados
- Python
- Flask
- ETL
- Data Warehouse
- BI
- Reportes regulatorios
- Logs operativos

Reglas:

- Responde siempre en español.
- Sé claro, profesional y amigable.
- Sé breve salvo que el usuario solicite detalle.
- Nunca inventes información.
- Si no conoces la respuesta, indícalo de forma transparente.
- Si no tienes suficiente contexto, solicita más información.
- Prioriza Netezza sobre SQL genérico.
- Si piden código SQL, genera código completo y optimizado.
- Si piden Shell, agrega logs y control de errores.
- Si piden Stored Procedures, agrega manejo de errores y validaciones.
- Si piden documentación, responde basado en la documentación encontrada.
- Si piden indicadores o dashboards, utiliza la información disponible y explica el resultado.
- Si preguntan por tendencias, realiza un análisis simple del comportamiento.
- Si preguntan por proyecciones, indica que son estimaciones basadas en tendencias históricas.
- Si preguntan quién te creó, responde:
  "Fui creado por José Luis Falcon Flores, Especialista en Datos Regulatorios del equipo BI."

- Si no tienes conocimiento sobre un tema, responde:

  "🤖 Aún no tengo conocimiento sobre ese tema.

  Mi conocimiento continúa creciendo y pronto podré ayudarte también con esa información.

  Actualmente puedo ayudarte con:
  • Documentación
  • Reportes regulatorios
  • Dashboard de devoluciones
  • Logs de ejecución
  • SQL y Netezza
  • Indicadores y tendencias

  🚀 Cada día aprendo algo nuevo."

Memoria:
{memoria}

Contexto:
{contexto}

Pregunta:
{pregunta}
"""

    r = requests.post(

        OLLAMA_URL,

        json={

            "model": MODELO,

            "prompt": prompt,

            "stream": False,

            "keep_alive": "15m",

            "options": {

                "num_predict": 220,

                "temperature": 0.1,

                "top_p": 0.9,

                "num_ctx": 4096,

                "repeat_penalty": 1.1

            }

        },

        timeout=90

    )


    r.raise_for_status()

    return r.json().get(
        "response",
        ""
    )


# =========================
# 🧠 AGENTE PRINCIPAL
# =========================

def agente(pregunta):
    memoria = session.get("memoria_chat", [])
    memoria_txt = "\n".join(memoria[-6:])

    p = pregunta.lower().strip()

    respuestas_rapidas = {
        "hola": "Hola, soy tu BI Assistant. Puedo ayudarte con documentación, reportes, inputs, dashboards, procesos BI, devoluciones, Netezza y reportes regulatorios.",
        "buenas": "Hola, soy tu BI Assistant. Puedo ayudarte con documentación, reportes, inputs, dashboards, procesos BI, devoluciones, Netezza y reportes regulatorios.",
        "que puedes hacer": "Puedo ayudarte con documentación, reportes, inputs, dashboards, procesos BI, devoluciones, Netezza y reportes regulatorios.",
        "qué puedes hacer": "Puedo ayudarte con documentación, reportes, inputs, dashboards, procesos BI, devoluciones, Netezza y reportes regulatorios.",
        "ayuda": "Puedes preguntarme por procesos documentados, reportes de norma, inputs, indicadores, dashboards, devoluciones, logs de ejecución o conceptos BI."
    }

    for clave, respuesta in respuestas_rapidas.items():
        if clave in p and len(p.split()) <= 5:
            memoria.append(f"Usuario: {pregunta}")
            memoria.append(f"Asistente: {respuesta}")
            session["memoria_chat"] = memoria[-10:]
            return respuesta

    if "me llamo" in p:
        respuesta = "Perfecto, lo tendré presente durante esta conversación."
        memoria.append(f"Usuario: {pregunta}")
        memoria.append(f"Asistente: {respuesta}")
        session["memoria_chat"] = memoria[-10:]
        return respuesta

    intencion = detectar_intencion(pregunta)

    if intencion == "tendencia_planta":
        respuesta = consultar_tendencia_planta(pregunta)

        memoria.append(f"Usuario: {pregunta}")
        memoria.append(f"Asistente: {respuesta}")
        session["memoria_chat"] = memoria[-10:]

        return respuesta

    # =========================
    # 👤 CREADOR
    # =========================

    if intencion == "creador":

        respuesta = (
            "Fui creado por Jose Luis Falcon Flores, "
            "Especialista BI en datos regulatorios - BI & BIGDATA, "
            "para apoyar consultas de documentación, reportes, "
            "Netezza, logs operativos, SQL y desarrollo técnico."
        )

        memoria.append(f"Usuario: {pregunta}")
        memoria.append(f"Asistente: {respuesta}")
        session["memoria_chat"] = memoria[-10:]

        return respuesta

    if intencion == "logs_norma":
        respuesta = consultar_logs_norma(pregunta)
        memoria.append(f"Usuario: {pregunta}")
        memoria.append(f"Asistente: {respuesta}")
        session["memoria_chat"] = memoria[-10:]
        return respuesta

    if intencion == "catalogo_norma":
        respuesta = consultar_catalogo_norma(pregunta)
        memoria.append(f"Usuario: {pregunta}")
        memoria.append(f"Asistente: {respuesta}")
        session["memoria_chat"] = memoria[-10:]
        return respuesta

    if intencion == "docs":
        respuesta = buscar_documentacion(pregunta)

        if respuesta:
            memoria.append(f"Usuario: {pregunta}")
            memoria.append(f"Asistente: {respuesta}")
            session["memoria_chat"] = memoria[-10:]
            return respuesta

    if intencion == "bi":
        respuesta = consultar_netezza(pregunta)

        if respuesta:
            memoria.append(f"Usuario: {pregunta}")
            memoria.append(f"Asistente: {respuesta}")
            session["memoria_chat"] = memoria[-10:]
            return respuesta

    respuesta = llamar_ollama(
    pregunta=pregunta,
    memoria=memoria_txt
    )

    # =========================
    # RESPUESTA DESCONOCIDA
    # =========================

    if (
        not respuesta
        or len(respuesta.strip()) < 10
        or "no encontré información" in respuesta.lower()
        or "no tengo información" in respuesta.lower()
    ):
        respuesta = """
    🤖 Aún no tengo conocimiento sobre ese tema.

    Mi conocimiento sigue creciendo y pronto podré ayudarte también con esa información.

    Por ahora puedo ayudarte con:

    • Documentación
    • Reportes regulatorios
    • Logs de ejecución
    • Inputs y catálogos
    • Dashboard de devoluciones
    • SQL y Netezza
    • Tendencias e indicadores

    🚀 Cada día aprendo algo nuevo.
    """

    memoria.append(f"Usuario: {pregunta}")
    memoria.append(f"Asistente: {respuesta}")
    session["memoria_chat"] = memoria[-10:]

    return respuesta

# =========================
# 🌐 RUTAS FLASK
# =========================

@chatbox_bp.route("/chatbox")
def home():
    return render_template("chatbox.html")


@chatbox_bp.route("/chatbox/ask", methods=["POST"])
def ask():
    data = request.get_json()
    pregunta = data.get("message", "").strip()

    if not pregunta:
        return jsonify({"response": "Por favor escribe un mensaje."})

    try:
        inicio = time.time()

        respuesta = agente(pregunta)

        fin = time.time()

        tiempo = round(fin - inicio, 2)

        respuesta_final = f"""
        {respuesta}

        ⏱ Tiempo de respuesta:
        {tiempo} segundos
        """

        return jsonify({
            "response": respuesta_final
        })

    except Exception as e:
        return jsonify({
            "response": f"No pude procesar la consulta. Detalle: {str(e)}"
        }), 500


@chatbox_bp.route("/chatbox/limpiar", methods=["POST"])
def limpiar():
    session.pop("memoria_chat", None)
    return jsonify({"response": "Memoria limpiada."})

def consultar_tendencia_planta(pregunta):
    p = pregunta.lower()

    if "mtc" in p:
        nombre_planta = "PLANTA MTC"

        sql = """
        SELECT 
            TRANS_DT AS PERIODO,
            CASE 
                WHEN PRODUCTOS IN ('CONTROL','CONTRATO') THEN 'POSTPAGO' 
                ELSE 'PREPAGO' 
            END AS GRUPO,
            COUNT(*) AS CANTIDAD 
        FROM PROD_REGU_INPUT_DATA..T_INP_PLT_MTC
        WHERE TRANS_DT >= '2025-01-01'
          AND ESTADO1 = 'A'
          AND PRODUCTOS IS NOT NULL 
          AND LENGTH(PRODUCTOS) <> 0
        GROUP BY 1,2
        ORDER BY 1,2 DESC
        """

    elif "trafico" in p or "tráfico" in p or "acumulado" in p:
        nombre_planta = "PLANTA TRÁFICO ACUMULADO"

        sql = """
        SELECT 
            PERIODO,
            CASE 
                WHEN EVENTOS = '100' THEN 'TRAFICO ENTRANTE + MOVIVOX'
                WHEN EVENTOS = '010' THEN 'TRAFICO SALIENTE'
                WHEN EVENTOS = '001' THEN 'DATOS'
            END AS GRUPO,
            CANTIDAD
        FROM CONTROL_MAKO..T_CTRL_TRAFICO_ACUMULADO
        WHERE TABLA LIKE 'TRF_ANT%'
          AND PERIODO >= '202501'
        ORDER BY 1 ASC, 3 DESC
        """

    else:
        return ""

    try:
        conn = conectar_netezza()
        df = pd.read_sql(sql, conn)
        conn.close()

        if df.empty:
            return f"No encontré información para {nombre_planta}."

        df["CANTIDAD"] = pd.to_numeric(df["CANTIDAD"], errors="coerce").fillna(0)

        tendencia = (
            df.groupby("PERIODO", as_index=False)["CANTIDAD"]
            .sum()
            .sort_values("PERIODO")
        )

        if len(tendencia) < 2:
            return f"No hay suficientes periodos para calcular tendencia de {nombre_planta}."

        ultimo = tendencia.iloc[-1]
        anterior = tendencia.iloc[-2]

        valor_ultimo = float(ultimo["CANTIDAD"])
        valor_anterior = float(anterior["CANTIDAD"])

        variacion = (
            ((valor_ultimo - valor_anterior) / valor_anterior) * 100
            if valor_anterior != 0 else 0
        )

        if variacion > 2:
            estado = "creciente"
            icono = "📈"
        elif variacion < -2:
            estado = "decreciente"
            icono = "📉"
        else:
            estado = "estable"
            icono = "➖"

        # Proyección simple: último valor + promedio de variación de últimos periodos
        tendencia["DIF"] = tendencia["CANTIDAD"].diff()
        promedio_dif = tendencia["DIF"].tail(3).mean()
        proyeccion = valor_ultimo + promedio_dif if pd.notna(promedio_dif) else valor_ultimo

        # Crear imagen
        img_folder = os.path.join(os.getcwd(), "static", "img", "chatbot")
        os.makedirs(img_folder, exist_ok=True)

        nombre_img = f"tendencia_{nombre_planta.lower().replace(' ', '_').replace('á','a')}.png"
        ruta_img = os.path.join(img_folder, nombre_img)

        plt.figure(figsize=(8, 4))
        plt.plot(
            tendencia["PERIODO"].astype(str),
            tendencia["CANTIDAD"],
            marker="o"
        )
        plt.title(nombre_planta)
        plt.xlabel("Periodo")
        plt.ylabel("Cantidad")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(ruta_img)
        plt.close()

        url_img = f"/static/img/chatbot/{nombre_img}"

        return f"""
{icono} Tendencia de {nombre_planta}

Último periodo: {ultimo["PERIODO"]}
Cantidad actual: {valor_ultimo:,.0f}
Periodo anterior: {anterior["PERIODO"]}
Cantidad anterior: {valor_anterior:,.0f}

Variación: {variacion:.2f}%
Estado: {estado}

Proyección siguiente periodo: {proyeccion:,.0f} aprox.

Gráfico generado:
{url_img}
"""

    except Exception as e:
        return f"Error consultando tendencia de planta: {str(e)}"