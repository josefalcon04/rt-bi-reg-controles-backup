import json
import logging

import pandas as pd

from flask import Blueprint, render_template

from app.servicios.bases.connection_manager import conectar_netezza


NRIPO_035_bp = Blueprint("NRIPO_035", __name__)


# ============================================================
# CONSULTAS
# ============================================================

def Query_NRIPO_035_TOT():

    conn = conectar_netezza()

    if not conn:
        logging.error("No se pudo conectar a Netezza")
        return []

    sql = """
        SELECT
            DISTINCT
            SUBSTRING(ANIO_MES, 1, 4)
            || LPAD(TRIM(MES), 2, '0') AS PERIODO,

            SUM(LINEAS_EN_SERVICIO) AS LINEAS_EN_SERVICIO,

            SUM(LINEAS_A_SERVICIO_A_3_MES)
                AS LINEAS_A_SERVICIO_A_3_MES

        FROM PROD_REGU_NORMA_DATA..T_NRM_NRIPO_035_HIST

        WHERE ANIO_MES >= '202501'

        GROUP BY 1

        ORDER BY 1 ASC
    """

    try:

        df = pd.read_sql(sql, conn)

        return df.to_dict(orient="records")

    except Exception as e:

        logging.error(
            f"Error Query_NRIPO_035_TOT: {e}"
        )

        return []

    finally:

        conn.close()


# ============================================================
# NRIPO 033 VS 035
# ============================================================

def Query_nripo_33_35_DIF():

    conn = conectar_netezza()

    if not conn:

        logging.error(
            "No se pudo conectar a Netezza"
        )

        return []

    sql = """
        SELECT

            b.PERIODO AS PERIODO,

            b.NRIPO_033,

            c.LINEAS_EN_SERVICIO,

            (
                b.NRIPO_033
                - c.LINEAS_EN_SERVICIO
            ) AS DIFERENCIA_NRIPO_033

        FROM
        (

            SELECT

                SUBSTRING(ANIO_MES,1,4)
                || TRIM(TO_CHAR(MES,'00'))
                AS PERIODO,

                SUM(LINEAS_SERVICIO)
                AS NRIPO_033

            FROM PROD_REGU_NORMA_DATA..T_NRM_NRIPO_033_HIST

            WHERE ANIO_MES >= '202501'

            GROUP BY 1

        ) b

        FULL OUTER JOIN

        (

            SELECT

                SUBSTRING(ANIO_MES,1,4)
                || LPAD(TRIM(MES),2,'0')
                AS PERIODO,

                SUM(LINEAS_EN_SERVICIO)
                AS LINEAS_EN_SERVICIO,

                SUM(LINEAS_A_SERVICIO_A_3_MES)
                AS LINEAS_A_SERVICIO_A_3_MES

            FROM PROD_REGU_NORMA_DATA..T_NRM_NRIPO_035_HIST

            WHERE ANIO_MES >= '202501'

            GROUP BY 1

        ) c

        ON b.PERIODO = c.PERIODO

        ORDER BY PERIODO ASC
    """

    try:

        df = pd.read_sql(sql, conn)

        return df.to_dict(orient="records")

    except Exception as e:

        logging.error(
            f"Error Query_NRIPO_033_035_DIF: {e}"
        )

        return []

    finally:

        conn.close()


# ============================================================
# NRIPO 034 VS 035
# ============================================================

def Query_nripo_34_35_DIF():

    conn = conectar_netezza()

    if not conn:

        logging.error(
            "No se pudo conectar a Netezza"
        )

        return []

    sql = """
        SELECT

            a.PERIODO AS PERIODO,

            a.NRIPO_034,

            c.LINEAS_A_SERVICIO_A_3_MES,

            (
                a.NRIPO_034
                - c.LINEAS_A_SERVICIO_A_3_MES
            ) AS DIFERENCIA_NRIPO_034

        FROM
        (

            SELECT

                SUBSTRING(ANIO_MES,1,4)
                || TRIM(TO_CHAR(MES,'00'))
                AS PERIODO,

                SUM(LINEAS_SERVICIO)
                AS NRIPO_034

            FROM PROD_REGU_NORMA_DATA..T_NRM_NRIPO_034_HIST

            WHERE ANIO_MES >= '202501'

            GROUP BY 1

        ) a

        FULL OUTER JOIN

        (

            SELECT

                SUBSTRING(ANIO_MES,1,4)
                || LPAD(TRIM(MES),2,'0')
                AS PERIODO,

                SUM(LINEAS_EN_SERVICIO)
                AS LINEAS_EN_SERVICIO,

                SUM(LINEAS_A_SERVICIO_A_3_MES)
                AS LINEAS_A_SERVICIO_A_3_MES

            FROM PROD_REGU_NORMA_DATA..T_NRM_NRIPO_035_HIST

            WHERE ANIO_MES >= '202501'

            GROUP BY 1

        ) c

        ON a.PERIODO = c.PERIODO

        ORDER BY PERIODO ASC
    """

    try:

        df = pd.read_sql(sql, conn)

        return df.to_dict(orient="records")

    except Exception as e:

        logging.error(
            f"Error Query_NRIPO_034_035_DIF: {e}"
        )

        return []

    finally:

        conn.close()


# ============================================================
# PREPARAR DATOS
# ============================================================

def preparar_datos_nripo_035(df):

    if not df:

        return {
            "periodos": [],
            "lineas_servicio": [],
            "lineas_3_meses": [],
            "diferencia": [],
            "porcentaje_diferencia": []
        }

    data = pd.DataFrame(df)

    if data.empty:

        return {
            "periodos": [],
            "lineas_servicio": [],
            "lineas_3_meses": [],
            "diferencia": [],
            "porcentaje_diferencia": []
        }

    data["PERIODO"] = (
        data["PERIODO"]
        .astype(str)
        .str[:6]
    )

    data["PERIODO_FECHA"] = pd.to_datetime(
        data["PERIODO"],
        format="%Y%m",
        errors="coerce"
    )

    data = data.sort_values(
        "PERIODO_FECHA"
    )

    data["LINEAS_EN_SERVICIO"] = pd.to_numeric(
        data["LINEAS_EN_SERVICIO"],
        errors="coerce"
    ).fillna(0)

    data["LINEAS_A_SERVICIO_A_3_MES"] = pd.to_numeric(
        data["LINEAS_A_SERVICIO_A_3_MES"],
        errors="coerce"
    ).fillna(0)

    # Millones
    data["LINEAS_EN_SERVICIO"] = (
        data["LINEAS_EN_SERVICIO"] / 1_000_000
    )

    data["LINEAS_A_SERVICIO_A_3_MES"] = (
        data["LINEAS_A_SERVICIO_A_3_MES"] / 1_000_000
    )

    data["DIFERENCIA"] = (
        data["LINEAS_EN_SERVICIO"]
        - data["LINEAS_A_SERVICIO_A_3_MES"]
    )

    data["PORCENTAJE_DIF"] = (
        data["LINEAS_A_SERVICIO_A_3_MES"]
        .div(
            data["LINEAS_EN_SERVICIO"].replace(0, pd.NA)
        )
        * 100
    )

    data["PORCENTAJE_DIF"] = (
        data["PORCENTAJE_DIF"]
        .fillna(0)
    )

    return {

        "periodos": data[
            "PERIODO_FECHA"
        ].dt.strftime("%Y-%m").tolist(),

        "lineas_servicio": (
            data["LINEAS_EN_SERVICIO"]
            .round(3)
            .tolist()
        ),

        "lineas_3_meses": (
            data["LINEAS_A_SERVICIO_A_3_MES"]
            .round(3)
            .tolist()
        ),

        "diferencia": (
            data["DIFERENCIA"]
            .round(3)
            .tolist()
        ),

        "porcentaje_diferencia": (
            data["PORCENTAJE_DIF"]
            .round(2)
            .tolist()
        )
    }


# ============================================================
# PREPARAR NRIPO 033 VS 035
# ============================================================

def preparar_datos_033_035(df):

    if not df:
        return {
            "periodos": [],
            "nripo_033": [],
            "lineas_035": [],
            "diferencia": [],
            "porcentaje": []
        }

    data = pd.DataFrame(df)

    if data.empty:
        return {
            "periodos": [],
            "nripo_033": [],
            "lineas_035": [],
            "diferencia": [],
            "porcentaje": []
        }

    data["PERIODO"] = (
        data["PERIODO"]
        .astype(str)
        .str[:6]
    )

    data["PERIODO_FECHA"] = pd.to_datetime(
        data["PERIODO"],
        format="%Y%m",
        errors="coerce"
    )

    data = data.sort_values(
        "PERIODO_FECHA"
    )

    columnas = [
        "NRIPO_033",
        "LINEAS_EN_SERVICIO",
        "DIFERENCIA_NRIPO_033"
    ]

    for col in columnas:

        data[col] = pd.to_numeric(
            data[col],
            errors="coerce"
        ).fillna(0)

        data[col] = (
            data[col] / 1_000_000
        )

    data["PORC_DIF"] = (
        data["DIFERENCIA_NRIPO_033"]
        .div(
            data["LINEAS_EN_SERVICIO"].replace(0, pd.NA)
        )
        * 100
    )

    data["PORC_DIF"] = (
        data["PORC_DIF"]
        .fillna(0)
    )

    return {

        "periodos": data[
            "PERIODO_FECHA"
        ].dt.strftime("%Y-%m").tolist(),

        "nripo_033": (
            data["NRIPO_033"]
            .round(3)
            .tolist()
        ),

        "lineas_035": (
            data["LINEAS_EN_SERVICIO"]
            .round(3)
            .tolist()
        ),

        "diferencia": (
            data["DIFERENCIA_NRIPO_033"]
            .round(3)
            .tolist()
        ),

        "porcentaje": (
            data["PORC_DIF"]
            .round(2)
            .tolist()
        )
    }


# ============================================================
# PREPARAR NRIPO 034 VS 035
# ============================================================

def preparar_datos_034_035(df):

    if not df:
        return {
            "periodos": [],
            "nripo_034": [],
            "lineas_3_meses": [],
            "diferencia": [],
            "porcentaje": []
        }

    data = pd.DataFrame(df)

    if data.empty:
        return {
            "periodos": [],
            "nripo_034": [],
            "lineas_3_meses": [],
            "diferencia": [],
            "porcentaje": []
        }

    data["PERIODO"] = (
        data["PERIODO"]
        .astype(str)
        .str[:6]
    )

    data["PERIODO_FECHA"] = pd.to_datetime(
        data["PERIODO"],
        format="%Y%m",
        errors="coerce"
    )

    data = data.sort_values(
        "PERIODO_FECHA"
    )

    columnas = [
        "NRIPO_034",
        "LINEAS_A_SERVICIO_A_3_MES",
        "DIFERENCIA_NRIPO_034"
    ]

    for col in columnas:

        data[col] = pd.to_numeric(
            data[col],
            errors="coerce"
        ).fillna(0)

        data[col] = (
            data[col] / 1_000_000
        )

    data["PORC_DIF"] = (
        data["DIFERENCIA_NRIPO_034"]
        .div(
            data["LINEAS_A_SERVICIO_A_3_MES"].replace(0, pd.NA)
        )
        * 100
    )

    data["PORC_DIF"] = (
        data["PORC_DIF"]
        .fillna(0)
    )

    return {

        "periodos": data[
            "PERIODO_FECHA"
        ].dt.strftime("%Y-%m").tolist(),

        "nripo_034": (
            data["NRIPO_034"]
            .round(3)
            .tolist()
        ),

        "lineas_3_meses": (
            data["LINEAS_A_SERVICIO_A_3_MES"]
            .round(3)
            .tolist()
        ),

        "diferencia": (
            data["DIFERENCIA_NRIPO_034"]
            .round(3)
            .tolist()
        ),

        "porcentaje": (
            data["PORC_DIF"]
            .round(2)
            .tolist()
        )
    }


# ============================================================
# RUTA PRINCIPAL
# ============================================================

@NRIPO_035_bp.route("/NRIPO_035")
def index_mtc():

    try:

        df1 = Query_NRIPO_035_TOT()

        df2 = Query_nripo_33_35_DIF()

        df3 = Query_nripo_34_35_DIF()


        if not df1:

            return (
                "<h2>No hay datos disponibles para NRIPO 035</h2>",
                503
            )


        datos_035 = preparar_datos_nripo_035(
            df1
        )

        datos_033_035 = preparar_datos_033_035(
            df2
        )

        datos_034_035 = preparar_datos_034_035(
            df3
        )


        return render_template(

            "NRIPO_035.html",

            datos_035=json.dumps(
                datos_035
            ),

            datos_033_035=json.dumps(
                datos_033_035
            ),

            datos_034_035=json.dumps(
                datos_034_035
            )

        )


    except Exception as e:

        logging.exception(
            "Error cargando NRIPO 035"
        )

        return (
            "<h2>Error cargando NRIPO 035</h2>",
            500
        )