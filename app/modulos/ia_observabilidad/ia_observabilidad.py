# ============================================================
# IA OBSERVABILIDAD
# app/modulos/ia_observabilidad/ia_observabilidad.py
# ============================================================

import os
import logging
from pathlib import Path

import pandas as pd

from flask import (
    Blueprint,
    jsonify,
    render_template,
    request
)

from app.servicios.bases.connection_manager import conectar_netezza


# ============================================================
# CONFIGURACION
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | IA_OBSERVABILIDAD | %(levelname)s | %(message)s"
)


PROJECT_ROOT = Path(__file__).resolve().parents[3]

TEMPLATE_FOLDER = PROJECT_ROOT / "templates"
STATIC_FOLDER = PROJECT_ROOT / "static"


# ============================================================
# BLUEPRINT
# ============================================================

ia_observabilidad_bp = Blueprint(
    "ia_observabilidad",
    __name__,
    template_folder=str(TEMPLATE_FOLDER),
    static_folder=str(STATIC_FOLDER)
)


# ============================================================
# CONFIGURACION POR DEFECTO
# ============================================================

DEFAULT_PERIODO = os.getenv(
    "IA_OBSERVABILIDAD_PERIODO",
    "202606"
)


# ============================================================
# UTILIDADES
# ============================================================

def limpiar(valor):
    """
    Convierte cualquier valor a texto limpio.
    """
    if valor is None:
        return ""

    try:
        if pd.isna(valor):
            return ""
    except Exception:
        pass

    return str(valor).strip()


def clave(valor):
    """
    Clave normalizada para comparaciones.
    """
    return limpiar(valor).upper()


def sql_literal(valor):
    """
    Convierte un valor Python a literal SQL seguro.

    IMPORTANTE:
    No utilizamos %s porque en el entorno actual de Netezza
    estaba provocando:

        ERROR: Attribute 'S' not found

    Se escapan comillas simples duplicándolas.
    """

    texto = limpiar(valor)

    texto = texto.replace(
        "'",
        "''"
    )

    return "'" + texto + "'"


def obtener_columna(df, nombre):
    """
    Encuentra una columna sin depender de mayúsculas/minúsculas.
    """

    if df is None or df.empty:
        return None

    objetivo = str(nombre).upper()

    for columna in df.columns:

        if str(columna).upper() == objetivo:
            return columna

    return None


def valor_columna(row, nombre, default=""):
    """
    Obtiene un valor de una fila sin depender del case
    del nombre de columna.
    """

    objetivo = str(nombre).upper()

    for columna in row.index:

        if str(columna).upper() == objetivo:

            valor = row[columna]

            if valor is None:
                return default

            try:
                if pd.isna(valor):
                    return default
            except Exception:
                pass

            return valor

    return default


# ============================================================
# ESTADOS
# ============================================================

ESTADO_PRIORIDAD = {
    "UNKNOWN": 0,
    "OK": 1,
    "WARNING": 2,
    "RUNNING": 3,
    "ERROR": 4
}


def normalizar_estado(valor):
    """
    Normaliza un estado individual.

    IMPORTANTE:
    La regla de VERDE para PROCESS e INPUT se determina
    posteriormente mediante TODOS_EXITO(), es decir, todos
    los registros de la categoría deben tener EXITO.

    Para REPORT:
        EXTRACTOR FINALIZADO -> OK
        NULL / vacío / cualquier otro valor -> WARNING

    Se mantienen ERROR/RUNNING para poder distinguir los
    estados no exitosos.
    """

    texto = clave(valor)

    # Aceptar EXITO y ÉXITO
    texto = texto.replace("É", "E")

    if not texto:
        return "UNKNOWN"

    # --------------------------------------------------------
    # EXITO
    # --------------------------------------------------------
    if texto == "EXITO":
        return "OK"

    # --------------------------------------------------------
    # ERROR
    # --------------------------------------------------------
    errores = (
        "ERROR",
        "ERR",
        "CANCEL",
        "CANCELADO",
        "CANCELED",
        "FALL",
        "FALLIDO",
        "FAILED",
        "FAIL",
        "NOK",
        "RECHAZ"
    )

    if any(valor_error in texto for valor_error in errores):
        return "ERROR"

    # --------------------------------------------------------
    # RUNNING
    # --------------------------------------------------------
    estados_running = (
        "RUNNING",
        "EJECUTANDO",
        "EJECUCION",
        "PROCESANDO",
        "PROCESSING",
        "EN EJECUCION",
        "INICIADO"
    )

    if any(valor_run in texto for valor_run in estados_running):
        return "RUNNING"

    # --------------------------------------------------------
    # WARNING / PENDIENTE
    # --------------------------------------------------------
    estados_warning = (
        "WARNING",
        "WARN",
        "ADVERT",
        "PENDIENT",
        "DEMOR",
        "DELAY",
        "ESPERA"
    )

    if any(valor_warning in texto for valor_warning in estados_warning):
        return "WARNING"

    return "UNKNOWN"


def todos_exito(valores):
    """
    Regla principal para PROCESS e INPUT.

    Verde (OK) únicamente cuando TODOS los valores existentes
    son exactamente EXITO.

    Si existe ERROR/CANCELADO/etc. -> ERROR.
    Si existe RUNNING -> RUNNING.
    Si existe cualquier otro valor o pendiente -> WARNING.
    Si no existen valores -> UNKNOWN.
    """

    valores_limpios = []

    for valor in valores:
        texto = clave(valor).replace("É", "E")

        if texto:
            valores_limpios.append(texto)

    if not valores_limpios:
        return "UNKNOWN"

    # --------------------------------------------------------
    # TODOS EXITO = VERDE
    # --------------------------------------------------------
    if all(valor == "EXITO" for valor in valores_limpios):
        return "OK"

    # --------------------------------------------------------
    # Si existe un error, rojo
    # --------------------------------------------------------
    for valor in valores_limpios:
        if normalizar_estado(valor) == "ERROR":
            return "ERROR"

    # --------------------------------------------------------
    # Si todavía hay una ejecución en curso
    # --------------------------------------------------------
    for valor in valores_limpios:
        if normalizar_estado(valor) == "RUNNING":
            return "RUNNING"

    # --------------------------------------------------------
    # Cualquier otro caso no es verde
    # --------------------------------------------------------
    return "WARNING"


def estado_reporte(valor):
    """
    Regla específica para REPORT.

    ESTADO_REPORTE = "Extractor Finalizado" -> VERDE / OK.
    NULL, vacío o cualquier otro valor -> WARNING / PENDIENTE.
    """

    texto = clave(valor).replace("É", "E")

    if texto == "EXTRACTOR FINALIZADO":
        return "OK"

    return "WARNING"


def combinar_estado(actual, nuevo):
    """
    Conserva el estado de mayor prioridad.
    Se mantiene únicamente para compatibilidad con otras
    partes del módulo; PROCESS e INPUT utilizan TODOS_EXITO().
    """

    actual = actual or "UNKNOWN"
    nuevo = nuevo or "UNKNOWN"

    if ESTADO_PRIORIDAD.get(nuevo, 0) > ESTADO_PRIORIDAD.get(actual, 0):
        return nuevo

    return actual


# ============================================================
# CONEXION Netezza
# ============================================================

def obtener_conexion():

    conn = conectar_netezza()

    if conn is None:

        raise RuntimeError(
            "No fue posible obtener conexión a Netezza."
        )

    return conn


# ============================================================
# EJECUTAR SQL
# ============================================================

def ejecutar_dataframe(sql):

    logging.info(
        "Ejecutando consulta Netezza..."
    )

    conn = obtener_conexion()

    try:

        df = pd.read_sql(
            sql,
            conn
        )

        logging.info(
            "Consulta OK. Registros: %s",
            len(df)
        )

        return df

    finally:

        try:
            conn.close()
        except Exception:
            pass


# ============================================================
# TOPOLOGIA
# ============================================================

SQL_TOPOLOGIA_BASE = """
SELECT
    A.SECUENCIA_REPORTE,
    A.NOMBRE_PROCESO_REPO,
    A.TIPO_REPO,
    A.FRECUENCIA_REPO,
    A.DIA_EJECUCION_REPO,
    A.HORA_EJECUCION_REPO,
    A.FRAME_EJECUTA_SP,
    A.LOG_NOMBRE_SP,

    B.SECUENCIA_INPUT,
    B.NOMBRE_INPUT,
    B.FRECUENCIA_INPUT,
    B.DIA_EJECUCION_INPUT,
    B.HORA_EJECUCION_INPUT,
    B.FILTRO_CAMPO,
    B.SCHEMA_INPUT

FROM CONTROL_MAKO..T_CATA_REPORTES_NORMA A

JOIN CONTROL_MAKO..T_CATA_INPUTS_NORMA B

    ON POSITION(
        '|' || B.SECUENCIA_INPUT || '|'
        IN
        '|' || A.RELACION || '|'
    ) > 0
    AND A.ESTADO = '1'
    AND A.TIPO_REPO <> 'RENTESEG' 
"""


def obtener_topologia(proceso=None):

    sql = SQL_TOPOLOGIA_BASE

    # ========================================================
    # FILTRO OPCIONAL
    # ========================================================

    if proceso:

        proceso_sql = sql_literal(
            proceso
        )

        sql += f"""
        WHERE UPPER(TRIM(A.NOMBRE_PROCESO_REPO))
              =
              UPPER(TRIM({proceso_sql}))
        """

    sql += """
    ORDER BY
        A.NOMBRE_PROCESO_REPO,
        B.NOMBRE_INPUT
    """

    logging.info(
        "Obteniendo topología. Proceso=%s",
        proceso or "TODOS"
    )

    return ejecutar_dataframe(
        sql
    )


# ============================================================
# ESTADOS DE EJECUCION
# ============================================================

def obtener_estados(periodo):

    periodo = limpiar(
        periodo
    )

    if not periodo:

        periodo = DEFAULT_PERIODO

    periodo_sql = sql_literal(
        periodo
    )

    sql = f"""
    SELECT

        PERIODO,

        NOMBRE_PROCESO_REPO,

        EJECUCION,

        NOMBRE_INPUT,

        EJECUCION_INPUT,

        ESTADO_REPORTE

    FROM CONTROL_MAKO..T_AGR_NORMA_CONTROL

    WHERE PERIODO = {periodo_sql}
    """

    logging.info(
        "Obteniendo estados. Periodo=%s",
        periodo
    )

    return ejecutar_dataframe(
        sql
    )


# ============================================================
# CONSTRUIR MAPAS DE ESTADO
# ============================================================

def construir_mapas_estado(df_estados):
    """
    Construye los estados finales por categoría.

    REGLAS:

    PROCESS
        T_AGR_NORMA_CONTROL.EJECUCION
        -> VERDE solamente si TODOS los registros del proceso
           tienen EXITO.

    INPUT
        T_AGR_NORMA_CONTROL.EJECUCION_INPUT
        -> VERDE solamente si TODOS los registros del input
           tienen EXITO.

    REPORT
        T_AGR_NORMA_CONTROL.ESTADO_REPORTE
        -> OK = VERDE / Extractor Finalizado
        -> NULL/vacío/diferente de OK = PENDIENTE (WARNING)

    No se mezclan las tres categorías.
    """

    estados_proceso = {}
    estados_input = {}
    estados_reporte = {}

    if df_estados is None or df_estados.empty:

        logging.warning(
            "No se encontraron estados para el periodo."
        )

        return (
            estados_proceso,
            estados_input,
            estados_reporte
        )

    # --------------------------------------------------------
    # Acumuladores crudos
    # --------------------------------------------------------

    valores_proceso = {}
    valores_input = {}
    valores_reporte = {}

    for _, row in df_estados.iterrows():

        # ----------------------------------------------------
        # PROCESS -> EJECUCION
        # ----------------------------------------------------

        nombre_proceso = clave(
            valor_columna(
                row,
                "NOMBRE_PROCESO_REPO"
            )
        )

        if nombre_proceso:

            valores_proceso.setdefault(
                nombre_proceso,
                []
            ).append(
                valor_columna(
                    row,
                    "EJECUCION"
                )
            )

            # ------------------------------------------------
            # REPORT -> ESTADO_REPORTE
            # ------------------------------------------------

            valores_reporte.setdefault(
                nombre_proceso,
                []
            ).append(
                valor_columna(
                    row,
                    "ESTADO_REPORTE"
                )
            )

        # ----------------------------------------------------
        # INPUT -> EJECUCION_INPUT
        # ----------------------------------------------------

        nombre_input = clave(
            valor_columna(
                row,
                "NOMBRE_INPUT"
            )
        )

        if nombre_input:

            valores_input.setdefault(
                nombre_input,
                []
            ).append(
                valor_columna(
                    row,
                    "EJECUCION_INPUT"
                )
            )

    # --------------------------------------------------------
    # CALCULAR ESTADO FINAL DE PROCESS
    # --------------------------------------------------------

    for nombre_proceso, valores in valores_proceso.items():

        estados_proceso[nombre_proceso] = todos_exito(
            valores
        )

        logging.debug(
            "PROCESS %s | valores=%s | estado=%s",
            nombre_proceso,
            [clave(v) for v in valores],
            estados_proceso[nombre_proceso]
        )

    # --------------------------------------------------------
    # CALCULAR ESTADO FINAL DE INPUT
    # --------------------------------------------------------

    for nombre_input, valores in valores_input.items():

        estados_input[nombre_input] = todos_exito(
            valores
        )

        logging.debug(
            "INPUT %s | valores=%s | estado=%s",
            nombre_input,
            [clave(v) for v in valores],
            estados_input[nombre_input]
        )

    # --------------------------------------------------------
    # CALCULAR ESTADO FINAL DE REPORT
    # --------------------------------------------------------

    for nombre_proceso, valores in valores_reporte.items():

        # Para REPORT, el valor final correcto es:
        # ESTADO_REPORTE = "Extractor Finalizado" -> OK.
        # Si hay varias filas, todas deben estar finalizadas.
        # Si alguna es NULL, vacía o tiene otro estado -> WARNING.
        estados_reporte[nombre_proceso] = (
            "OK"
            if valores and all(
                clave(v).replace("É", "E") == "EXTRACTOR FINALIZADO"
                for v in valores
            )
            else "WARNING"
        )

        logging.debug(
            "REPORT %s | valores=%s | estado=%s",
            nombre_proceso,
            [clave(v) for v in valores],
            estados_reporte[nombre_proceso]
        )

    return (
        estados_proceso,
        estados_input,
        estados_reporte
    )


# ============================================================
# CONSTRUIR GRAFO
# ============================================================

def construir_grafo(
    df_topologia,
    df_estados
):

    # ========================================================
    # MAPAS DE ESTADO
    # ========================================================

    (
        estados_proceso,
        estados_input,
        estados_reporte
    ) = construir_mapas_estado(
        df_estados
    )

    # ========================================================
    # CONTENEDORES
    # ========================================================

    nodes = []
    links = []

    node_ids = set()
    link_ids = set()

    # ========================================================
    # FUNCIONES INTERNAS
    # ========================================================

    def agregar_nodo(node):

        node_id = node["id"]

        if node_id in node_ids:
            return

        node_ids.add(
            node_id
        )

        nodes.append(
            node
        )

    def agregar_link(
        source,
        target,
        relation
    ):

        link_id = (
            f"{source}"
            f"__{target}"
            f"__{relation}"
        )

        if link_id in link_ids:
            return

        link_ids.add(
            link_id
        )

        links.append({
            "id": link_id,
            "source": source,
            "target": target,
            "relation": relation
        })

    # ========================================================
    # RECORRER TOPOLOGIA
    # ========================================================

    if df_topologia is not None:

        for _, row in df_topologia.iterrows():

            proceso = limpiar(
                valor_columna(
                    row,
                    "NOMBRE_PROCESO_REPO"
                )
            )

            input_name = limpiar(
                valor_columna(
                    row,
                    "NOMBRE_INPUT"
                )
            )

            if not proceso:
                continue

            proceso_key = clave(
                proceso
            )

            input_key = clave(
                input_name
            )

            # ------------------------------------------------
            # IDS
            # ------------------------------------------------

            proceso_id = (
                f"PROCESS::{proceso_key}"
            )

            report_id = (
                f"REPORT::{proceso_key}"
            )

            # ------------------------------------------------
            # ESTADO PROCESO
            # ------------------------------------------------

            estado_proceso = estados_proceso.get(
                proceso_key,
                "UNKNOWN"
            )

            estado_reporte = estados_reporte.get(
                proceso_key,
                "WARNING"
            )

            # ------------------------------------------------
            # DATOS PROCESO
            # ------------------------------------------------

            secuencia_reporte = limpiar(
                valor_columna(
                    row,
                    "SECUENCIA_REPORTE"
                )
            )

            frecuencia_reporte = limpiar(
                valor_columna(
                    row,
                    "FRECUENCIA_REPO"
                )
            )

            hora_reporte = limpiar(
                valor_columna(
                    row,
                    "HORA_EJECUCION_REPO"
                )
            )

            sp_log = limpiar(
                valor_columna(
                    row,
                    "LOG_NOMBRE_SP"
                )
            )

            if not sp_log:

                sp_log = limpiar(
                    valor_columna(
                        row,
                        "FRAME_EJECUTA_SP"
                    )
                )

            tipo_reporte = limpiar(
                valor_columna(
                    row,
                    "TIPO_REPO"
                )
            )

            # ------------------------------------------------
            # NODE PROCESS
            # ------------------------------------------------

            agregar_nodo({

                "id": proceso_id,

                "name": proceso,

                "type": "PROCESS",

                "status": estado_proceso,

                "sequence": secuencia_reporte,

                "frequency": frecuencia_reporte,

                "execution": hora_reporte,

                "schema": "",

                "sp_log": sp_log,

                "filter": "",

                "report_type": tipo_reporte

            })

            # ------------------------------------------------
            # NODE REPORT
            # ------------------------------------------------
            #
            # IMPORTANTE:
            # No existe un nombre independiente del reporte
            # en la consulta proporcionada.
            #
            # Por eso se utiliza NOMBRE_PROCESO_REPO.
            #

            agregar_nodo({

                "id": report_id,

                "name": proceso,

                "type": "REPORT",

                "status": estado_reporte,

                "sequence": secuencia_reporte,

                "frequency": frecuencia_reporte,

                "execution": hora_reporte,

                "schema": "",

                "sp_log": sp_log,

                "filter": "",

                "report_type": tipo_reporte

            })

            # ------------------------------------------------
            # PROCESS -> REPORT
            # ------------------------------------------------

            agregar_link(
                proceso_id,
                report_id,
                "OUTPUT"
            )

            # ------------------------------------------------
            # INPUT
            # ------------------------------------------------

            if input_name:

                input_id = (
                    f"INPUT::{input_key}"
                )

                estado_input = estados_input.get(
                    input_key,
                    "UNKNOWN"
                )

                agregar_nodo({

                    "id": input_id,

                    "name": input_name,

                    "type": "INPUT",

                    "status": estado_input,

                    "sequence": limpiar(
                        valor_columna(
                            row,
                            "SECUENCIA_INPUT"
                        )
                    ),

                    "frequency": limpiar(
                        valor_columna(
                            row,
                            "FRECUENCIA_INPUT"
                        )
                    ),

                    "execution": limpiar(
                        valor_columna(
                            row,
                            "HORA_EJECUCION_INPUT"
                        )
                    ),

                    "schema": limpiar(
                        valor_columna(
                            row,
                            "SCHEMA_INPUT"
                        )
                    ),

                    "sp_log": "",

                    "filter": limpiar(
                        valor_columna(
                            row,
                            "FILTRO_CAMPO"
                        )
                    )

                })

                # ------------------------------------------------
                # INPUT -> PROCESS
                # ------------------------------------------------

                agregar_link(
                    input_id,
                    proceso_id,
                    "INPUT"
                )

    # ========================================================
    # KPIs
    # ========================================================

    process_nodes = [
        node
        for node in nodes
        if node["type"] == "PROCESS"
    ]

    kpis = {

        "processes": len(
            process_nodes
        ),

        "normal": sum(
            1
            for node in process_nodes
            if node["status"] == "OK"
        ),

        "warning": sum(
            1
            for node in process_nodes
            if node["status"] == "WARNING"
        ),

        "error": sum(
            1
            for node in process_nodes
            if node["status"] == "ERROR"
        ),

        "running": sum(
            1
            for node in process_nodes
            if node["status"] == "RUNNING"
        )

    }

    # ========================================================
    # INFORMACION ADICIONAL
    # ========================================================

    tipos = {}

    for node in nodes:

        tipo = node.get(
            "type",
            "UNKNOWN"
        )

        tipos[tipo] = (
            tipos.get(
                tipo,
                0
            ) + 1
        )

    # ========================================================
    # RESULTADO
    # ========================================================

    resultado = {

        "nodes": nodes,

        "links": links,

        "kpis": kpis,

        "metadata": {

            "total_nodes": len(nodes),

            "total_links": len(links),

            "total_processes": len(
                process_nodes
            ),

            "node_types": tipos

        }

    }

    logging.info(
        "Grafo construido | Procesos=%s | Nodos=%s | Links=%s",
        kpis["processes"],
        len(nodes),
        len(links)
    )

    return resultado


# ============================================================
# PAGINA
# ============================================================

@ia_observabilidad_bp.route("/observabilidad")
@ia_observabilidad_bp.route("/ia-observabilidad")
def pagina():

    return render_template(
        "ia_observabilidad.html"
    )


# ============================================================
# API - LISTA DE PROCESOS
# ============================================================

@ia_observabilidad_bp.route(
    "/ia-observabilidad/api/procesos"
)
def api_procesos():

    try:

        df = obtener_topologia()

        if df is None or df.empty:

            return jsonify({
                "procesos": []
            })

        columna = obtener_columna(
            df,
            "NOMBRE_PROCESO_REPO"
        )

        if columna is None:

            return jsonify({
                "procesos": []
            })

        procesos = sorted(
            {
                limpiar(valor)
                for valor in df[columna].tolist()
                if limpiar(valor)
            },
            key=str.upper
        )

        logging.info(
            "Procesos disponibles: %s",
            len(procesos)
        )

        return jsonify({

            "procesos": procesos,

            "total": len(
                procesos
            )

        })

    except Exception as exc:

        logging.exception(
            "Error API procesos"
        )

        return jsonify({

            "error": str(exc),

            "procesos": []

        }), 500


# ============================================================
# API - GRAFO
# ============================================================

@ia_observabilidad_bp.route(
    "/ia-observabilidad/api/grafo"
)
def api_grafo():

    proceso = limpiar(
        request.args.get(
            "proceso",
            ""
        )
    )

    periodo = limpiar(
        request.args.get(
            "periodo",
            DEFAULT_PERIODO
        )
    )

    if not periodo:

        periodo = DEFAULT_PERIODO

    logging.info(
        "================================================"
    )

    logging.info(
        "Solicitud API GRAFO"
    )

    logging.info(
        "Proceso: %s",
        proceso or "TODOS"
    )

    logging.info(
        "Periodo: %s",
        periodo
    )

    logging.info(
        "================================================"
    )

    try:

        # ====================================================
        # TOPOLOGIA
        # ====================================================

        df_topologia = obtener_topologia(
            proceso=proceso or None
        )

        logging.info(
            "Topología obtenida: %s registros",
            len(df_topologia)
        )

        # ====================================================
        # ESTADOS
        # ====================================================

        df_estados = obtener_estados(
            periodo
        )

        logging.info(
            "Estados obtenidos: %s registros",
            len(df_estados)
        )

        # ====================================================
        # CONSTRUIR GRAFO
        # ====================================================

        resultado = construir_grafo(
            df_topologia,
            df_estados
        )

        # ====================================================
        # FILTROS
        # ====================================================

        resultado["filters"] = {

            "proceso": (
                proceso
                if proceso
                else "TODOS"
            ),

            "periodo": periodo

        }

        # ====================================================
        # INFORMACION API
        # ====================================================

        resultado["api"] = {

            "status": "OK",

            "topologia_rows": len(
                df_topologia
            ),

            "estado_rows": len(
                df_estados
            )

        }

        logging.info(
            "API OK | Procesos=%s | Nodos=%s | Links=%s",
            resultado["kpis"]["processes"],
            len(resultado["nodes"]),
            len(resultado["links"])
        )

        return jsonify(
            resultado
        )

    except Exception as exc:

        logging.exception(
            "ERROR API GRAFO"
        )

        return jsonify({

            "api": {

                "status": "ERROR",

                "message": str(exc)

            },

            "error": str(exc),

            "nodes": [],

            "links": [],

            "kpis": {

                "processes": 0,

                "normal": 0,

                "warning": 0,

                "error": 0,

                "running": 0

            }

        }), 500


# ============================================================
# EJECUCION DIRECTA
# ============================================================

if __name__ == "__main__":

    from flask import Flask

    app = Flask(
        __name__,
        template_folder=str(
            TEMPLATE_FOLDER
        ),
        static_folder=str(
            STATIC_FOLDER
        )
    )

    app.register_blueprint(
        ia_observabilidad_bp
    )

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )