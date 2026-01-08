import os
import logging
import pandas as pd
from flask import Flask, Blueprint, render_template, send_from_directory
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from app.db import conectar_netezza  # Asegúrate de tener esto definido correctamente
import matplotlib.ticker as mtick

NRIPO_035_bp = Blueprint('NRIPO_035', __name__)

# ----------- CONSULTAS -----------

def Query_NRIPO_035_TOT():
    conn = conectar_netezza()
    if not conn:
        logging.error("No se pudo conectar a Netezza")
        return []

    sql = """
    SELECT 
    DISTINCT SUBSTRING( ANIO_MES,1,4) ||LPAD(TRIM(MES), 2, '0') AS PERIODO  
    ,sum(LINEAS_EN_SERVICIO) AS LINEAS_EN_SERVICIO, sum(LINEAS_A_SERVICIO_A_3_MES) AS LINEAS_A_SERVICIO_A_3_MES 
    FROM PROD_REGU_NORMA_DATA..T_NRM_NRIPO_035_HIST
    WHERE ANIO_MES >= '202401'
    GROUP BY 1
    ORDER BY 1 asc
    """

    try:
        df = pd.read_sql(sql, conn)
        return df.to_dict(orient="records")
    except Exception as e:
        logging.error(f"Error Query_NRIPO_035_TOT: {e}")
        return []
    finally:
        conn.close()

def Query_nripo_33_35_DIF():
    conn = conectar_netezza()
    if not conn:
        logging.error("No se pudo conectar a Netezza")
        return []

    sql = """
        SELECT 
            b.PERIODO AS PERIODO,
            b.NRIPO_033,
            c.LINEAS_EN_SERVICIO,
            (b.NRIPO_033 - c.LINEAS_EN_SERVICIO) AS DIFERENCIA_NRIPO_033
        FROM
        (
            -- NRIPO_033
            SELECT 
                SUBSTRING(ANIO_MES,1,4) || TRIM(TO_CHAR(MES,'00')) AS PERIODO,
                SUM(LINEAS_SERVICIO) AS NRIPO_033
            FROM PROD_REGU_NORMA_DATA..T_NRM_NRIPO_033_HIST
            WHERE ANIO_MES >= '202401'
            GROUP BY 1
        ) b
        FULL OUTER JOIN
        (
            -- NRIPO_035
            SELECT 
                SUBSTRING(ANIO_MES,1,4) || LPAD(TRIM(MES), 2, '0') AS PERIODO,
                SUM(LINEAS_EN_SERVICIO) AS LINEAS_EN_SERVICIO,
                SUM(LINEAS_A_SERVICIO_A_3_MES) AS LINEAS_A_SERVICIO_A_3_MES
            FROM PROD_REGU_NORMA_DATA..T_NRM_NRIPO_035_HIST
            WHERE ANIO_MES >= '202401'
            GROUP BY 1
        ) c
        ON b.PERIODO = c.PERIODO
        ORDER BY PERIODO ASC;
    """

    try:
        df = pd.read_sql(sql, conn)
        return df.to_dict(orient="records")
    except Exception as e:
        logging.error(f"Error Query_NRIPO_033_035_DIF: {e}")
        return []
    finally:
        conn.close()

def Query_nripo_34_35_DIF():
    conn = conectar_netezza()
    if not conn:
        logging.error("No se pudo conectar a Netezza")
        return []

    sql = """
        SELECT 
            a.PERIODO AS PERIODO,            
            a.NRIPO_034,
            c.LINEAS_A_SERVICIO_A_3_MES,
            (a.NRIPO_034 - c.LINEAS_A_SERVICIO_A_3_MES) AS DIFERENCIA_NRIPO_034
        FROM
        (
            -- NRIPO_034
            SELECT 
                SUBSTRING(ANIO_MES,1,4) || TRIM(TO_CHAR(MES,'00')) AS PERIODO,
                SUM(LINEAS_SERVICIO) AS NRIPO_034
            FROM PROD_REGU_NORMA_DATA..T_NRM_NRIPO_034_HIST
            WHERE ANIO_MES >= '202401'
            GROUP BY 1
        ) a
        FULL OUTER JOIN        
        (
            -- NRIPO_035
            SELECT 
                SUBSTRING(ANIO_MES,1,4) || LPAD(TRIM(MES), 2, '0') AS PERIODO,
                SUM(LINEAS_EN_SERVICIO) AS LINEAS_EN_SERVICIO,
                SUM(LINEAS_A_SERVICIO_A_3_MES) AS LINEAS_A_SERVICIO_A_3_MES
            FROM PROD_REGU_NORMA_DATA..T_NRM_NRIPO_035_HIST
            WHERE ANIO_MES >= '202401'
            GROUP BY 1
        ) c
        ON a.PERIODO = c.PERIODO
        ORDER BY PERIODO ASC;   
    """

    try:
        df = pd.read_sql(sql, conn)
        return df.to_dict(orient="records")
    except Exception as e:
        logging.error(f"Error Query_NRIPO_034_035_DIF: {e}")
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

def generar_grafico_nripo_035_TOT(df, img_name="grafico_nripo_035_tot.png"):

    df = pd.DataFrame(df)
    if df.empty:
        logging.warning("No hay datos para generar el gráfico NRIPO 035 TOT")
        return None

    # --- Normalizar y ordenar período ---
    df["PERIODO"] = df["PERIODO"].astype(str).str[:6]
    df["PERIODO"] = pd.to_datetime(df["PERIODO"], format="%Y%m")
    df = df.sort_values("PERIODO")

    # --- Escalar a millones ---
    columnas = ["LINEAS_EN_SERVICIO", "LINEAS_A_SERVICIO_A_3_MES"]
    for col in columnas:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0) / 1_000_000

    # --- Calcular diferencia y porcentaje ---
    df["DIFERENCIA"] = df["LINEAS_EN_SERVICIO"] - df["LINEAS_A_SERVICIO_A_3_MES"]
    df["TOTAL"] = df["LINEAS_EN_SERVICIO"] + df["LINEAS_A_SERVICIO_A_3_MES"]
    df["PORCENTAJE_DIF"] = (df["LINEAS_A_SERVICIO_A_3_MES"] /df["LINEAS_EN_SERVICIO"] ) * 100

    # --- Estilo general del gráfico ---
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax1 = plt.subplots(figsize=(14, 6))
    fig.patch.set_facecolor("#f8f9fa")
    fig.patch.set_edgecolor("black")  # borde exterior
    fig.patch.set_linewidth(3)        # grosor del borde

    # --- Líneas principales ---
    ax1.plot(df["PERIODO"], df["LINEAS_EN_SERVICIO"], marker="o", linewidth=2.5,
             color="#007bff", label="Líneas en Servicio")
    ax1.plot(df["PERIODO"], df["LINEAS_A_SERVICIO_A_3_MES"], marker="s", linewidth=2.5,
             color="#ff8c00", label="Líneas a Servicio a 3 Meses")

    # Etiquetas sobre las líneas
    for _, row in df.iterrows():
        ax1.text(row["PERIODO"], row["LINEAS_EN_SERVICIO"], f"{row['LINEAS_EN_SERVICIO']:.1f}",
                 ha="center", va="bottom", fontsize=8, color="#004085", fontweight="bold")
        ax1.text(row["PERIODO"], row["LINEAS_A_SERVICIO_A_3_MES"], f"{row['LINEAS_A_SERVICIO_A_3_MES']:.1f}",
                 ha="center", va="bottom", fontsize=8, color="#cc7000", fontweight="bold")

    # --- Configuración eje izquierdo ---
    ax1.set_xlabel("Período", fontweight="bold")
    ax1.set_ylabel("Cantidad (Millones)", fontweight="bold", color="#212529")
    ax1.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"{x:.1f}M"))
    ax1.tick_params(axis="x", rotation=0)
    ax1.grid(True, linestyle="--", alpha=0.3)

    # --- Eje derecho: % de diferencia ---
    ax2 = ax1.twinx()
    colores = ["#28a745" if v >= 0 else "#dc3545" for v in df["DIFERENCIA"]]
    bars = ax2.bar(df["PERIODO"], df["PORCENTAJE_DIF"], color=colores, alpha=0.3, width=20,
                   label="% Diferencia")
    ax2.set_ylabel("Diferencia porcentual (%)", fontweight="bold", color="#212529")
    ax2.yaxis.set_major_formatter(mtick.PercentFormatter())

    # Etiquetas en las barras
    for rect, pct in zip(bars, df["PORCENTAJE_DIF"]):
        height = rect.get_height()
        ax2.text(rect.get_x() + rect.get_width() / 2, height,
                 f"{pct:.1f}%", ha="center",
                 va="bottom" if pct >= 0 else "top",
                 fontsize=8, color="#212529", fontweight="bold")

    # --- Título y leyenda ---
    plt.title("Comparativa Líneas en Servicio vs Líneas en Servicio a 3 Meses",
              fontsize=13, fontweight="bold", color="#343a40")
    lines_labels = ax1.get_legend_handles_labels()
    bars_labels = ax2.get_legend_handles_labels()
    ax1.legend(
        lines_labels[0] + bars_labels[0],
        lines_labels[1] + bars_labels[1],
        loc="center left",
        bbox_to_anchor=(1.15, 0.5),  # mueve la leyenda más a la derecha
        fontsize=9,
        frameon=True,
        fancybox=True,
        shadow=False,
        borderpad=1
    )

    plt.tight_layout(rect=[0, 0, 0.85, 1])  # ajusta espacio para la leyenda fuera

    # --- Guardar imagen ---
    img_dir = os.path.join(os.getcwd(), "static/img")
    os.makedirs(img_dir, exist_ok=True)
    img_path = os.path.join(img_dir, img_name)
    plt.savefig(img_path, bbox_inches="tight", dpi=150)
    plt.close()

    logging.info(f"Gráfico generado: {img_path}")
    return img_name


def generar_grafico_nripo_033_vs_035(df, img_name="grafico_nripo_033_vs_035.png"):
    import pandas as pd
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mtick
    import os, logging

    df = pd.DataFrame(df)
    if df.empty:
        logging.warning("No hay datos para generar el gráfico NRIPO 033 vs 035")
        return None

    # --- Normalizar y ordenar período ---
    df["PERIODO"] = df["PERIODO"].astype(str).str[:6]
    df["PERIODO"] = pd.to_datetime(df["PERIODO"], format="%Y%m")
    df = df.sort_values("PERIODO")

    # --- Convertir columnas numéricas ---
    for col in ["NRIPO_033", "LINEAS_EN_SERVICIO", "DIFERENCIA_NRIPO_033"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # --- Escalar a millones ---
    df["NRIPO_033"] = df["NRIPO_033"] / 1_000_000
    df["LINEAS_EN_SERVICIO"] = df["LINEAS_EN_SERVICIO"] / 1_000_000
    df["DIFERENCIA_NRIPO_033"] = df["DIFERENCIA_NRIPO_033"] / 1_000_000

    # --- Calcular diferencia porcentual ---
    df["PORC_DIF"] = (df["DIFERENCIA_NRIPO_033"] / df["LINEAS_EN_SERVICIO"]) * 100

    # --- Estilo general ---
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax1 = plt.subplots(figsize=(12, 6))
    fig.patch.set_facecolor("#f8f9fa")
    fig.patch.set_edgecolor("black")
    fig.patch.set_linewidth(3)

    # --- Líneas principales ---
    ax1.plot(df["PERIODO"], df["NRIPO_033"], marker="o", linewidth=2.5,
             color="#007bff", label="NRIPO 033 (Total)")
    ax1.plot(df["PERIODO"], df["LINEAS_EN_SERVICIO"], marker="s", linewidth=2.5,
             color="#ff8c00", label="NRIPO 035 - Líneas en Servicio")

    # --- Etiquetas sobre las líneas ---
    for _, row in df.iterrows():
        ax1.text(row["PERIODO"], row["NRIPO_033"], f"{row['NRIPO_033']:.1f}",
                 ha="center", va="bottom", fontsize=8, color="#004085", fontweight="bold")
        ax1.text(row["PERIODO"], row["LINEAS_EN_SERVICIO"], f"{row['LINEAS_EN_SERVICIO']:.1f}",
                 ha="center", va="bottom", fontsize=8, color="#cc7000", fontweight="bold")

    # --- Config eje izquierdo ---
    ax1.set_xlabel("Período", fontweight="bold")
    ax1.set_ylabel("Cantidad (Millones)", fontweight="bold", color="#212529")
    ax1.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"{x:.1f}M"))
    ax1.tick_params(axis="x", rotation=0)
    ax1.grid(True, linestyle="--", alpha=0.3)

    # --- Eje derecho: barras % diferencia ---
    ax2 = ax1.twinx()
    width = 20
    ax2.bar(df["PERIODO"], df["PORC_DIF"], width=width, alpha=0.3,
            color="#007bff", label="% Diferencia NRIPO 033 vs 035")
    ax2.set_ylabel("Diferencia porcentual (%)", fontweight="bold", color="#212529")
    ax2.yaxis.set_major_formatter(mtick.PercentFormatter())

    # --- Etiquetas en barras ---
    for _, row in df.iterrows():
        ax2.text(row["PERIODO"], row["PORC_DIF"], f"{row['PORC_DIF']:.1f}%",
                 ha="center", va="bottom" if row["PORC_DIF"] >= 0 else "top",
                 fontsize=8, color="#004085", fontweight="bold")

    # --- Título y leyenda ---
    plt.title("Comparativa NRIPO 033 vs 035 - Líneas en Servicio",
              fontsize=13, fontweight="bold", color="#343a40")

    lines_labels = ax1.get_legend_handles_labels()
    bars_labels = ax2.get_legend_handles_labels()
    ax1.legend(
        lines_labels[0] + bars_labels[0],
        lines_labels[1] + bars_labels[1],
        loc="center left",
        bbox_to_anchor=(1.15, 0.5),
        fontsize=9,
        frameon=True,
        fancybox=True,
        shadow=False,
        borderpad=1
    )

    plt.tight_layout(rect=[0, 0, 0.85, 1])

    # --- Guardar imagen ---
    img_dir = os.path.join(os.getcwd(), "static/img")
    os.makedirs(img_dir, exist_ok=True)
    img_path = os.path.join(img_dir, img_name)
    plt.savefig(img_path, bbox_inches="tight", dpi=150)
    plt.close()

    logging.info(f"Gráfico generado: {img_path}")
    return img_name

def generar_grafico_nripo_034_vs_035(df, img_name="grafico_nripo_034_vs_035.png"):
    import pandas as pd
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mtick
    import os, logging

    df = pd.DataFrame(df)
    if df.empty:
        logging.warning("No hay datos para generar el gráfico NRIPO 034 vs 035")
        return None

    # --- Normalizar y ordenar período ---
    df["PERIODO"] = df["PERIODO"].astype(str).str[:6]
    df["PERIODO"] = pd.to_datetime(df["PERIODO"], format="%Y%m")
    df = df.sort_values("PERIODO")

    # --- Convertir columnas numéricas ---
    for col in ["NRIPO_034", "LINEAS_A_SERVICIO_A_3_MES", "DIFERENCIA_NRIPO_034"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # --- Escalar a millones ---
    df["NRIPO_034"] = df["NRIPO_034"] / 1_000_000
    df["LINEAS_A_SERVICIO_A_3_MES"] = df["LINEAS_A_SERVICIO_A_3_MES"] / 1_000_000
    df["DIFERENCIA_NRIPO_034"] = df["DIFERENCIA_NRIPO_034"] / 1_000_000

    # --- Calcular diferencia porcentual ---
    df["PORC_DIF"] = (df["DIFERENCIA_NRIPO_034"] / df["LINEAS_A_SERVICIO_A_3_MES"]) * 100

    # --- Estilo general ---
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax1 = plt.subplots(figsize=(12, 6))
    fig.patch.set_facecolor("#f8f9fa")
    fig.patch.set_edgecolor("black")
    fig.patch.set_linewidth(3)

    # --- Líneas principales ---
    ax1.plot(df["PERIODO"], df["NRIPO_034"], marker="^", linewidth=2.5,
             color="#6610f2", label="NRIPO 034 (Total)")
    ax1.plot(df["PERIODO"], df["LINEAS_A_SERVICIO_A_3_MES"], marker="d", linewidth=2.5,
             color="#20c997", label="NRIPO 035 - Líneas a 3 Meses")

    # --- Etiquetas sobre las líneas ---
    for _, row in df.iterrows():
        ax1.text(row["PERIODO"], row["NRIPO_034"], f"{row['NRIPO_034']:.1f}",
                 ha="center", va="bottom", fontsize=8, color="#4b0082", fontweight="bold")
        ax1.text(row["PERIODO"], row["LINEAS_A_SERVICIO_A_3_MES"], f"{row['LINEAS_A_SERVICIO_A_3_MES']:.1f}",
                 ha="center", va="bottom", fontsize=8, color="#0f5132", fontweight="bold")

    # --- Config eje izquierdo ---
    ax1.set_xlabel("Período", fontweight="bold")
    ax1.set_ylabel("Cantidad (Millones)", fontweight="bold", color="#212529")
    ax1.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"{x:.1f}M"))
    ax1.tick_params(axis="x", rotation=0)
    ax1.grid(True, linestyle="--", alpha=0.3)

    # --- Eje derecho: barras % diferencia ---
    ax2 = ax1.twinx()
    width = 20
    ax2.bar(df["PERIODO"], df["PORC_DIF"], width=width, alpha=0.3,
            color="#6610f2", label="% Diferencia NRIPO 034 vs 035")
    ax2.set_ylabel("Diferencia porcentual (%)", fontweight="bold", color="#212529")
    ax2.yaxis.set_major_formatter(mtick.PercentFormatter())

    # --- Etiquetas en barras ---
    for _, row in df.iterrows():
        ax2.text(row["PERIODO"], row["PORC_DIF"], f"{row['PORC_DIF']:.1f}%",
                 ha="center", va="bottom" if row["PORC_DIF"] >= 0 else "top",
                 fontsize=8, color="#4b0082", fontweight="bold")

    # --- Título y leyenda ---
    plt.title("Comparativa NRIPO 034 vs 035 - Líneas a Servicio a 3 Meses",
              fontsize=13, fontweight="bold", color="#343a40")

    lines_labels = ax1.get_legend_handles_labels()
    bars_labels = ax2.get_legend_handles_labels()
    ax1.legend(
        lines_labels[0] + bars_labels[0],
        lines_labels[1] + bars_labels[1],
        loc="center left",
        bbox_to_anchor=(1.15, 0.5),
        fontsize=9,
        frameon=True,
        fancybox=True,
        shadow=False,
        borderpad=1
    )

    plt.tight_layout(rect=[0, 0, 0.85, 1])

    # --- Guardar imagen ---
    img_dir = os.path.join(os.getcwd(), "static/img")
    os.makedirs(img_dir, exist_ok=True)
    img_path = os.path.join(img_dir, img_name)
    plt.savefig(img_path, bbox_inches="tight", dpi=150)
    plt.close()

    logging.info(f"Gráfico generado: {img_path}")
    return img_name



# ----------- RUTA PRINCIPAL -----------

@NRIPO_035_bp.route('/NRIPO_035')
def index_mtc():
    df1 = Query_NRIPO_035_TOT()
    df2 = Query_nripo_33_35_DIF()
    df3 = Query_nripo_34_35_DIF()

    if not df1 or not df2:
        return "<h2>Error al obtener datos de Netezza</h2>", 503

    img1 = generar_grafico_nripo_035_TOT(df1)
    img2 = generar_grafico_nripo_033_vs_035(df2)
    img3 = generar_grafico_nripo_034_vs_035(df3)

    return render_template('NRIPO_035.html', img1=img1, img2=img2, img3=img3)

# ----------- RUTA PARA CARGAR IMÁGENES -----------

@NRIPO_035_bp.route('/static/img/<filename>')
def imagenes(filename):
    img_dir = os.path.join(os.getcwd(), "static/img")
    return send_from_directory(img_dir, filename)
