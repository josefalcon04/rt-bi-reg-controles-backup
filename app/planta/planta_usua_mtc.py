import os
import logging
import pandas as pd
from flask import Flask, Blueprint, render_template, send_from_directory
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from app.db import conectar_netezza  # Asegúrate de tener esto definido correctamente

planta_usua_mtc_bp = Blueprint('planta_usua_mtc', __name__)

# ----------- CONSULTAS -----------

def Query_USUA_TOT():
    conn = conectar_netezza()
    if not conn:
        logging.error("No se pudo conectar a Netezza")
        return []

    sql = """
    SELECT 
    TO_CHAR(TRANS_DT,'YYYY-MM') AS PERIODO,
    count(*) AS CANTIDAD
    FROM PROD_REGU_INPUT_DATA..USUA_PLANTA_MTC
    WHERE TPROD1 IN ( 'CF', 'CC', 'CP')
    AND ESTADO1 = 'A'
    AND TO_CHAR(TRANS_DT,'YYYY-MM') >= '2024-01'
    GROUP BY 1
    """

    try:
        df = pd.read_sql(sql, conn)
        return df.to_dict(orient="records")
    except Exception as e:
        logging.error(f"Error Query_USUA_TOT: {e}")
        return []
    finally:
        conn.close()

def Query_USUA_MOD():
    conn = conectar_netezza()
    if not conn:
        logging.error("No se pudo conectar a Netezza")
        return []

    sql = """
    SELECT 
    TO_CHAR(TRANS_DT,'YYYY-MM') AS PERIODO,
    CASE WHEN TPROD1 = 'CP' THEN 'PREPAGO'
    WHEN TPROD1 IN ( 'CF', 'CC') THEN 'POSTPAGO'
    END AS MODALIDAD,
    count(*) AS CANTIDAD
    FROM PROD_REGU_INPUT_DATA..USUA_PLANTA_MTC
    WHERE TPROD1 IN ( 'CF', 'CC', 'CP')
    AND ESTADO1 = 'A'
    AND TO_CHAR(TRANS_DT,'YYYY-MM') >= '2024-01'
    GROUP BY 1,2
    """

    try:
        df = pd.read_sql(sql, conn)
        return df.to_dict(orient="records")
    except Exception as e:
        logging.error(f"Error Query_USUA_MOD: {e}")
        return []
    finally:
        conn.close()

# ----------- GENERADORES DE GRÁFICO -----------

def generar_grafico_USUA_TOT(df, img_name="grafico_usua_tot.png"):
    # --- Preparar DataFrame ---
    df = pd.DataFrame(df)    
    df["PERIODO"] = pd.to_datetime(df["PERIODO"], format="%Y-%m")
    df = df.sort_values("PERIODO")

    # Escalar a millones
    df["CANTIDAD"] = df["CANTIDAD"] / 1_000_000

    # Escala máxima uniforme
    max_y = df["CANTIDAD"].max() * 1.1

    # --- Crear gráfico ---
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(14, 6))

    ax.plot(df["PERIODO"].dt.strftime('%Y-%m'),
            df["CANTIDAD"],
            marker="o",
            linestyle="-",
            linewidth=2.5,
            color="#1f77b4",
            label="Total")

    # --- Etiquetas y título ---
    ax.set_xlabel("Período", fontsize=12, fontweight="bold")
    ax.set_ylabel("Cantidad (Millones)", fontsize=12, fontweight="bold")
    ax.set_title("Cantidad total de activos", fontsize=14, fontweight="bold", pad=20)

    # --- Mostrar valores sobre los puntos ---
    for x, y in zip(df["PERIODO"].dt.strftime('%Y-%m'), df["CANTIDAD"]):
        ax.text(x, y + (max_y * 0.01), f"{y:,.2f}", ha='center', va='bottom', fontsize=9, color="black")

    # --- Ajustes visuales ---
    ax.set_ylim(8, max_y)
    ax.tick_params(axis='x', rotation=0)
    ax.legend(loc="upper left", fontsize=10)
    plt.tight_layout()

    # --- Guardar imagen ---
    img_dir = os.path.join(os.getcwd(), "static/img")
    os.makedirs(img_dir, exist_ok=True)
    img_path = os.path.join(img_dir, img_name)

    plt.savefig(img_path, bbox_inches='tight')
    plt.close()

    return img_name

def generar_grafico_usua_modalidad(df, img_name="grafico_usua_modalidad.png"):
    # --- Validar DataFrame ---
    df = pd.DataFrame(df)
    if df.empty:
        logging.warning("No hay datos para generar el gráfico USUA por modalidad")
        return None

    # --- Normalizar columna PERIODO ---
    df["PERIODO"] = pd.to_datetime(df["PERIODO"].astype(str), format="%Y-%m", errors="coerce")
    df = df.dropna(subset=["PERIODO"])
    df = df.sort_values("PERIODO")

    # --- Escalar a millones ---
    df["CANTIDAD"] = pd.to_numeric(df["CANTIDAD"], errors="coerce").fillna(0) / 1_000_000

    # --- Crear figura ---
    fig, ax = plt.subplots(figsize=(14, 5))
    plt.style.use("seaborn-v0_8-whitegrid")

    # --- Escalas Y dinámicas ---
    max_y = df["CANTIDAD"].max() * 1.1
    min_y = max(0, df["CANTIDAD"].min() * 0.9)

    # --- Dibujar líneas por modalidad ---
    colores = plt.cm.tab10.colors
    for i, modalidad in enumerate(df["MODALIDAD"].unique()):
        df_mod = df[df["MODALIDAD"] == modalidad]

        ax.plot(
            df_mod["PERIODO"].dt.strftime("%Y-%m"),
            df_mod["CANTIDAD"],
            marker="o",
            linestyle="-",
            linewidth=2,
            color=colores[i % len(colores)],
            label=modalidad
        )

        # Etiquetas de valores (solo último punto para no saturar)
        for x, y in zip(df_mod["PERIODO"].dt.strftime("%Y-%m"), df_mod["CANTIDAD"]):
            ax.text(
                x, y + (max_y * 0.02),
                f"{y:.2f}",
                ha="center", va="bottom", fontsize=8, fontweight="bold"
            )

    # --- Configurar ejes ---
    ax.set_xlabel("Período", fontweight="bold")
    ax.set_ylabel("Cantidad (Millones)", fontweight="bold")
    ax.set_ylim(min_y, max_y)
    ax.tick_params(axis="x", rotation=0, labelsize=9)
    ax.tick_params(axis="y", labelsize=9)

    # --- Ejes visibles y limpios ---
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_color("black")
        spine.set_linewidth(0.8)

    # --- Título y leyenda ---
    plt.title("Cantidad total de activos por modalidad", fontweight="bold", pad=15)
    ax.legend(loc="best", fontsize=9, frameon=True)

    plt.tight_layout()

    # --- Guardar imagen ---
    img_dir = os.path.join(os.getcwd(), "static/img")
    os.makedirs(img_dir, exist_ok=True)
    img_path = os.path.join(img_dir, img_name)

    plt.savefig(img_path, bbox_inches="tight", dpi=200)
    plt.close()

    logging.info(f"✅ Gráfico generado correctamente: {img_path}")
    return img_name

# ----------- RUTA PRINCIPAL -----------

@planta_usua_mtc_bp.route('/planta_usua_mtc')
def index_mtc():
    df1 = Query_USUA_TOT()
    df2 = Query_USUA_MOD()

    if not df1 or not df2:
        return "<h2>Error al obtener datos de Netezza</h2>", 503

    img1 = generar_grafico_USUA_TOT(df1)   
    img2 = generar_grafico_usua_modalidad(df2)

    return render_template('planta_usua_mtc.html', img1=img1, img2=img2)

# ----------- RUTA PARA CARGAR IMÁGENES -----------

@planta_usua_mtc_bp.route('/static/img/<filename>')
def imagenes(filename):
    img_dir = os.path.join(os.getcwd(), "static/img")
    return send_from_directory(img_dir, filename)
