import os
import logging
import pandas as pd
from flask import Blueprint, render_template, send_from_directory

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from app.db import conectar_netezza


planta_tisa_bp = Blueprint('planta_tisa', __name__)


# ----------- CONSULTAS -----------

def Query_TISA_TOT():
    conn = conectar_netezza()

    if not conn:
        logging.error("No se pudo conectar a Netezza")
        return []

    sql = """
    SELECT 
        PERIODO,
        COUNT(*) AS CANTIDAD
    FROM PROD_REGU_INPUT_DATA..T_INP_PLT_TISA
    WHERE TPROD1 IN ('CF', 'CC', 'CP')
    AND ESTADO1 IN ('A')
    AND PERIODO >= '202401'
    GROUP BY 1
    ORDER BY 1
    """

    try:
        df = pd.read_sql(sql, conn)
        return df.to_dict(orient="records")

    except Exception as e:
        logging.error(f"Error Query_TISA_TOT: {e}")
        return []

    finally:
        conn.close()


def Query_TISA_MOD():
    conn = conectar_netezza()

    if not conn:
        logging.error("No se pudo conectar a Netezza")
        return []

    sql = """
    SELECT 
        PERIODO,
        CASE 
            WHEN TPROD1 = 'CP' THEN 'PREPAGO'
            WHEN TPROD1 IN ('CF', 'CC') THEN 'POSTPAGO'
        END AS MODALIDAD,
        COUNT(*) AS CANTIDAD
    FROM PROD_REGU_INPUT_DATA..T_INP_PLT_TISA
    WHERE TPROD1 IN ('CF', 'CC', 'CP')
    AND ESTADO1 IN ('A')
    AND PERIODO >= '202401'
    GROUP BY 1,2
    ORDER BY 1,2
    """

    try:
        df = pd.read_sql(sql, conn)
        return df.to_dict(orient="records")

    except Exception as e:
        logging.error(f"Error Query_TISA_MOD: {e}")
        return []

    finally:
        conn.close()


# ----------- GENERADORES DE GRÁFICO -----------

def generar_grafico_TISA_TOT(
    datos,
    img_name="grafico_tisa_tot.png"
):
    df = pd.DataFrame(datos)

    if df.empty:
        logging.warning("No hay datos para generar gráfico TISA total")
        return None

    df["PERIODO"] = pd.to_datetime(
        df["PERIODO"].astype(str) + "01",
        format="%Y%m%d",
        errors="coerce"
    )

    df["CANTIDAD"] = pd.to_numeric(
        df["CANTIDAD"],
        errors="coerce"
    ).fillna(0)

    df = df.dropna(subset=["PERIODO"])
    df = df.sort_values("PERIODO")

    # Escalar a millones
    df["CANTIDAD"] = df["CANTIDAD"] / 1_000_000

    # Escala dinámica proporcional
    min_y = df["CANTIDAD"].min() * 0.98
    max_y = df["CANTIDAD"].max() * 1.05

    if min_y == max_y:
        min_y = min_y * 0.95
        max_y = max_y * 1.05

    plt.style.use("seaborn-v0_8-whitegrid")

    fig, ax = plt.subplots(
        figsize=(14, 6),
        constrained_layout=True
    )

    x_labels = df["PERIODO"].dt.strftime("%Y-%m")

    ax.plot(
        x_labels,
        df["CANTIDAD"],
        marker="o",
        linestyle="-",
        linewidth=2.5,
        color="#1f77b4",
        label="Total"
    )

    ax.set_title(
        "Cantidad total de activos",
        fontsize=14,
        fontweight="bold",
        pad=20
    )

    ax.set_xlabel(
        "Período",
        fontsize=12,
        fontweight="bold"
    )

    ax.set_ylabel(
        "Cantidad (Millones)",
        fontsize=12,
        fontweight="bold"
    )

    ax.set_ylim(min_y, max_y)

    for x, y in zip(x_labels, df["CANTIDAD"]):
        ax.text(
            x,
            y + ((max_y - min_y) * 0.02),
            f"{y:,.2f}",
            ha="center",
            va="bottom",
            fontsize=9,
            color="black"
        )

    ax.tick_params(
        axis="x",
        rotation=0,
        labelsize=9
    )

    ax.tick_params(
        axis="y",
        labelsize=9
    )

    ax.legend(
        loc="upper left",
        fontsize=10,
        frameon=True
    )

    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_color("#444")
        spine.set_linewidth(0.8)

    img_dir = os.path.join(os.getcwd(), "static/img")
    os.makedirs(img_dir, exist_ok=True)

    img_path = os.path.join(img_dir, img_name)

    plt.savefig(
        img_path,
        bbox_inches="tight",
        dpi=200
    )

    plt.close()

    logging.info(f"✅ Gráfico generado correctamente: {img_path}")

    return img_name


def generar_grafico_tisa_modalidad(
    datos,
    img_name="grafico_tisa_modalidad.png"
):
    df = pd.DataFrame(datos)

    if df.empty:
        logging.warning("No hay datos para generar gráfico TISA por modalidad")
        return None

    df["PERIODO"] = pd.to_datetime(
        df["PERIODO"].astype(str) + "01",
        format="%Y%m%d",
        errors="coerce"
    )

    df["CANTIDAD"] = pd.to_numeric(
        df["CANTIDAD"],
        errors="coerce"
    ).fillna(0)

    df = df.dropna(subset=["PERIODO"])
    df = df.sort_values("PERIODO")

    df["CANTIDAD"] = df["CANTIDAD"] / 1_000_000

    min_y = df["CANTIDAD"].min() * 0.98
    max_y = df["CANTIDAD"].max() * 1.05

    if min_y == max_y:
        min_y = min_y * 0.95
        max_y = max_y * 1.05

    plt.style.use("seaborn-v0_8-whitegrid")

    fig, ax = plt.subplots(
        figsize=(14, 5),
        constrained_layout=True
    )

    colores = plt.cm.tab10.colors

    for i, modalidad in enumerate(df["MODALIDAD"].dropna().unique()):
        df_mod = df[df["MODALIDAD"] == modalidad]

        x_labels = df_mod["PERIODO"].dt.strftime("%Y-%m")

        ax.plot(
            x_labels,
            df_mod["CANTIDAD"],
            marker="o",
            linestyle="-",
            linewidth=2.2,
            color=colores[i % len(colores)],
            label=modalidad
        )

        for x, y in zip(x_labels, df_mod["CANTIDAD"]):
            ax.text(
                x,
                y + ((max_y - min_y) * 0.02),
                f"{y:.2f}",
                ha="center",
                va="bottom",
                fontsize=8,
                fontweight="bold"
            )

    ax.set_title(
        "Cantidad total de activos por modalidad",
        fontsize=14,
        fontweight="bold",
        pad=15
    )

    ax.set_xlabel(
        "Período",
        fontweight="bold"
    )

    ax.set_ylabel(
        "Cantidad (Millones)",
        fontweight="bold"
    )

    ax.set_ylim(min_y, max_y)

    ax.tick_params(
        axis="x",
        rotation=0,
        labelsize=9
    )

    ax.tick_params(
        axis="y",
        labelsize=9
    )

    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_color("#444")
        spine.set_linewidth(0.8)

    ax.legend(
        loc="best",
        fontsize=9,
        frameon=True
    )

    img_dir = os.path.join(os.getcwd(), "static/img")
    os.makedirs(img_dir, exist_ok=True)

    img_path = os.path.join(img_dir, img_name)

    plt.savefig(
        img_path,
        bbox_inches="tight",
        dpi=200
    )

    plt.close()

    logging.info(f"✅ Gráfico generado correctamente: {img_path}")

    return img_name


# ----------- RUTA PRINCIPAL -----------

@planta_tisa_bp.route('/planta_tisa')
def index_mtc():
    df1 = Query_TISA_TOT()
    df2 = Query_TISA_MOD()

    if not df1 or not df2:
        return "<h2>Error al obtener datos de Netezza</h2>", 503

    img1 = generar_grafico_TISA_TOT(df1)
    img2 = generar_grafico_tisa_modalidad(df2)

    return render_template(
        'planta_tisa.html',
        img1=img1,
        img2=img2
    )


# ----------- RUTA PARA CARGAR IMÁGENES -----------

@planta_tisa_bp.route('/static/img/<filename>')
def imagenes(filename):
    img_dir = os.path.join(os.getcwd(), "static/img")
    return send_from_directory(img_dir, filename)