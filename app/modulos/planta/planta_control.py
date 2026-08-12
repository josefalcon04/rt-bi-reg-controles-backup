import logging
import pandas as pd

from flask import (
    Blueprint,
    render_template,
    request,
    jsonify
)

from app.servicios.bases.connection_manager import conectar_netezza


# ============================================================
# BLUEPRINT
# ============================================================

planta_control_bp = Blueprint(
    "planta",
    __name__
)


# ============================================================
# COLORES OFICIALES POR TECNOLOGÍA
# ============================================================

COLORES_TECNOLOGIA = {
    "ADSL": "#F59E0B",   # Naranja
    "FTTH": "#2563EB",   # Azul
    "HFC": "#16A34A"     # Verde
}


# ============================================================
# CONSULTA PLANTA COMERCIAL
# ============================================================

def Query_Netezza():

    logging.info(
        "Ejecutando Query_Netezza - Planta Comercial"
    )

    conn = conectar_netezza()

    if not conn:

        logging.error(
            "No se pudo conectar a Netezza"
        )

        return []

    sql = """
        SELECT
            PERIODO,
            ESTADO,
            TECNOLOGIA,
            SUM(CANTIDAD) AS CANTIDAD
        FROM CONTROL_MAKO..T_AGR_VAL_PLT
        WHERE FUENTE = 'JRR_BA_PLANTA'
          AND TECNOLOGIA <> 'None'
          AND PERIODO >= '202501'
        GROUP BY
            PERIODO,
            ESTADO,
            TECNOLOGIA
        ORDER BY
            PERIODO,
            TECNOLOGIA
    """

    try:

        df = pd.read_sql(
            sql,
            conn
        )

        logging.info(
            "Query_Netezza OK - %s registros",
            len(df)
        )

        return df.to_dict(
            orient="records"
        )

    except Exception as error:

        logging.exception(
            "Error en Query_Netezza: %s",
            error
        )

        return []

    finally:

        try:
            conn.close()
        except Exception:
            pass


# ============================================================
# CONSULTA PLANTA CONTROL BI
# ============================================================

def Query_Netezza2():

    logging.info(
        "Ejecutando Query_Netezza2 - Planta Control BI"
    )

    conn = conectar_netezza()

    if not conn:

        logging.error(
            "No se pudo conectar a Netezza"
        )

        return []

    sql = """
        SELECT
            PERIODO,
            ESTADO,
            TECNOLOGIA,
            SUM(CANTIDAD) AS CANTIDAD
        FROM CONTROL_MAKO..T_AGR_VAL_PLT
        WHERE FUENTE = 'T_INH_PLT_CHU'
          AND TECNOLOGIA <> 'None'
          AND PERIODO >= '202501'
        GROUP BY
            PERIODO,
            ESTADO,
            TECNOLOGIA
        ORDER BY
            PERIODO,
            TECNOLOGIA
    """

    try:

        df = pd.read_sql(
            sql,
            conn
        )

        logging.info(
            "Query_Netezza2 OK - %s registros",
            len(df)
        )

        return df.to_dict(
            orient="records"
        )

    except Exception as error:

        logging.exception(
            "Error en Query_Netezza2: %s",
            error
        )

        return []

    finally:

        try:
            conn.close()
        except Exception:
            pass


# ============================================================
# NORMALIZAR DATAFRAME
# ============================================================

def normalizar_dataframe(datos):

    columnas = [
        "PERIODO",
        "ESTADO",
        "TECNOLOGIA",
        "CANTIDAD"
    ]

    if not datos:

        return pd.DataFrame(
            columns=columnas
        )

    df = pd.DataFrame(
        datos
    )

    # --------------------------------------------------------
    # Verificar columnas
    # --------------------------------------------------------

    columnas_faltantes = [
        columna
        for columna in columnas
        if columna not in df.columns
    ]

    if columnas_faltantes:

        logging.error(
            "Faltan columnas: %s",
            columnas_faltantes
        )

        return pd.DataFrame(
            columns=columnas
        )

    # --------------------------------------------------------
    # ESTADO
    # --------------------------------------------------------

    df["ESTADO"] = (
        df["ESTADO"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    # --------------------------------------------------------
    # TECNOLOGIA
    # --------------------------------------------------------

    df["TECNOLOGIA"] = (
        df["TECNOLOGIA"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    # --------------------------------------------------------
    # PERIODO
    # --------------------------------------------------------

    df["PERIODO"] = (
        df["PERIODO"]
        .astype(str)
        .str.strip()
    )

    df["PERIODO"] = pd.to_datetime(
        df["PERIODO"] + "01",
        format="%Y%m%d",
        errors="coerce"
    )

    # --------------------------------------------------------
    # CANTIDAD
    # --------------------------------------------------------

    df["CANTIDAD"] = pd.to_numeric(
        df["CANTIDAD"],
        errors="coerce"
    ).fillna(0)

    # --------------------------------------------------------
    # ELIMINAR REGISTROS INVÁLIDOS
    # --------------------------------------------------------

    df = df.dropna(
        subset=["PERIODO"]
    )

    # --------------------------------------------------------
    # ORDEN
    # --------------------------------------------------------

    df = df.sort_values(
        [
            "PERIODO",
            "TECNOLOGIA"
        ]
    )

    return df


# ============================================================
# APLICAR FILTROS
# ============================================================

def aplicar_filtros(df):

    if df.empty:
        return df

    # ========================================================
    # TECNOLOGÍA
    # ========================================================

    tecnologia = request.args.get(
        "tecnologia",
        "TODAS"
    )

    tecnologia = (
        tecnologia
        .strip()
        .upper()
    )

    if tecnologia != "TODAS":

        df = df[
            df["TECNOLOGIA"] == tecnologia
        ]

    # ========================================================
    # ESTADO
    # ========================================================

    estado = request.args.get(
        "estado",
        "ACTIVO"
    )

    estado = (
        estado
        .strip()
        .upper()
    )

    if estado:

        df = df[
            df["ESTADO"] == estado
        ]

    # ========================================================
    # PERÍODO
    #
    # Puede recibir:
    #
    # 2026
    # 202601
    # 202601,202602,202603
    # ========================================================

    periodo_param = request.args.get(
        "periodo",
        ""
    )

    periodo_param = (
        periodo_param
        .strip()
    )

    if periodo_param:

        periodos = [
            periodo.strip()
            for periodo in periodo_param.split(",")
            if periodo.strip()
        ]

        condiciones = []

        periodo_texto = (
            df["PERIODO"]
            .dt.strftime("%Y%m")
        )

        for periodo in periodos:

            # ------------------------------------------------
            # AÑO
            # ------------------------------------------------

            if len(periodo) == 4:

                condiciones.append(
                    periodo_texto.str.startswith(
                        periodo
                    )
                )

            # ------------------------------------------------
            # MES
            # ------------------------------------------------

            elif len(periodo) == 6:

                condiciones.append(
                    periodo_texto == periodo
                )

        # ----------------------------------------------------
        # UNIR CON OR
        # ----------------------------------------------------

        if condiciones:

            mascara = condiciones[0]

            for condicion in condiciones[1:]:

                mascara = (
                    mascara |
                    condicion
                )

            df = df[
                mascara
            ]

    return df


# ============================================================
# CONVERTIR DATAFRAME A JSON
# ============================================================

def dataframe_a_json(df):

    if df.empty:
        return []

    resultado = []

    meses = [
        "Ene",
        "Feb",
        "Mar",
        "Abr",
        "May",
        "Jun",
        "Jul",
        "Ago",
        "Sep",
        "Oct",
        "Nov",
        "Dic"
    ]

    for _, fila in df.iterrows():

        tecnologia = (
            str(fila["TECNOLOGIA"])
            .strip()
            .upper()
        )

        # ----------------------------------------------------
        # PERÍODO
        # ----------------------------------------------------

        periodo_codigo = (
            fila["PERIODO"]
            .strftime("%Y%m")
        )

        mes = fila["PERIODO"].month

        anio = (
            fila["PERIODO"]
            .strftime("%y")
        )

        periodo_label = (
            f"{meses[mes - 1]}-{anio}"
        )

        # ----------------------------------------------------
        # CANTIDAD EN MILLONES
        # ----------------------------------------------------

        cantidad = (
            float(fila["CANTIDAD"]) /
            1_000_000
        )

        resultado.append({

            "periodo":
                periodo_codigo,

            "periodo_label":
                periodo_label,

            "estado":
                str(fila["ESTADO"]),

            "tecnologia":
                tecnologia,

            "cantidad":
                round(
                    cantidad,
                    6
                ),

            "color":
                COLORES_TECNOLOGIA.get(
                    tecnologia,
                    "#64748B"
                )
        })

    return resultado


# ============================================================
# PREPARAR SERIES POR TECNOLOGÍA
#
# Esta estructura será utilizada por
# tendencias_plantas.js para pintar cada tecnología
# con su propia escala visual.
# ============================================================

def preparar_series_tecnologia(df):

    series = {}

    if df.empty:
        return series

    tecnologias = sorted(
        df["TECNOLOGIA"]
        .dropna()
        .unique()
        .tolist()
    )

    for tecnologia in tecnologias:

        df_tech = df[
            df["TECNOLOGIA"] == tecnologia
        ].copy()

        if df_tech.empty:
            continue

        df_tech = df_tech.sort_values(
            "PERIODO"
        )

        datos = []

        for _, fila in df_tech.iterrows():

            cantidad_millones = (
                float(fila["CANTIDAD"]) /
                1_000_000
            )

            datos.append({

                "periodo":
                    fila["PERIODO"].strftime(
                        "%Y-%m"
                    ),

                "periodo_codigo":
                    fila["PERIODO"].strftime(
                        "%Y%m"
                    ),

                "cantidad":
                    round(
                        cantidad_millones,
                        6
                    ),

                "estado":
                    str(fila["ESTADO"]),

                "tecnologia":
                    tecnologia,

                "color":
                    COLORES_TECNOLOGIA.get(
                        tecnologia,
                        "#64748B"
                    )
            })

        valores = [
            item["cantidad"]
            for item in datos
        ]

        if valores:

            valor_min = min(valores)
            valor_max = max(valores)

        else:

            valor_min = 0
            valor_max = 0

        # ----------------------------------------------------
        # ESCALA INDEPENDIENTE
        #
        # Dejamos margen arriba y abajo.
        # Esto permite que ADSL no quede pegado al cero
        # cuando FTTH tiene valores mucho mayores.
        # ----------------------------------------------------

        if valor_max == valor_min:

            margen = (
                max(
                    abs(valor_max) * 0.10,
                    0.01
                )
            )

        else:

            margen = (
                (valor_max - valor_min) * 0.12
            )

        escala_min = max(
            0,
            valor_min - margen
        )

        escala_max = (
            valor_max + margen
        )

        # Evitar escalas extremadamente pequeñas

        if escala_max <= escala_min:

            escala_max = (
                escala_min + 0.01
            )

        series[tecnologia] = {

            "tecnologia":
                tecnologia,

            "color":
                COLORES_TECNOLOGIA.get(
                    tecnologia,
                    "#64748B"
                ),

            "datos":
                datos,

            "min":
                round(
                    escala_min,
                    6
                ),

            "max":
                round(
                    escala_max,
                    6
                ),

            "valor_min":
                round(
                    valor_min,
                    6
                ),

            "valor_max":
                round(
                    valor_max,
                    6
                )
        }

    return series


# ============================================================
# RUTA PRINCIPAL
# ============================================================

@planta_control_bp.route(
    "/planta"
)
def index():

    return render_template(
        "planta_control.html"
    )


# ============================================================
# API - PLANTA COMERCIAL
# ============================================================

@planta_control_bp.route(
    "/planta_datos1"
)
def planta_datos1():

    try:

        datos = Query_Netezza()

        df = normalizar_dataframe(
            datos
        )

        df = aplicar_filtros(
            df
        )

        resultado = dataframe_a_json(
            df
        )

        # ====================================================
        # SERIES INDEPENDIENTES POR TECNOLOGÍA
        # ====================================================

        series = preparar_series_tecnologia(
            df
        )

        logging.info(
            "Planta Comercial - %s registros después de filtros",
            len(resultado)
        )

        return jsonify({

            "success":
                True,

            "planta":
                "Planta Comercial",

            "datos":
                resultado,

            "series":
                series,

            "total":
                len(resultado),

            "colores":
                COLORES_TECNOLOGIA,

            "escala_independiente":
                True
        })

    except Exception as error:

        logging.exception(
            "Error en /planta_datos1: %s",
            error
        )

        return jsonify({

            "success":
                False,

            "planta":
                "Planta Comercial",

            "datos":
                [],

            "series":
                {},

            "total":
                0,

            "error":
                str(error)

        }), 500


# ============================================================
# API - PLANTA CONTROL BI
# ============================================================

@planta_control_bp.route(
    "/planta_datos2"
)
def planta_datos2():

    try:

        datos = Query_Netezza2()

        df = normalizar_dataframe(
            datos
        )

        df = aplicar_filtros(
            df
        )

        resultado = dataframe_a_json(
            df
        )

        # ====================================================
        # SERIES INDEPENDIENTES POR TECNOLOGÍA
        # ====================================================

        series = preparar_series_tecnologia(
            df
        )

        logging.info(
            "Planta Control BI - %s registros después de filtros",
            len(resultado)
        )

        return jsonify({

            "success":
                True,

            "planta":
                "Planta Control BI",

            "datos":
                resultado,

            "series":
                series,

            "total":
                len(resultado),

            "colores":
                COLORES_TECNOLOGIA,

            "escala_independiente":
                True
        })

    except Exception as error:

        logging.exception(
            "Error en /planta_datos2: %s",
            error
        )

        return jsonify({

            "success":
                False,

            "planta":
                "Planta Control BI",

            "datos":
                [],

            "series":
                {},

            "total":
                0,

            "error":
                str(error)

        }), 500


# ============================================================
# API - OPCIONES DE FILTROS
# ============================================================

@planta_control_bp.route(
    "/planta_opciones"
)
def planta_opciones():

    try:

        datos1 = Query_Netezza()

        datos2 = Query_Netezza2()

        df1 = normalizar_dataframe(
            datos1
        )

        df2 = normalizar_dataframe(
            datos2
        )

        # ====================================================
        # TECNOLOGÍAS
        # ====================================================

        tecnologias = set()

        if not df1.empty:

            tecnologias.update(
                df1["TECNOLOGIA"]
                .unique()
            )

        if not df2.empty:

            tecnologias.update(
                df2["TECNOLOGIA"]
                .unique()
            )

        tecnologias = sorted(
            list(tecnologias)
        )

        # TODAS primero

        tecnologias.insert(
            0,
            "TODAS"
        )

        # ====================================================
        # ESTADOS
        # ====================================================

        estados = set()

        if not df1.empty:

            estados.update(
                df1["ESTADO"]
                .unique()
            )

        if not df2.empty:

            estados.update(
                df2["ESTADO"]
                .unique()
            )

        estados = sorted(
            list(estados)
        )

        # ACTIVO primero

        if "ACTIVO" in estados:

            estados.remove(
                "ACTIVO"
            )

            estados.insert(
                0,
                "ACTIVO"
            )

        # ====================================================
        # PERÍODOS
        # ====================================================

        periodos = set()

        if not df1.empty:

            periodos.update(
                df1["PERIODO"]
                .dt.strftime("%Y%m")
                .unique()
            )

        if not df2.empty:

            periodos.update(
                df2["PERIODO"]
                .dt.strftime("%Y%m")
                .unique()
            )

        periodos = sorted(
            list(periodos),
            reverse=True
        )

        # ====================================================
        # AÑO ACTUAL
        # ====================================================

        anio_actual = str(
            pd.Timestamp.now().year
        )

        # ====================================================
        # RESPUESTA
        # ====================================================

        return jsonify({

            "success":
                True,

            "tecnologias":
                tecnologias,

            "estados":
                estados,

            "periodos":
                periodos,

            "anio_actual":
                anio_actual,

            "colores":
                COLORES_TECNOLOGIA

        })

    except Exception as error:

        logging.exception(
            "Error en /planta_opciones: %s",
            error
        )

        return jsonify({

            "success":
                False,

            "tecnologias":
                [
                    "TODAS"
                ],

            "estados":
                [
                    "ACTIVO"
                ],

            "periodos":
                [],

            "anio_actual":
                str(
                    pd.Timestamp.now().year
                ),

            "colores":
                COLORES_TECNOLOGIA,

            "error":
                str(error)

        }), 500