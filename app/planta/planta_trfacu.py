import os
import logging
import pandas as pd
from flask import Flask, Blueprint, render_template, send_from_directory
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from app.db import conectar_netezza  # Asegúrate de tener esto definido correctamente
import matplotlib.ticker as mtick

planta_trfacu_bp = Blueprint('planta_trfacu', __name__)

# ----------- CONSULTAS -----------

def Query_TRFACUV1_TOT():
    conn = conectar_netezza()
    if not conn:
        logging.error("No se pudo conectar a Netezza")
        return []

    sql = """
    SELECT PERIODO,
    CASE WHEN EVENTOS = '100' THEN 'TRAFICO ENTRATE + MOVIVOX'
        WHEN EVENTOS = '010' THEN 'TRAFICO SALIENTE'
        WHEN EVENTOS = '001' THEN 'DATOS'
        END AS EVENTOS,
    CANTIDAD
    FROM CONTROL_MAKO..T_CTRL_TRAFICO_ACUMULADO
    WHERE TABLA  LIKE 'TRF_ANT%'
    AND PERIODO >= '202501'
    ORDER BY 1 ASC ,3 desc
    """

    try:
        df = pd.read_sql(sql, conn)
        return df.to_dict(orient="records")
    except Exception as e:
        logging.error(f"Error Query_TRFACUV1_TOT: {e}")
        return []
    finally:
        conn.close()

def Query_TRFACUV2_TOT():
    conn = conectar_netezza()
    if not conn:
        logging.error("No se pudo conectar a Netezza")
        return []

    sql = """
    SELECT PERIODO,
    CASE WHEN EVENTOS = '100000' THEN 'TRAFICO ENTRATE'
        WHEN EVENTOS = '010000' THEN 'TRAFICO SALIENTE'
        WHEN EVENTOS = '001000' THEN 'DATOS'
        WHEN EVENTOS = '000100' THEN 'SMS ENTRANTE'
        WHEN EVENTOS = '000010' THEN 'SMS SALIENTE'
        WHEN EVENTOS = '000001' THEN 'MOVIVOX'
        END AS EVENTOS,
    CANTIDAD
    FROM CONTROL_MAKO..T_CTRL_TRAFICO_ACUMULADO
    WHERE TABLA  NOT LIKE 'TRF_ANT%'
    AND PERIODO >= '202501'
    ORDER BY 1 ASC ,3 desc
    """

    try:
        df = pd.read_sql(sql, conn)
        return df.to_dict(orient="records")
    except Exception as e:
        logging.error(f"Error Query_TRFACUV2_TOT: {e}")
        return []
    finally:
        conn.close()

# ----------- GENERADORES DE GRÁFICO -----------
def convertir_cantidad_a_millones(df, columnas):
    """Convierte una o varias columnas numéricas a millones."""
    if isinstance(columnas, str):
        columnas = [columnas]
    for col in columnas:
        if col in df.columns:
            try:
                df[col] = pd.to_numeric(df[col], errors="coerce") / 1_000_000
            except Exception as e:
                logging.error(f"Error al convertir columna '{col}': {e}")
        else:
            logging.warning(f"Columna '{col}' no encontrada en el DataFrame")
    return df

def generar_grafico_trfacuv1(df, img_name="grafico_trfacuv1.png"):
    # --- Validar DataFrame ---
    df = pd.DataFrame(df)
    if df.empty:
        logging.warning("No hay datos para generar el gráfico TRFACU V1")
        return None

    # --- Normalizar columna PERIODO ---
    df["PERIODO"] = df["PERIODO"].astype(str)
    if df["PERIODO"].str.match(r"^\d{6}$").all():
        df["PERIODO"] = pd.to_datetime(df["PERIODO"], format="%Y%m")
    else:
        df["PERIODO"] = pd.to_datetime(df["PERIODO"], errors="coerce")

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
    for i, modalidad in enumerate(df["EVENTOS"].unique()):
        df_mod = df[df["EVENTOS"] == modalidad]

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
    plt.title("Cantidad total de eventos por periodo", fontweight="bold", pad=15)
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

def generar_grafico_trfacuv2(df, img_name="grafico_trfacuv2.png"):
    # --- Validar DataFrame ---
    df = pd.DataFrame(df)
    if df.empty:
        logging.warning("No hay datos para generar el gráfico TRFACU V2")
        return None

    # --- Normalizar columna PERIODO ---
    df["PERIODO"] = df["PERIODO"].astype(str)
    if df["PERIODO"].str.match(r"^\d{6}$").all():
        df["PERIODO"] = pd.to_datetime(df["PERIODO"], format="%Y%m")
    else:
        df["PERIODO"] = pd.to_datetime(df["PERIODO"], errors="coerce")

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
    for i, modalidad in enumerate(df["EVENTOS"].unique()):
        df_mod = df[df["EVENTOS"] == modalidad]

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
    plt.title("Cantidad total de eventos por periodo", fontweight="bold", pad=15)
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

@planta_trfacu_bp.route('/planta_trfacu')
def index_mtc():
    df1 = Query_TRFACUV1_TOT()
    df2 = Query_TRFACUV2_TOT()

    if not df1 or not df2:
        return "<h2>Error al obtener datos de Netezza</h2>", 503

    img1 = generar_grafico_trfacuv1(df1)
    img2 = generar_grafico_trfacuv2(df2)


    return render_template('planta_trfacu.html', img1=img1, img2=img2)

# ----------- RUTA PARA CARGAR IMÁGENES -----------

@planta_trfacu_bp.route('/static/img/<filename>')
def imagenes(filename):
    img_dir = os.path.join(os.getcwd(), "static/img")
    return send_from_directory(img_dir, filename)
