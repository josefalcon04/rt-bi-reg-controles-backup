from flask import Blueprint, render_template, request, jsonify
from app.db import conectar_netezza
import pandas as pd

devoluciones_bp = Blueprint('devoluciones', __name__)

# 🔥 CACHE SIMPLE
df_cache = None


# =========================
# 📊 OBTENER DATA
# =========================
def obtener_datos():
    global df_cache

    if df_cache is not None:
        return df_cache

    query = """
    SELECT 
    FECHA_PROCESO_D as FECHA_PROCESO,producto,comentario,RESULTADO AS RESULTADO_NC,sum(TOT_CANT_REGISTROS) AS TOT_CANT_REGISTROS,sum(MONTO_SOLES) AS MONTO_SOLES
    FROM CONTROL_MAKO..TMP_JFF_FEATDEVO_2_017
    WHERE 1=1
    AND FECHA_PROCESO_D >= '2026-01-01'
    AND FECHA_PROCESO_D <= (SELECT max(FECHA_PROCESO) FROM PROD_REGU_INH_DATA..T_DEVOLM_OUT_DEVAFECENVIO_S_H)
    GROUP BY 1,2,3,4
    ORDER BY 1 desc,2,3,4
;
    """

    try:
        conn = conectar_netezza()
        df = pd.read_sql(query, conn)
        conn.close()

        if df.empty:
            return df

        # 🔢 Tipos
        df['TOT_CANT_REGISTROS'] = pd.to_numeric(df['TOT_CANT_REGISTROS'], errors='coerce')
        df['MONTO_SOLES'] = pd.to_numeric(df['MONTO_SOLES'], errors='coerce')

        # 📅 Fechas
        df['FECHA_PROCESO'] = pd.to_datetime(df['FECHA_PROCESO'])
        df['FECHA_STR'] = df['FECHA_PROCESO'].dt.strftime('%Y-%m-%d')

        df['year'] = df['FECHA_PROCESO'].dt.year
        df['month'] = df['FECHA_PROCESO'].dt.month
        df['day'] = df['FECHA_PROCESO'].dt.day

        # 🔥 Clasificación OK / NOK
        df['TIPO'] = df['COMENTARIO'].apply(
            lambda x: 'NOK' if 'NOK' in str(x).upper() else 'OK'
        )

        df_cache = df
        return df

    except Exception as e:
        print(f"Error devoluciones: {e}")
        return pd.DataFrame()


# =========================
# 🎯 VISTA
# =========================
@devoluciones_bp.route('/devoluciones')
def dashboard():
    return render_template("devoluciones.html")


# =========================
# 🎯 DATA COMPLETA (combos)
# =========================
@devoluciones_bp.route('/devoluciones/data_full')
def data_full():
    df = obtener_datos()

    if df.empty:
        return jsonify([])

    return jsonify(df.to_dict(orient="records"))


# =========================
# 🎯 FILTROS (AÑO)
# =========================
@devoluciones_bp.route('/devoluciones/filtros')
def filtros():
    df = obtener_datos()

    if df.empty:
        return jsonify({"years": []})

    years = sorted(df['year'].unique().tolist(), reverse=True)

    return jsonify({"years": years})


# =========================
# 🎯 MESES
# =========================
@devoluciones_bp.route('/devoluciones/meses')
def meses():
    df = obtener_datos()

    year = request.args.get("year")

    if year:
        df = df[df['year'] == int(year)]

    months = sorted(df['month'].unique().tolist())

    return jsonify({"months": months})


# =========================
# 🎯 DÍAS
# =========================
@devoluciones_bp.route('/devoluciones/dias')
def dias():
    df = obtener_datos()

    year = request.args.get("year")
    month = request.args.get("month")

    if year:
        df = df[df['year'] == int(year)]

    if month:
        df = df[df['month'] == int(month)]

    days = sorted(df['day'].unique().tolist())

    return jsonify({"days": days})


# =========================
# 📊 DATA PRINCIPAL
# =========================
@devoluciones_bp.route('/devoluciones/data')
def data():
    df = obtener_datos()

    # =========================
    # 🔥 FILTROS
    # =========================
    year = request.args.get("year")
    month = request.args.get("month")
    day = request.args.get("day")

    producto = request.args.get("producto")
    comentario = request.args.get("comentario")
    resultado = request.args.get("resultado")

    if year:
        df = df[df['year'] == int(year)]

    if month:
        df = df[df['month'] == int(month)]

    if day:
        df = df[df['day'] == int(day)]

    if producto:
        df = df[df['PRODUCTO'] == producto]

    if comentario:
        df = df[df['COMENTARIO'] == comentario]

    if resultado:
        df = df[df['RESULTADO_NC'] == resultado]

    # =========================
    # 🔥 SIN DATA
    # =========================
    if df.empty:
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
            "tendencia": []
        })

    # =========================
    # 🔥 KPIs PRO
    # =========================
    total = df['TOT_CANT_REGISTROS'].sum()
    total_monto = df['MONTO_SOLES'].sum()

    ok = df[df['TIPO'] == 'OK']['TOT_CANT_REGISTROS'].sum()
    nok = df[df['TIPO'] == 'NOK']['TOT_CANT_REGISTROS'].sum()

    porc_ok = (ok / total * 100) if total > 0 else 0
    porc_nok = (nok / total * 100) if total > 0 else 0

    kpis = {
        "total_registros": int(total),
        "total_monto": float(total_monto),
        "ok": int(ok),
        "nok": int(nok),
        "porc_ok": round(porc_ok, 2),
        "porc_nok": round(porc_nok, 2)
    }

    # =========================
    # 📊 GRÁFICOS
    # =========================
    pie = df.groupby('PRODUCTO')['TOT_CANT_REGISTROS'].sum().reset_index()

    barras = df.groupby(['FECHA_STR','TIPO'])['TOT_CANT_REGISTROS'].sum().reset_index()

    producto = df.groupby('PRODUCTO')['MONTO_SOLES'].sum().reset_index()

    comentario = df.groupby('COMENTARIO').agg({
                        'TOT_CANT_REGISTROS': 'sum',
                        'MONTO_SOLES': 'sum'
                    }).reset_index()

    resultado = df.groupby('RESULTADO_NC').agg({
                        'TOT_CANT_REGISTROS': 'sum',
                        'MONTO_SOLES': 'sum'
                    }).reset_index()

    tendencia = df.groupby('FECHA_STR')['MONTO_SOLES'].sum().reset_index()

    # =========================
    # 🔥 RETURN FINAL
    # =========================
    return jsonify({
        "kpis": kpis,
        "pie": pie.to_dict(orient="records"),
        "barras": barras.to_dict(orient="records"),
        "producto": producto.to_dict(orient="records"),
        "comentario": comentario.to_dict(orient="records"),
        "resultado": resultado.to_dict(orient="records"),
        "tendencia": tendencia.to_dict(orient="records")
    })