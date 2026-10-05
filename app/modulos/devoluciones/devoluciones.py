from flask import Blueprint, render_template, request, jsonify
from app.servicios.bases.connection_manager import conectar_netezza
import pandas as pd
from datetime import timedelta

devoluciones_bp = Blueprint('devoluciones', __name__)

# ============================================================
# CACHE SIMPLE
# ============================================================
df_cache = None


# ============================================================
# UTILIDADES
# ============================================================
def _json_records(df):
    """Convierte DataFrame a registros JSON evitando NaN/NaT."""
    if df is None or df.empty:
        return []
    return df.where(pd.notnull(df), None).to_dict(orient="records")


def _normalizar_producto(valor):
    """
    Normaliza nombres de producto para poder relacionar:
    'Post - pago', 'Post-pago', 'POST PAGO', etc.
    """
    if valor is None:
        return ""
    return (
        str(valor)
        .upper()
        .strip()
        .replace(" ", "")
        .replace("-", "")
        .replace("_", "")
    )


def _producto_020(valor):
    """
    Convierte el producto seleccionado en una condición lógica
    para la tabla 020.
    """
    normalizado = _normalizar_producto(valor)

    if normalizado == "POSTPAGO":
        return "POST"
    if normalizado in ("PREPAGO",):
        return "PRE"

    return None


# ============================================================
# DATA PRINCIPAL - TABLA 017
# ============================================================
def obtener_datos():
    global df_cache

    query = """
    SELECT
        FECHA_PROCESO_D AS FECHA_PROCESO,
        PRODUCTO,
        COMENTARIO,
        RESULTADO AS RESULTADO_NC,
        SUM(TOT_CANT_REGISTROS) AS TOT_CANT_REGISTROS,
        SUM(MONTO_SOLES) AS MONTO_SOLES
    FROM CONTROL_MAKO..TMP_JFF_FEATDEVO_2_017
    WHERE FECHA_PROCESO_D >= '2026-01-01'
      AND FECHA_PROCESO_D <= (
          SELECT MAX(FECHA_PROCESO) + 1
          FROM PROD_REGU_INH_DATA..T_DEVOLM_OUT_DEVAFECENVIO_S_H
      )
    GROUP BY 1,2,3,4
    ORDER BY 1 DESC,2,3,4
    """

    try:
        conn = conectar_netezza()
        df = pd.read_sql(query, conn)
        conn.close()

        df.columns = df.columns.str.upper()

        if df.empty:
            return df

        df["TOT_CANT_REGISTROS"] = pd.to_numeric(
            df["TOT_CANT_REGISTROS"], errors="coerce"
        ).fillna(0)

        df["MONTO_SOLES"] = pd.to_numeric(
            df["MONTO_SOLES"], errors="coerce"
        ).fillna(0)

        df["FECHA_PROCESO"] = pd.to_datetime(
            df["FECHA_PROCESO"], errors="coerce"
        )

        df = df.dropna(subset=["FECHA_PROCESO"])

        df["FECHA_STR"] = df["FECHA_PROCESO"].dt.strftime("%Y-%m-%d")
        df["year"] = df["FECHA_PROCESO"].dt.year
        df["month"] = df["FECHA_PROCESO"].dt.month
        df["day"] = df["FECHA_PROCESO"].dt.day

        df["TIPO"] = df["COMENTARIO"].apply(
            lambda x: "NOK"
            if str(x).upper().strip().startswith("NOK")
            else "OK"
        )

        return df

    except Exception as e:
        print(f"Error devoluciones 017: {e}")
        return pd.DataFrame()


# ============================================================
# RESUMEN POR PRODUCTO - TABLA 017
#
# IMPORTANTE:
#   Este resumen es INDEPENDIENTE de la TABLA 020.
#
#   Query validado:
#       FECHA_PROCESO_D = fecha seleccionada
#       COMENTARIO = 'OK - CANDIDATO'
#
#   POSTPAGO y PREPAGO salen directamente de la TABLA 017.
# ============================================================
def obtener_resumen_producto_017(fecha_seleccionada, producto=None):
    if not fecha_seleccionada:
        return [
            {
                "PRODUCTO": "Post - pago",
                "TIPO_PRODUCTO": "POSTPAGO",
                "REGISTROS": 0,
                "MONTO": 0
            },
            {
                "PRODUCTO": "Pre - pago",
                "TIPO_PRODUCTO": "PREPAGO",
                "REGISTROS": 0,
                "MONTO": 0
            }
        ]

    query = """
    SELECT
        FECHA_PROCESO_D AS FECHA_PROCESO,
        PRODUCTO,
        SUM(TOT_CANT_REGISTROS) AS TOT_CANT_REGISTROS,
        SUM(MONTO_SOLES) AS MONTO_SOLES
    FROM CONTROL_MAKO..TMP_JFF_FEATDEVO_2_017
    WHERE FECHA_PROCESO_D = ?
      AND COMENTARIO = 'OK - CANDIDATO'
    GROUP BY 1,2
    ORDER BY 1;
    """

    try:
        conn = conectar_netezza()

        try:
            df_resumen = pd.read_sql(
                query,
                conn,
                params=[fecha_seleccionada]
            )
        finally:
            conn.close()

        if df_resumen.empty:
            print(
                f"[RESUMEN 017] SIN DATOS para "
                f"FECHA_PROCESO_D = {fecha_seleccionada}"
            )

            return [
                {
                    "PRODUCTO": "Post - pago",
                    "TIPO_PRODUCTO": "POSTPAGO",
                    "REGISTROS": 0,
                    "MONTO": 0
                },
                {
                    "PRODUCTO": "Pre - pago",
                    "TIPO_PRODUCTO": "PREPAGO",
                    "REGISTROS": 0,
                    "MONTO": 0
                }
            ]

        df_resumen.columns = df_resumen.columns.str.upper()

        df_resumen["TOT_CANT_REGISTROS"] = pd.to_numeric(
            df_resumen["TOT_CANT_REGISTROS"],
            errors="coerce"
        ).fillna(0)

        df_resumen["MONTO_SOLES"] = pd.to_numeric(
            df_resumen["MONTO_SOLES"],
            errors="coerce"
        ).fillna(0)

        # Si se seleccionó producto, respetarlo únicamente
        # para las tarjetas del resumen.
        if producto:
            producto_norm = _normalizar_producto(producto)

            if producto_norm == "POSTPAGO":
                df_resumen = df_resumen[
                    df_resumen["PRODUCTO"]
                    .apply(_normalizar_producto) == "POSTPAGO"
                ]
            elif producto_norm == "PREPAGO":
                df_resumen = df_resumen[
                    df_resumen["PRODUCTO"]
                    .apply(_normalizar_producto) == "PREPAGO"
                ]

        resultado = {
            "POSTPAGO": {
                "PRODUCTO": "Post - pago",
                "TIPO_PRODUCTO": "POSTPAGO",
                "REGISTROS": 0,
                "MONTO": 0
            },
            "PREPAGO": {
                "PRODUCTO": "Pre - pago",
                "TIPO_PRODUCTO": "PREPAGO",
                "REGISTROS": 0,
                "MONTO": 0
            }
        }

        for _, row in df_resumen.iterrows():
            producto_nombre = str(
                row["PRODUCTO"]
            ).strip()

            producto_norm = _normalizar_producto(
                producto_nombre
            )

            if producto_norm == "POSTPAGO":
                resultado["POSTPAGO"] = {
                    "PRODUCTO": "Post - pago",
                    "TIPO_PRODUCTO": "POSTPAGO",
                    "REGISTROS": int(
                        row["TOT_CANT_REGISTROS"] or 0
                    ),
                    "MONTO": float(
                        row["MONTO_SOLES"] or 0
                    )
                }

            elif producto_norm == "PREPAGO":
                resultado["PREPAGO"] = {
                    "PRODUCTO": "Pre - pago",
                    "TIPO_PRODUCTO": "PREPAGO",
                    "REGISTROS": int(
                        row["TOT_CANT_REGISTROS"] or 0
                    ),
                    "MONTO": float(
                        row["MONTO_SOLES"] or 0
                    )
                }

        print(
            "[RESUMEN 017] "
            f"fecha={fecha_seleccionada} | "
            f"POSTPAGO={resultado['POSTPAGO']['REGISTROS']} / "
            f"S/ {resultado['POSTPAGO']['MONTO']:.2f} | "
            f"PREPAGO={resultado['PREPAGO']['REGISTROS']} / "
            f"S/ {resultado['PREPAGO']['MONTO']:.2f}"
        )

        return [
            resultado["POSTPAGO"],
            resultado["PREPAGO"]
        ]

    except Exception as e:
        print(
            "[RESUMEN 017] ERROR: "
            f"{type(e).__name__}: {e}"
        )

        return [
            {
                "PRODUCTO": "Post - pago",
                "TIPO_PRODUCTO": "POSTPAGO",
                "REGISTROS": 0,
                "MONTO": 0
            },
            {
                "PRODUCTO": "Pre - pago",
                "TIPO_PRODUCTO": "PREPAGO",
                "REGISTROS": 0,
                "MONTO": 0
            }
        ]


# ============================================================
# PROCESO ABONADOS
#
# Usa exactamente el mismo rango mostrado en el Process Flow:
#   fecha_fin    = fecha seleccionada - 1 día
#   fecha_inicio = fecha_fin - 8 días
#
# Ejemplo:
#   seleccionada 2026-08-31
#   rango        2026-08-22 al 2026-08-30
#
# Fuente:
#   PROD_REGU_INH_DATA..T_DEVOLM_OUT_ABOAFECTADOS_D_H
# ============================================================
def obtener_proceso_abonados(fecha_seleccionada, producto=None):
    if not fecha_seleccionada:
        return {
            "fecha_inicio": None,
            "fecha_fin": None,
            "total": 0,
            "items": []
        }

    try:
        fecha_dashboard = pd.to_datetime(
            fecha_seleccionada,
            errors="coerce"
        )

        if pd.isna(fecha_dashboard):
            return {
                "fecha_inicio": None,
                "fecha_fin": None,
                "total": 0,
                "items": []
            }

        fecha_dashboard = fecha_dashboard.normalize()

        # Mismo rango del Process Flow
        fecha_fin = fecha_dashboard - timedelta(days=1)
        fecha_inicio = fecha_fin - timedelta(days=8)

        fecha_inicio_str = fecha_inicio.strftime("%Y-%m-%d")
        fecha_fin_str = fecha_fin.strftime("%Y-%m-%d")

        query = """
        SELECT
            PRODUCTO,
            COUNT(*) AS CANTIDAD
        FROM PROD_REGU_INH_DATA..T_DEVOLM_OUT_ABOAFECTADOS_D_H
        WHERE CAST(FECHA_PROCESO AS DATE)
              BETWEEN CAST(? AS DATE) AND CAST(? AS DATE)
        """

        params = [
            fecha_inicio_str,
            fecha_fin_str
        ]

        producto_tipo = _normalizar_producto(producto)

        if producto_tipo == "POSTPAGO":
            query += """
                AND UPPER(REPLACE(REPLACE(TRIM(PRODUCTO), ' ', ''), '-', ''))
                    = 'POSTPAGO'
            """
        elif producto_tipo == "PREPAGO":
            query += """
                AND UPPER(REPLACE(REPLACE(TRIM(PRODUCTO), ' ', ''), '-', ''))
                    = 'PREPAGO'
            """

        query += """
        GROUP BY 1
        ORDER BY 1
        """

        print(
            "[ABONADOS] rango consultado = "
            f"{fecha_inicio_str} al {fecha_fin_str}"
        )
        print(
            "[ABONADOS] producto = "
            f"{producto if producto else 'TODOS'}"
        )

        conn = conectar_netezza()

        try:
            df = pd.read_sql(
                query,
                conn,
                params=params
            )
        finally:
            conn.close()

        if df.empty:
            print("[ABONADOS] SIN DATOS")
            return {
                "fecha_inicio": fecha_inicio_str,
                "fecha_fin": fecha_fin_str,
                "total": 0,
                "items": []
            }

        df.columns = df.columns.str.upper()

        df["PRODUCTO"] = (
            df["PRODUCTO"]
            .fillna("")
            .astype(str)
            .str.strip()
        )

        df["CANTIDAD"] = pd.to_numeric(
            df["CANTIDAD"],
            errors="coerce"
        ).fillna(0).astype(int)

        items = _json_records(
            df[["PRODUCTO", "CANTIDAD"]]
        )

        total = int(df["CANTIDAD"].sum())

        print(
            "[ABONADOS] total = "
            f"{total}"
        )
        print(
            "[ABONADOS] detalle = "
            f"{items}"
        )

        return {
            "fecha_inicio": fecha_inicio_str,
            "fecha_fin": fecha_fin_str,
            "total": total,
            "items": items
        }

    except Exception as e:
        print(
            "[ABONADOS] ERROR: "
            f"{type(e).__name__}: {e}"
        )

        return {
            "fecha_inicio": None,
            "fecha_fin": None,
            "total": 0,
            "items": []
        }


# ============================================================
# TABLA 020 - FLUJO DEL PROCESO
#
# REGLA IMPORTANTE:
# Si el usuario selecciona 2026-08-31 en el dashboard,
# la tabla 020 se consulta con FECHA_REPORTE = 2026-08-30.
# ============================================================
def obtener_ciclo_020(fecha_seleccionada, producto=None):
    """
    TABLA 020 - FLUJO DEL PROCESO.

    La fecha de la TABLA 020 corresponde a la fecha seleccionada
    en el dashboard menos 1 día.

    La categorización visual utiliza el DETALLE definido en el
    query solicitado:
      - POSTPAGO: candidatos, próxima semana y cerradas.
      - PREPAGO: semana en curso.
    """

    if not fecha_seleccionada:
        return {
            "fecha_reporte": None,
            "fecha_seleccionada": None,
            "items": [],
            "items_postpago": [],
            "items_prepago": [],
            "productos": [],
            "resumen_producto": []
        }

    try:
        fecha_dashboard = pd.to_datetime(
            fecha_seleccionada,
            errors="coerce"
        )

        if pd.isna(fecha_dashboard):
            return {
                "fecha_reporte": None,
                "fecha_seleccionada": fecha_seleccionada,
                "items": [],
                "items_postpago": [],
                "items_prepago": [],
                "productos": [],
                "resumen_producto": []
            }

        fecha_dashboard = fecha_dashboard.normalize()
        fecha_reporte = fecha_dashboard - timedelta(days=1)

        fecha_reporte_str = fecha_reporte.strftime("%Y-%m-%d")
        fecha_seleccionada_str = fecha_dashboard.strftime("%Y-%m-%d")

        # =====================================================
        # QUERY BASE SOLICITADO POR EL USUARIO.
        # Se agrega MONTO_SOLES para conservar el dato monetario
        # que ya muestra el componente visual.
        # =====================================================
        query = """
        SELECT
            X.PRODUCTO,
            X.DETALLE,
            COUNT(*) AS CANTIDAD,
            SUM(X.MONTO_SOLES) AS MONTO_SOLES
        FROM (
            SELECT
                PRODUCTO,
                CASE
                    WHEN FECHA_REPORTE = FECHA_PROCESO
                         AND FUENTE = 'PROX_N'
                         AND ESTADO_CICLO = 'PROXIMA SEMANA'
                        THEN 'PROXIMA SEMANA (SEMANA)'

                    WHEN FECHA_REPORTE <> FECHA_PROCESO
                         AND FUENTE = 'PROX_N'
                         AND ESTADO_CICLO = 'PROXIMA SEMANA'
                        THEN 'PROXIMA SEMANA (SEMANA ANT.)'

                    WHEN FECHA_REPORTE = FECHA_PROCESO
                         AND FUENTE = 'REJ_S'
                         AND ESTADO_CICLO = 'PROXIMA SEMANA'
                        THEN 'PROXIMA SEMANA (SEMANA)'

                    WHEN FECHA_REPORTE <> FECHA_PROCESO
                         AND FUENTE = 'REJ_S'
                         AND ESTADO_CICLO = 'PROXIMA SEMANA'
                        THEN 'PROXIMA SEMANA (SEMANA ANT.)'

                    WHEN FECHA_REPORTE = FECHA_PROCESO
                         AND FUENTE = 'REJ_X'
                         AND ESTADO_CICLO = 'CERRADO SIN RECIBO'
                        THEN 'CERRADO SIN RECIBO (SEMANA)'

                    WHEN FECHA_REPORTE <> FECHA_PROCESO
                         AND FUENTE = 'REJ_X'
                         AND ESTADO_CICLO = 'CERRADO SIN RECIBO'
                        THEN 'CERRADO SIN RECIBO (SEMANA ANT.)'

                    WHEN FUENTE = 'EXCLUI'
                        THEN 'PROXIMA SEMANA (SEMANA ANT.)'

                    WHEN ESTADO_CICLO = 'AVERIAS SEMANA'
                        THEN 'AVERIAS SEMANA'

                    WHEN ESTADO_CICLO = 'AVERIAS SEMANA ANT.'
                        THEN 'AVERIAS SEMANA ANT.'

                    WHEN ESTADO_CICLO = 'REJECT 1'
                        THEN 'REJECT 1'

                    WHEN ESTADO_CICLO = 'REJECT 2'
                        THEN 'REJECT 2'

                    WHEN ESTADO_CICLO = 'REJECT 3'
                        THEN 'REJECT 3'

                    WHEN ESTADO_CICLO = 'REJECT 4'
                        THEN 'REJECT 4'

                    WHEN PRODUCTO <> 'Post - pago'
                        THEN 'SEMANA EN CURSO'
                END AS DETALLE,

                CASE
                    WHEN PRODUCTO = 'Post - pago'
                        THEN CREDIT_AMOUNT_DET / 100.0
                    ELSE COALESCE(MONTO_DEVOLVER, 0)
                END AS MONTO_SOLES

            FROM PROD_REGU_INH_DATA..T_DEVOLM_REPORTE_SEMANAL_HIST

            WHERE CAST(FECHA_REPORTE AS DATE) = CAST(? AS DATE)
        """

        params = [fecha_reporte_str]

        if producto:
            query += """
                AND PRODUCTO = ?
            """
            params.append(producto)

        query += """
            ) X
        WHERE X.DETALLE IS NOT NULL
        GROUP BY
            X.PRODUCTO,
            X.DETALLE
        """

        conn = conectar_netezza()
        try:
            df_flujo = pd.read_sql(
                query,
                conn,
                params=params
            )
        finally:
            conn.close()

        if df_flujo.empty:
            return {
                "fecha_reporte": fecha_reporte_str,
                "fecha_seleccionada": fecha_seleccionada_str,
                "items": [],
                "items_postpago": [],
                "items_prepago": [],
                "productos": [],
                "resumen_producto": []
            }

        df_flujo.columns = df_flujo.columns.str.upper()

        df_flujo["PRODUCTO"] = (
            df_flujo["PRODUCTO"]
            .fillna("")
            .astype(str)
            .str.strip()
        )

        df_flujo["DETALLE"] = (
            df_flujo["DETALLE"]
            .fillna("")
            .astype(str)
            .str.strip()
        )

        df_flujo["CANTIDAD"] = pd.to_numeric(
            df_flujo["CANTIDAD"],
            errors="coerce"
        ).fillna(0)

        df_flujo["MONTO_SOLES"] = pd.to_numeric(
            df_flujo["MONTO_SOLES"],
            errors="coerce"
        ).fillna(0)

        # Solo se conservan los productos solicitados.
        df_flujo["TIPO_PRODUCTO"] = (
            df_flujo["PRODUCTO"]
            .apply(_normalizar_producto)
            .map({
                "POSTPAGO": "POSTPAGO",
                "PREPAGO": "PREPAGO"
            })
        )

        df_flujo = df_flujo[
            df_flujo["TIPO_PRODUCTO"].isin(["POSTPAGO", "PREPAGO"])
        ].copy()

        # PREPAGO se muestra exclusivamente como SEMANA EN CURSO,
        # tal como se solicitó para la vista.
        df_flujo.loc[
            df_flujo["TIPO_PRODUCTO"] == "PREPAGO",
            "DETALLE"
        ] = "SEMANA EN CURSO"

        # Consolidar nuevamente después de normalizar PREPAGO.
        df_flujo = (
            df_flujo.groupby(
                ["PRODUCTO", "TIPO_PRODUCTO", "DETALLE"],
                as_index=False
            )
            .agg({
                "CANTIDAD": "sum",
                "MONTO_SOLES": "sum"
            })
        )

        orden = {
            "AVERIAS SEMANA": 1,
            "AVERIAS SEMANA ANT.": 2,
            "REJECT 1": 3,
            "REJECT 2": 4,
            "REJECT 3": 5,
            "REJECT 4": 6,
            "PROXIMA SEMANA (SEMANA ANT.)": 7,
            "PROXIMA SEMANA (SEMANA)": 8,
            "CERRADO SIN RECIBO (SEMANA ANT.)": 9,
            "CERRADO SIN RECIBO (SEMANA)": 10,
            "SEMANA EN CURSO": 1
        }

        df_flujo["ORDEN"] = (
            df_flujo["DETALLE"]
            .map(orden)
            .fillna(99)
            .astype(int)
        )

        df_flujo = df_flujo.sort_values(
            ["TIPO_PRODUCTO", "ORDEN", "DETALLE"]
        )

        df_flujo["TOTAL_PRODUCTO"] = (
            df_flujo.groupby("TIPO_PRODUCTO")["CANTIDAD"]
            .transform("sum")
        )

        df_flujo["PORCENTAJE_CICLO"] = 0.0
        mask = df_flujo["TOTAL_PRODUCTO"] > 0
        df_flujo.loc[mask, "PORCENTAJE_CICLO"] = (
            df_flujo.loc[mask, "CANTIDAD"]
            / df_flujo.loc[mask, "TOTAL_PRODUCTO"]
            * 100
        )

        df_flujo["PORCENTAJE_CICLO"] = (
            df_flujo["PORCENTAJE_CICLO"].round(2)
        )
        df_flujo["CANTIDAD"] = (
            df_flujo["CANTIDAD"].round(0).astype(int)
        )
        df_flujo["MONTO_SOLES"] = (
            df_flujo["MONTO_SOLES"].round(2)
        )

        ciclo_postpago = df_flujo[
            df_flujo["TIPO_PRODUCTO"] == "POSTPAGO"
        ].copy()

        ciclo_prepago = df_flujo[
            df_flujo["TIPO_PRODUCTO"] == "PREPAGO"
        ].copy()

        # Mantener el resumen de producto existente para no afectar
        # los KPIs superiores del dashboard.
        query_resumen = """
        SELECT
            PRODUCTO,
            SUM(CANTIDAD) AS CANTIDAD,
            SUM(MONTO_A_DEVOLVER) AS MONTO
        FROM CONTROL_MAKO..TMP_JFF_FEATDEVO_2_020
        WHERE CAST(FECHA_REPORTE AS DATE) = CAST(? AS DATE)
          AND (
                (UPPER(TRIM(PRODUCTO)) LIKE 'POST%'
                 AND ESTADO_CICLO = 'CANDIDATOS')
             OR (UPPER(TRIM(PRODUCTO)) LIKE 'PRE%'
                 AND ESTADO_CICLO = 'PREPAGO')
          )
        """

        params_resumen = [fecha_reporte_str]

        if producto:
            query_resumen += """
                AND PRODUCTO = ?
            """
            params_resumen.append(producto)

        query_resumen += """
        GROUP BY PRODUCTO
        """

        conn = conectar_netezza()
        try:
            df_resumen = pd.read_sql(
                query_resumen,
                conn,
                params=params_resumen
            )
        finally:
            conn.close()

        if not df_resumen.empty:
            df_resumen.columns = df_resumen.columns.str.upper()
            df_resumen["CANTIDAD"] = pd.to_numeric(
                df_resumen["CANTIDAD"], errors="coerce"
            ).fillna(0)
            df_resumen["MONTO"] = pd.to_numeric(
                df_resumen["MONTO"], errors="coerce"
            ).fillna(0)

        post = {
            "PRODUCTO": "Post - pago",
            "TIPO_PRODUCTO": "POSTPAGO",
            "REGISTROS": 0,
            "MONTO": 0
        }

        pre = {
            "PRODUCTO": "Pre - pago",
            "TIPO_PRODUCTO": "PREPAGO",
            "REGISTROS": 0,
            "MONTO": 0
        }

        for _, row in df_resumen.iterrows():
            tipo = _normalizar_producto(row["PRODUCTO"])

            if tipo == "POSTPAGO":
                post["REGISTROS"] = int(row["CANTIDAD"] or 0)
                post["MONTO"] = float(row["MONTO"] or 0)
            elif tipo == "PREPAGO":
                pre["REGISTROS"] = int(row["CANTIDAD"] or 0)
                pre["MONTO"] = float(row["MONTO"] or 0)

        return {
            "fecha_reporte": fecha_reporte_str,
            "fecha_seleccionada": fecha_seleccionada_str,
            "items": _json_records(df_flujo),
            "items_postpago": _json_records(ciclo_postpago),
            "items_prepago": _json_records(ciclo_prepago),
            "productos": sorted(df_flujo["PRODUCTO"].unique().tolist()),
            "resumen_producto": [post, pre]
        }

    except Exception as e:
        print(
            "[TABLA 020 - FLUJO] ERROR: "
            f"{type(e).__name__}: {e}"
        )

        return {
            "fecha_reporte": (
                fecha_reporte_str
                if "fecha_reporte_str" in locals()
                else None
            ),
            "fecha_seleccionada": (
                fecha_dashboard.strftime("%Y-%m-%d")
                if "fecha_dashboard" in locals()
                and not pd.isna(fecha_dashboard)
                else fecha_seleccionada
            ),
            "items": [],
            "items_postpago": [],
            "items_prepago": [],
            "productos": [],
            "resumen_producto": []
        }


# ============================================================
# VISTA
# ============================================================
@devoluciones_bp.route("/devoluciones")
def dashboard():
    return render_template("devoluciones.html")


# ============================================================
# DATA COMPLETA PARA COMBOS
# ============================================================
@devoluciones_bp.route("/devoluciones/data_full")
def data_full():
    df = obtener_datos()

    if df.empty:
        return jsonify([])

    return jsonify(_json_records(df))


# ============================================================
# FILTROS - AÑOS
# ============================================================
@devoluciones_bp.route("/devoluciones/filtros")
def filtros():
    df = obtener_datos()

    if df.empty:
        return jsonify({"years": []})

    years = sorted(
        df["year"].unique().tolist(),
        reverse=True
    )

    return jsonify({"years": years})


# ============================================================
# MESES
# ============================================================
@devoluciones_bp.route("/devoluciones/meses")
def meses():
    df = obtener_datos()

    year = request.args.get("year")

    if year:
        df = df[df["year"] == int(year)]

    months = sorted(
        df["month"].unique().tolist()
    )

    return jsonify({"months": months})


# ============================================================
# DÍAS
# ============================================================
@devoluciones_bp.route("/devoluciones/dias")
def dias():
    df = obtener_datos()

    year = request.args.get("year")
    month = request.args.get("month")

    if year:
        df = df[df["year"] == int(year)]

    if month:
        df = df[df["month"] == int(month)]

    days = sorted(
        df["day"].unique().tolist()
    )

    return jsonify({"days": days})


# ============================================================
# AVERÍAS PROCESADAS EN FARECO - TABLA 019
# La sección utiliza la FECHA_REPORTE seleccionada en el dashboard.
# El filtro de PRODUCTO es opcional y se aplica cuando el usuario
# selecciona POSTPAGO o PREPAGO.
# ============================================================
def obtener_averias_fareco(fecha, producto=None):
    """
    TABLA 019 - AVERÍAS PROCESADAS EN FARECO

    Fuente exclusiva:
      T_DEVOLM_OUT_TOTAL_HIST A
      T_DEVOLM_REPORTE_SEMANAL_HIST B
      TMP_JFF_TMP_CAT_ERR C

    RESULTADO:
      Success / Rejection

    ESTADO_CICLO:
      AVERIAS SEMANA / REJECT 1 / REJECT 2 / REJECT 3 / REJECT 4

    IMPORTANTE:
      El dashboard muestra la fecha seleccionada, pero FARECO se
      consulta con FECHA_REPORTE = fecha seleccionada - 1 día.
      Ejemplo: 31/08/2026 -> 30/08/2026.

      PRODUCTO NO SE USA EN ESTA consulta porque el query entregado
      para TABLA 019 no contiene PRODUCTO.
    """

    if not fecha:
        return []

    try:
        fecha_dashboard = pd.to_datetime(fecha, errors="coerce")

        if pd.isna(fecha_dashboard):
            print(f"[FARECO 019] Fecha inválida: {fecha}")
            return []

        fecha_reporte = (
            fecha_dashboard.normalize() - timedelta(days=1)
        ).strftime("%Y-%m-%d")

        query = """
        SELECT
            B.FECHA_REPORTE,
            A.RESULTADO,
            A.CODMOT,
            B.ESTADO_CICLO,
            C.REASON AS DESCRIPCION,
            SUM(A.CREDIT_AMOUNT) AS MONTO,
            COUNT(*) AS CANTIDAD
        FROM PROD_REGU_INH_DATA..T_DEVOLM_OUT_TOTAL_HIST A
        LEFT JOIN PROD_REGU_INH_DATA..T_DEVOLM_REPORTE_SEMANAL_HIST B
            ON A.ANEXO = B.ANEXO
            AND A.TELEFONO = B.TELEFONO
            AND A.DURINTER = B.DURINTER
            AND B.REPORTE = A.NRO_TICKET
            AND A.ID_OUT = B.ID_OUT
        LEFT JOIN CONTROL_MAKO..TMP_JFF_TMP_CAT_ERR C
            ON A.CODMOT = C.ERROR_ID
        WHERE CAST(B.FECHA_REPORTE AS DATE) = CAST(? AS DATE)
        GROUP BY
            B.FECHA_REPORTE,
            A.RESULTADO,
            A.CODMOT,
            B.ESTADO_CICLO,
            C.REASON
        ORDER BY
            CASE
                WHEN B.ESTADO_CICLO = 'AVERIAS SEMANA' THEN 1
                WHEN B.ESTADO_CICLO = 'REJECT 1' THEN 2
                WHEN B.ESTADO_CICLO = 'REJECT 2' THEN 3
                WHEN B.ESTADO_CICLO = 'REJECT 3' THEN 4
                WHEN B.ESTADO_CICLO = 'REJECT 4' THEN 5
                ELSE 99
            END,
            A.RESULTADO,
            CANTIDAD DESC
        """

        print(
            f"[FARECO 019] fecha seleccionada={fecha_dashboard:%Y-%m-%d} | "
            f"FECHA_REPORTE consultada={fecha_reporte}"
        )

        conn = conectar_netezza()

        try:
            df = pd.read_sql(
                query,
                conn,
                params=[fecha_reporte]
            )
        finally:
            conn.close()

        if df.empty:
            print(
                f"[FARECO 019] SIN DATOS para FECHA_REPORTE={fecha_reporte}"
            )
            return []

        df.columns = df.columns.str.upper()

        df["RESULTADO"] = (
            df["RESULTADO"]
            .fillna("")
            .astype(str)
            .str.strip()
        )

        df["ESTADO_CICLO"] = (
            df["ESTADO_CICLO"]
            .fillna("")
            .astype(str)
            .str.strip()
        )

        df["CODMOT"] = (
            df["CODMOT"]
            .fillna("")
            .astype(str)
            .str.strip()
        )

        df["DESCRIPCION"] = (
            df["DESCRIPCION"]
            .fillna("")
            .astype(str)
            .str.strip()
        )

        df["CANTIDAD"] = pd.to_numeric(
            df["CANTIDAD"],
            errors="coerce"
        ).fillna(0).astype(int)

        df["MONTO"] = pd.to_numeric(
            df["MONTO"],
            errors="coerce"
        ).fillna(0.0)

        # Diagnóstico real de lo que llega desde Netezza.
        print("[FARECO 019] RESULTADOS:")
        print(df.groupby("RESULTADO")["CANTIDAD"].sum().to_dict())

        print("[FARECO 019] CICLOS:")
        print(df.groupby("ESTADO_CICLO")["CANTIDAD"].sum().to_dict())

        return _json_records(df)

    except Exception as e:
        print(
            f"[FARECO 019] ERROR: {type(e).__name__}: {e}"
        )
        return []


# ============================================================
# DATA PRINCIPAL
# ============================================================
@devoluciones_bp.route("/devoluciones/data")
def data():
    df = obtener_datos()

    # ========================================================
    # FILTROS
    # ========================================================
    year = request.args.get("year")
    month = request.args.get("month")
    day = request.args.get("day")

    fecha = None

    if year and month and day:
        fecha = (
            f"{year}-{int(month):02d}-{int(day):02d}"
        )

    producto = request.args.get("producto")
    comentario = request.args.get("comentario")
    resultado = request.args.get("resultado")

    if year:
        df = df[df["year"] == int(year)]

    if month:
        df = df[df["month"] == int(month)]

    if day:
        df = df[df["day"] == int(day)]

    if producto:
        df = df[df["PRODUCTO"] == producto]

    if comentario:
        df = df[df["COMENTARIO"] == comentario]

    if resultado:
        df = df[df["RESULTADO_NC"] == resultado]

    # ========================================================
    # PROCESO ABONADOS
    #
    # Usa exactamente el mismo rango semanal mostrado arriba.
    # ========================================================
    abonados = obtener_proceso_abonados(
        fecha_seleccionada=fecha,
        producto=producto
    )

    # ========================================================
    # TABLA 020
    #
    # Se consulta SIEMPRE con fecha seleccionada - 1 día.
    # ========================================================
    ciclo = obtener_ciclo_020(
        fecha_seleccionada=fecha,
        producto=producto
    )

    # ========================================================
    # RESUMEN POR PRODUCTO -> TABLA 017
    #
    # EXCLUSIVO:
    #   FECHA seleccionada
    #   COMENTARIO = 'OK - CANDIDATO'
    #
    # NO utiliza la TABLA 020.
    # ========================================================
    resumen_producto_017 = obtener_resumen_producto_017(
        fecha_seleccionada=fecha,
        producto=producto
    )

    # Guardamos el resumen de TABLA 020 ANTES de reemplazar
    # el campo que consume el frontend para las tarjetas.
    resumen_020 = ciclo.get(
        "resumen_producto",
        []
    )

    # Las tarjetas del frontend usan este campo.
    # El Process Flow sigue utilizando exclusivamente ciclo["items"].
    ciclo["resumen_producto"] = resumen_producto_017

    # ========================================================
    # SIN DATA 017
    # ========================================================
    if df.empty:
        averias_fareco = (
            obtener_averias_fareco(fecha, producto)
            if fecha
            else []
        )

        return jsonify({
            "kpis": {
                "total_registros": 0,
                "total_monto": 0,
                "ok": 0,
                "nok": 0,
                "porc_ok": 0,
                "porc_nok": 0
            },
            "pie": [],
            "barras": [],
            "producto": [],
            "comentario": [],
            "resultado": [],
            "tendencia": [],
            "pie_nok": [],
            "averias_fareco": averias_fareco,
            "abonados": abonados,
            "ciclo": ciclo
        })

    # ========================================================
    # KPIs
    # ========================================================
    total = df["TOT_CANT_REGISTROS"].sum()
    total_monto = df["MONTO_SOLES"].sum()

    ok = df[
        df["TIPO"] == "OK"
    ]["TOT_CANT_REGISTROS"].sum()

    nok = df[
        df["TIPO"] == "NOK"
    ]["TOT_CANT_REGISTROS"].sum()

    porc_ok = (
        ok / total * 100
        if total > 0
        else 0
    )

    porc_nok = (
        nok / total * 100
        if total > 0
        else 0
    )

    # ========================================================
    # CANDIDATOS POSTPAGO / PREPAGO
    #
    # Se toma desde TABLA 020 para que coincida con
    # el flujo que se muestra en pantalla.
    # ========================================================
    # Los KPIs de candidatos mantienen su fuente TABLA 020.
    # El cambio a 017 aplica únicamente al resumen visual por producto.

    candidatos_postpago = 0
    candidatos_prepago = 0
    monto_postpago = 0
    monto_prepago = 0

    for item in resumen_020:
        tipo = str(
            item.get("TIPO_PRODUCTO", "")
        ).upper()

        cantidad = float(
            item.get("REGISTROS", 0) or 0
        )

        monto = float(
            item.get("MONTO", 0) or 0
        )

        if tipo == "POSTPAGO":
            candidatos_postpago += cantidad
            monto_postpago += monto

        elif tipo == "PREPAGO":
            candidatos_prepago += cantidad
            monto_prepago += monto

    # ========================================================
    # KPIs
    # ========================================================
    kpis = {
        "total_registros": int(total),
        "total_monto": float(total_monto),
        "ok": int(ok),
        "nok": int(nok),
        "porc_ok": round(porc_ok, 2),
        "porc_nok": round(porc_nok, 2),

        # Datos 020
        "candidatos_postpago": int(candidatos_postpago),
        "candidatos_prepago": int(candidatos_prepago),
        "monto_postpago": float(monto_postpago),
        "monto_prepago": float(monto_prepago)
    }

    # ========================================================
    # GRÁFICOS
    # ========================================================
    df_ok = df[
        df["TIPO"] == "OK"
    ].copy()

    pie = (
        df_ok.groupby("PRODUCTO")[
            "TOT_CANT_REGISTROS"
        ]
        .sum()
        .reset_index()
    )

    df_nok = df[
        df["TIPO"] == "NOK"
    ].copy()

    pie_nok = (
        df_nok.groupby("PRODUCTO")[
            "TOT_CANT_REGISTROS"
        ]
        .sum()
        .reset_index()
    )

    barras = (
        df.groupby(
            ["FECHA_STR", "TIPO"]
        )["TOT_CANT_REGISTROS"]
        .sum()
        .reset_index()
    )

    producto_data = (
        df.groupby("PRODUCTO")
        .agg({
            "TOT_CANT_REGISTROS": "sum",
            "MONTO_SOLES": "sum"
        })
        .reset_index()
    )

    comentario_data = (
        df.groupby("COMENTARIO")
        .agg({
            "TOT_CANT_REGISTROS": "sum",
            "MONTO_SOLES": "sum"
        })
        .reset_index()
    )

    resultado_data = (
        df.groupby("RESULTADO_NC")
        .agg({
            "TOT_CANT_REGISTROS": "sum",
            "MONTO_SOLES": "sum"
        })
        .reset_index()
    )

    tendencia = (
        df.groupby("FECHA_STR")
        .agg({
            "TOT_CANT_REGISTROS": "sum",
            "MONTO_SOLES": "sum"
        })
        .reset_index()
    )

    # ========================================================
    # AVERÍAS PROCESADAS EN FARECO - TABLA 019
    # ========================================================
    averias_fareco = []

    if fecha:
        averias_fareco = obtener_averias_fareco(fecha, producto)

    # ========================================================
    # RESPUESTA FINAL
    # ========================================================
    return jsonify({
        "kpis": kpis,
        "pie": _json_records(pie),
        "barras": _json_records(barras),
        "producto": _json_records(producto_data),
        "comentario": _json_records(comentario_data),
        "resultado": _json_records(resultado_data),
        "tendencia": _json_records(tendencia),
        "pie_nok": _json_records(pie_nok),
        "averias_fareco": averias_fareco,
        "abonados": abonados,

        # TABLA 020
        "ciclo": ciclo
    })
