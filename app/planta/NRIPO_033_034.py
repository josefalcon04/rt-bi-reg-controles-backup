import os
import logging
import pandas as pd
from flask import Flask, Blueprint, render_template, send_from_directory
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from app.db import conectar_netezza  # Asegúrate de tener esto definido correctamente
import matplotlib.ticker as mtick

NRIPO_033_034_bp = Blueprint('NRIPO_033_034', __name__)

# ----------- CONSULTAS -----------

def Query_NRIPO_033():
    conn = conectar_netezza()
    if not conn:
        logging.error("No se pudo conectar a Netezza")
        return []

    sql = """
    SELECT 
        SUBSTRING( ANIO_MES,1,4) || trim(TO_char(MES,'00')) AS PERIODO,
        MODALIDAD,
        sum(LINEAS_SERVICIO) AS CANTIDAD 
    FROM PROD_REGU_NORMA_DATA..T_NRM_NRIPO_033_HIST
    WHERE ANIO_MES >= '202501'
    GROUP BY 1,2
    ORDER BY 1 desc
    """

    try:
        df = pd.read_sql(sql, conn)
        return df.to_dict(orient="records")
    except Exception as e:
        logging.error(f"Error Query_NRIPO_033: {e}")
        return []
    finally:
        conn.close()

def Query_NRIPO_033_TOT():
    conn = conectar_netezza()
    if not conn:
        logging.error("No se pudo conectar a Netezza")
        return []

    sql = """
    SELECT 
    SUBSTRING( ANIO_MES,1,4) || trim(TO_char(MES,'00')) AS PERIODO ,sum(LINEAS_SERVICIO) AS CANTIDAD 
    FROM PROD_REGU_NORMA_DATA..T_NRM_NRIPO_033_HIST
    WHERE ANIO_MES >= '202401'
    GROUP BY 1
    ORDER BY 1 desc
    """

    try:
        df = pd.read_sql(sql, conn)
        return df.to_dict(orient="records")
    except Exception as e:
        logging.error(f"Error Query_NRIPO_033_TOT: {e}")
        return []
    finally:
        conn.close()

def Query_NRIPO_034():
    conn = conectar_netezza()
    if not conn:
        logging.error("No se pudo conectar a Netezza")
        return []

    sql = """
    SELECT 
    SUBSTRING( ANIO_MES,1,4) || trim(TO_char(MES,'00')) AS PERIODO,MODALIDAD ,sum(LINEAS_SERVICIO) AS CANTIDAD 
    FROM PROD_REGU_NORMA_DATA..T_NRM_NRIPO_034_HIST
    WHERE ANIO_MES >= '202501'
    GROUP BY 1,2
    ORDER BY 1 desc;
    """

    try:
        df = pd.read_sql(sql, conn)
        return df.to_dict(orient="records")
    except Exception as e:
        logging.error(f"Error Query_NRIPO_034: {e}")
        return []
    finally:
        conn.close()

def Query_NRIPO_034_TOT():
    conn = conectar_netezza()
    if not conn:
        logging.error("No se pudo conectar a Netezza")
        return []

    sql = """
    SELECT 
    SUBSTRING( ANIO_MES,1,4) || trim(TO_char(MES,'00')) AS PERIODO ,sum(LINEAS_SERVICIO) AS CANTIDAD 
    FROM PROD_REGU_NORMA_DATA..T_NRM_NRIPO_034_HIST
    WHERE ANIO_MES >= '202401'
    GROUP BY 1
    ORDER BY 1 desc
    """

    try:
        df = pd.read_sql(sql, conn)
        return df.to_dict(orient="records")
    except Exception as e:
        logging.error(f"Error Query_NRIPO_034_TOT: {e}")
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

def generar_grafico_nripo_033(df, img_name="grafico_nripo_033.png"):
    df = pd.DataFrame(df)
    if df.empty:
        logging.warning("No hay datos para generar el gráfico NRIPO 033")
        return None

    # --- Normalizar columna PERIODO ---
    df["PERIODO"] = df["PERIODO"].astype(str)

    if df["PERIODO"].str.match(r"^\d{6}$").all():
        df["PERIODO"] = pd.to_datetime(df["PERIODO"], format="%Y%m")
    else:
        df["PERIODO"] = pd.to_datetime(df["PERIODO"], errors="coerce")

    df = df.sort_values("PERIODO")

    # Escalar a millones la columna cantidad
    df = convertir_cantidad_a_millones(df, "CANTIDAD")

    # --- Crear figura ---
    fig, ax1 = plt.subplots(figsize=(14, 5))

    # Escala máxima eje Y izquierdo
    max_y = df["CANTIDAD"].max()
    if pd.isna(max_y):
        logging.warning("Columna CANTIDAD no tiene valores numéricos válidos")
        return None
    max_y *= 1.1

    # --- Gráfico de líneas ---
    for modalidad in df["MODALIDAD"].unique():
        df_mod = df[df["MODALIDAD"] == modalidad]
        ax1.plot(
            df_mod["PERIODO"].dt.strftime("%Y-%m"),
            df_mod["CANTIDAD"],
            marker="o",
            linestyle="-",
            label=modalidad
        )

        # Etiquetas de valores
        for x, y in zip(df_mod["PERIODO"].dt.strftime("%Y-%m"), df_mod["CANTIDAD"]):
            ax1.text(x, y, f"{y:.1f}", ha="center", va="bottom", fontsize=7, fontweight="bold")

    ax1.set_xlabel("Período", fontweight="bold")
    ax1.set_ylabel("Cantidad (Millones)", fontweight="bold")
    ax1.set_ylim(0, max_y)
    ax1.tick_params(axis="x", rotation=0)
    ax1.grid(False)

    # --- Título y leyenda ---
    plt.title("Líneas móviles en servicio por modalidad", fontweight="bold")
    ax1.legend(loc="best", fontsize=8, frameon=True)

    plt.tight_layout()

    # Guardar imagen
    img_dir = os.path.join(os.getcwd(), "static/img")
    os.makedirs(img_dir, exist_ok=True)
    img_path = os.path.join(img_dir, img_name)

    plt.savefig(img_path, bbox_inches="tight")
    plt.close()

    logging.info(f"Gráfico generado: {img_path}")
    return img_name


COLORES_TIPO = {
    "Prepago":  "#ff8c00",  # naranja
    "Postpago": "#007bff",  # azul
    "Control":  "#28a745",  # verde
    "Total":    "#6c757d"   # gris
}

def generar_grafico_nripo_033_TOT(df, img_name="grafico_nripo_033_tot.png"):
    df = pd.DataFrame(df)
    if df.empty:
        logging.warning("No hay datos para generar el gráfico NRIPO 033 TOT")
        return None

    # Asegurar que PERIODO tenga formato YYYYMM y convertir a fecha
    df["PERIODO"] = df["PERIODO"].astype(str).str[:6]
    df["PERIODO"] = pd.to_datetime(df["PERIODO"], format="%Y%m")
    df = df.sort_values("PERIODO")

    # Escalar a millones
    df = convertir_cantidad_a_millones(df, "CANTIDAD")

    # Escala máxima eje Y izquierdo
    max_y = df["CANTIDAD"].max()
    if pd.isna(max_y):
        logging.warning("Columna CANTIDAD no tiene valores numéricos válidos")
        return None
    max_y *= 1.1

    # --- Crear figura con ejes dobles ---
    fig, ax1 = plt.subplots(figsize=(14, 5))

    # 📈 Línea total
    ax1.plot(
        df["PERIODO"].dt.strftime("%Y-%m"),
        df["CANTIDAD"],
        marker="o",
        linestyle="-",
        color=COLORES_TIPO["Total"],
        label="Total"
    )

    # Etiquetas sobre los puntos
    for x, y in zip(df["PERIODO"].dt.strftime("%Y-%m"), df["CANTIDAD"]):
        ax1.text(x, y, f"{y:.1f}", ha="center", va="bottom", fontsize=7, fontweight="bold")

    ax1.set_xlabel("Período", fontweight="bold")
    ax1.set_ylabel("Cantidad (Millones)", fontweight="bold")
    ax1.set_ylim(0, max_y)
    ax1.tick_params(axis="x", rotation=0)
    ax1.grid(False)

    # --- Eje derecho con variación 📊 ---
    ax2 = ax1.twinx()

    variacion = df.set_index("PERIODO")["CANTIDAD"].diff().fillna(0)

    # Colores dinámicos: verde (+), rojo (-)
    colores = ["green" if v >= 0 else "red" for v in variacion.values]

    ax2.bar(
        variacion.index.strftime("%Y-%m"),
        variacion.values,
        color=colores,
        alpha=0.7
    )

    ax2.set_ylabel("Variación (Millones)", fontweight="bold")

    # --- Título y leyenda ---
    plt.title("Líneas móviles en servicio (Total)", fontweight="bold")
    lines_labels = ax1.get_legend_handles_labels()
    bars_labels = ax2.get_legend_handles_labels()
    ax1.legend(
        lines_labels[0] + bars_labels[0],
        lines_labels[1] + bars_labels[1],
        loc="best",
        fontsize=8,
        frameon=True
    )

    # Formatear eje Y izquierdo como millones
    ax1.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"{x:.1f}M"))

    plt.tight_layout()

    # Guardar imagen
    img_dir = os.path.join(os.getcwd(), "static/img")
    os.makedirs(img_dir, exist_ok=True)
    img_path = os.path.join(img_dir, img_name)

    plt.savefig(img_path, bbox_inches="tight")
    plt.close()

    logging.info(f"Gráfico generado: {img_path}")
    return img_name


def generar_grafico_nripo_034(df, img_name="grafico_nripo_034.png"):
    df = pd.DataFrame(df)
    if df.empty:
        logging.warning("No hay datos para generar el gráfico NRIPO 034")
        return None

    # --- Normalizar columna PERIODO ---
    df["PERIODO"] = df["PERIODO"].astype(str)
    if df["PERIODO"].str.match(r"^\d{6}$").all():
        df["PERIODO"] = pd.to_datetime(df["PERIODO"], format="%Y%m")
    else:
        df["PERIODO"] = pd.to_datetime(df["PERIODO"], errors="coerce")

    df = df.sort_values("PERIODO")

    # Escalar a millones la columna cantidad
    df = convertir_cantidad_a_millones(df, "CANTIDAD")

    # --- Crear figura ---
    fig, ax = plt.subplots(figsize=(14, 5))

    # Escala máxima eje Y
    max_y = df["CANTIDAD"].max()
    if pd.isna(max_y):
        logging.warning("Columna CANTIDAD no tiene valores numéricos válidos")
        return None
    max_y *= 1.1

    # --- Gráfico de líneas ---
    for modalidad in df["MODALIDAD"].unique():
        df_mod = df[df["MODALIDAD"] == modalidad]
        ax.plot(
            df_mod["PERIODO"].dt.strftime("%Y-%m"),
            df_mod["CANTIDAD"],
            marker="o",
            linestyle="-",
            label=modalidad
        )

        # Etiquetas de valores
        for x, y in zip(df_mod["PERIODO"].dt.strftime("%Y-%m"), df_mod["CANTIDAD"]):
            ax.text(x, y, f"{y:.1f}", ha="center", va="bottom", fontsize=7, fontweight="bold")

    ax.set_xlabel("Período", fontweight="bold")
    ax.set_ylabel("Cantidad (Millones)", fontweight="bold")
    ax.set_ylim(0, max_y)
    ax.tick_params(axis="x", rotation=0)
    ax.grid(False)

    # --- Título y leyenda ---
    plt.title("Líneas móviles en servicio a 3 meses", fontweight="bold")
    ax.legend(loc="best", fontsize=8, frameon=True)

    plt.tight_layout()

    # Guardar imagen
    img_dir = os.path.join(os.getcwd(), "static/img")
    os.makedirs(img_dir, exist_ok=True)
    img_path = os.path.join(img_dir, img_name)

    plt.savefig(img_path, bbox_inches="tight")
    plt.close()
    

    logging.info(f"Gráfico generado: {img_path}")
    return img_name


def generar_grafico_nripo_034_TOT(df, img_name="grafico_nripo_034_tot.png"):
    df = pd.DataFrame(df)
    if df.empty:
        logging.warning("No hay datos para generar el gráfico NRIPO 034 TOT")
        return None

    # Asegurar que PERIODO tenga formato YYYYMM y convertir a fecha
    df["PERIODO"] = df["PERIODO"].astype(str).str[:6]
    df["PERIODO"] = pd.to_datetime(df["PERIODO"], format="%Y%m")
    df = df.sort_values("PERIODO")

    # Escalar a millones
    df = convertir_cantidad_a_millones(df, "CANTIDAD")

    # Escala máxima eje Y izquierdo
    max_y = df["CANTIDAD"].max()
    if pd.isna(max_y):
        logging.warning("Columna CANTIDAD no tiene valores numéricos válidos")
        return None
    max_y *= 1.1

    # --- Crear figura con ejes dobles ---
    fig, ax1 = plt.subplots(figsize=(14, 5))

    # 📈 Línea total
    ax1.plot(
        df["PERIODO"].dt.strftime("%Y-%m"),
        df["CANTIDAD"],
        marker="o",
        linestyle="-",
        color=COLORES_TIPO["Total"],
        label="Total"
    )

    # Etiquetas sobre los puntos
    for x, y in zip(df["PERIODO"].dt.strftime("%Y-%m"), df["CANTIDAD"]):
        ax1.text(x, y, f"{y:.1f}", ha="center", va="bottom", fontsize=7, fontweight="bold")

    ax1.set_xlabel("Período", fontweight="bold")
    ax1.set_ylabel("Cantidad (Millones)", fontweight="bold")
    ax1.set_ylim(0, max_y)
    ax1.tick_params(axis="x", rotation=0)
    ax1.grid(False)

    # --- Eje derecho con variación 📊 ---
    ax2 = ax1.twinx()

    variacion = df.set_index("PERIODO")["CANTIDAD"].diff().fillna(0)

    # Colores dinámicos: verde (+), rojo (-)
    colors = ["green" if v >= 0 else "red" for v in variacion.values]

    ax2.bar(
        variacion.index.strftime("%Y-%m"),
        variacion.values,
        color=colors,
        alpha=0.6,
        label="Variación"
    )

    ax2.set_ylabel("Variación (Millones)", fontweight="bold")

    # --- Título y leyenda ---
    plt.title("Líneas móviles en servicio (Total)", fontweight="bold")
    lines_labels = ax1.get_legend_handles_labels()
    bars_labels = ax2.get_legend_handles_labels()
    ax1.legend(
        lines_labels[0] + bars_labels[0],
        lines_labels[1] + bars_labels[1],
        loc="best",
        fontsize=8,
        frameon=True
    )

    # Formatear eje Y izquierdo como millones
    ax1.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"{x:.1f}M"))

    plt.tight_layout()

    # Guardar imagen
    img_dir = os.path.join(os.getcwd(), "static/img")
    os.makedirs(img_dir, exist_ok=True)
    img_path = os.path.join(img_dir, img_name)

    plt.savefig(img_path, bbox_inches="tight")
    plt.close()

    logging.info(f"Gráfico generado: {img_path}")
    return img_name

# ----------- RUTA PRINCIPAL -----------

@NRIPO_033_034_bp.route('/NRIPO_033_034')
def index_mtc():
    df1 = Query_NRIPO_033()
    df2 = Query_NRIPO_034()
    df3 = Query_NRIPO_033_TOT()
    df4 = Query_NRIPO_034_TOT()

    if not df1 or not df2 or not df3 or not df4:
        return "<h2>Error al obtener datos de Netezza</h2>", 503

    img1 = generar_grafico_nripo_033(df1)
    img2 = generar_grafico_nripo_034(df2)
    img3 = generar_grafico_nripo_033_TOT(df3)
    img4 = generar_grafico_nripo_034_TOT(df4)

    return render_template('NRIPO_033_034.html', img1=img1, img2=img2, img3=img3, img4=img4)

# ----------- RUTA PARA CARGAR IMÁGENES -----------

@NRIPO_033_034_bp.route('/static/img/<filename>')
def imagenes(filename):
    img_dir = os.path.join(os.getcwd(), "static/img")
    return send_from_directory(img_dir, filename)
