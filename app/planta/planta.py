import os, logging
import pandas as pd
from app.db import conectar_netezza  # Importa la conexión centralizada
import matplotlib
matplotlib.use("Agg")  # Usa un backend sin interfaz gráfica
import matplotlib.pyplot as plt
from flask import Flask, render_template, request, Blueprint
from flask import send_from_directory
import numpy as np

planta_bp = Blueprint('planta', __name__)
planta_bp.debug = True  # Agrega esto

# Variable global para almacenar el valor máximo de CANTIDAD
max_y_global = 0

def Query_Netezza():
    print("Query_Netezza")    
    conn = conectar_netezza()
    
    if not conn:
        logging.error("No se pudo conectar a Netezza")
        return []

    sql_trd = """    
    SELECT PERIODO,ESTADO,TECNOLOGIA,sum(CANTIDAD) AS CANTIDAD 
    FROM control_mako..T_AGR_VAL_PLT
    WHERE FUENTE = 'JRR_BA_PLANTA'
    and TECNOLOGIA <> 'None'
    and PERIODO >= '202501'
    GROUP BY 1,2,3;
    """

    try:
        df_trd = pd.read_sql(sql_trd, conn)
        print("Query terada1 OK")
        return df_trd.to_dict(orient="records")
        
    except Exception as ERR_NETE:
        logging.error(f"Error al ejecutar la consulta en Query_Netezza: {ERR_NETE}")
        return []
    finally:        
        print("Conexión a Teradata cerrada")

def Query_Netezza2():
    print("Query_Netezza2")    
    conn = conectar_netezza()
    
    if not conn:
        logging.error("No se pudo conectar a Netezza")
        return []

    sql_trd2 = """    
    SELECT PERIODO,ESTADO,TECNOLOGIA,sum(CANTIDAD) AS CANTIDAD 
    FROM control_mako..T_AGR_VAL_PLT
    WHERE FUENTE = 'T_INH_PLT_CHU'
    and TECNOLOGIA <> 'None'
    and PERIODO >= '202501'
    GROUP BY 1,2,3;    
    """

    try:
        df_trd2 = pd.read_sql(sql_trd2, conn)
        print("Query terada2 OK")
        return df_trd2.to_dict(orient="records")
        
    except Exception as ERR_NETE:
        logging.error(f"Error al ejecutar la consulta en Query_Netezza2: {ERR_NETE}")
        return []
    finally:
        print("Conexión a Teradata2 cerrada")

# Colores fijos asignados por tecnología
COLORES_TECNOLOGIA = {
    "ADSL": "#ff7f0e",  # Naranja
    "FTTH": "#1f77b4",  # Celeste
    "HFC": "#2ca02c"    # Verde
}


@planta_bp.route('/planta')
def index():
    # Ejecutar las consultas en Teradata
    df1 = Query_Netezza()
    df2 = Query_Netezza2()

    if not df1 or not df2:
        return "<h2>Error al obtener datos de Teradata</h2>", 503

    df1 = pd.DataFrame(df1)
    df2 = pd.DataFrame(df2)

    # Obtener las tecnologías y agregar la opción "Todas"
    tecnologias1 = df1["TECNOLOGIA"].unique().tolist()    
    tecnologias1.insert(0, "TODAS")

    tecnologias2 = df2["TECNOLOGIA"].unique().tolist()    
    tecnologias2.insert(0, "TODAS")

    # Obtener los estados únicos por cada consulta
    estados1 = df1["ESTADO"].unique().tolist()
    estados2 = df2["ESTADO"].unique().tolist()
    
    # Obtener los periodos
    periodo1 = df1["PERIODO"].unique().tolist()
    periodo2 = df2["PERIODO"].unique().tolist()

    return render_template('planta.html', 
                            tecnologias1=tecnologias1,
                            tecnologias2=tecnologias2, 
                            estados1=estados1,
                            estados2=estados2,
                            periodo1=periodo1,
                            periodo2=periodo2)

def generar_grafico(df, img_name):
    global max_y_global

    # --- Validar columnas ---
    required_columns = {"ESTADO", "TECNOLOGIA", "PERIODO", "CANTIDAD"}
    if not required_columns.issubset(df.columns):
        logging.error("❌ Faltan columnas requeridas en el DataFrame")
        return "Error: Datos incompletos", 500

    # --- Obtener parámetros de URL ---
    tecnologia = request.args.get("tecnologia", "TODAS")
    estado = request.args.get("estado", "ACTIVO")
    periodos_param = request.args.get("periodo", "")
    periodos = periodos_param.split(",") if periodos_param else []

    logging.info(f"Tecnología seleccionada: {tecnologia}")
    logging.info(f"Estado seleccionado: {estado}")
    logging.info(f"Períodos seleccionados: {periodos if periodos else 'TODOS'}")

    # --- Filtrar por estado ---
    df = df[df["ESTADO"] == estado]
    if df.empty:
        logging.warning("⚠️ No hay datos para el estado seleccionado")
        return "No hay datos disponibles", 404

    # --- Normalizar columnas ---
    df["TECNOLOGIA"] = df["TECNOLOGIA"].astype(str).str.strip().str.upper()
    df["PERIODO"] = pd.to_datetime(df["PERIODO"].astype(str) + "01", format="%Y%m%d", errors="coerce")
    df = df.dropna(subset=["PERIODO"]).sort_values("PERIODO")
    df["CANTIDAD"] = pd.to_numeric(df["CANTIDAD"], errors="coerce").fillna(0)

    # --- Filtrar por períodos específicos ---
    if periodos:
        periodos_dt = [pd.to_datetime(p + "01", format="%Y%m%d", errors="coerce") for p in periodos]
        df = df[df["PERIODO"].isin(periodos_dt)]
        if df.empty:
            logging.warning("⚠️ No hay datos para los períodos seleccionados")
            return "No hay datos disponibles", 404

    # --- Escalar valores ---
    df["CANTIDAD"] = df["CANTIDAD"] / 1_000_000  # millones

    # --- Crear gráfico ---
    fig, ax = plt.subplots(figsize=(14, 5))
    plt.style.use("seaborn-v0_8-whitegrid")

    # --- Calcular escala Y dinámica ---
    max_y = df["CANTIDAD"].max() * 1.1
    min_y = max(0, df["CANTIDAD"].min() * 0.9)

    if max_y_global == 0:
        max_y_global = max_y

    # --- Dibujar líneas ---
    tecnologias = df["TECNOLOGIA"].unique()
    colores = plt.cm.tab10.colors

    if tecnologia == "TODAS":
        for i, tech in enumerate(tecnologias):
            df_tech = df[df["TECNOLOGIA"] == tech]

            if df_tech.empty:
                logging.warning(f"⚠️ Sin datos para la tecnología: {tech}")
                continue  # Evita el error IndexError

            ax.plot(
                df_tech["PERIODO"].dt.strftime("%Y-%m"),
                df_tech["CANTIDAD"],
                marker="o", linewidth=2, linestyle="-",
                color=colores[i % len(colores)],
                label=tech
            )

            # Etiqueta solo en el último punto si hay datos
            last_row = df_tech.iloc[-1]
            ax.text(
                last_row["PERIODO"].strftime("%Y-%m"),
                last_row["CANTIDAD"] + (max_y * 0.02),
                f"{last_row['CANTIDAD']:.2f}",
                ha="center", va="bottom", fontsize=8, fontweight="bold"
            )

    else:
        df = df[df["TECNOLOGIA"] == tecnologia.strip().upper()]
        if df.empty:
            logging.warning("⚠️ No hay datos disponibles para la tecnología seleccionada")
            return "No hay datos disponibles para la tecnología seleccionada", 404

        color = COLORES_TECNOLOGIA.get(tecnologia, "#1f77b4")
        ax.plot(
            df["PERIODO"].dt.strftime("%Y-%m"),
            df["CANTIDAD"],
            marker="o", linewidth=2, linestyle="-",
            color=color, label=tecnologia
        )

        # Etiqueta solo si hay datos
        last_row = df.iloc[-1]
        ax.text(
            last_row["PERIODO"].strftime("%Y-%m"),
            last_row["CANTIDAD"] + (max_y * 0.02),
            f"{last_row['CANTIDAD']:.2f}",
            ha="center", va="bottom", fontsize=8, fontweight="bold"
        )

    # --- Configuración de ejes ---
    ax.set_xlabel("Período", fontweight="bold")
    ax.set_ylabel("Cantidad (Millones)", fontweight="bold")
    ax.set_ylim(min_y, max_y)
    ax.tick_params(axis="x", rotation=0, labelsize=9)
    ax.tick_params(axis="y", labelsize=9)

    # --- Bordes elegantes ---
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_color("black")
        spine.set_linewidth(0.8)

    # --- Título y leyenda ---
    plt.title(f"Cantidad total de activos ({estado}) por tecnología", fontweight="bold", pad=15)
    ax.legend(loc="best", fontsize=9, frameon=True)

    plt.tight_layout()

    # --- Guardar imagen ---
    img_dir = os.path.join(os.getcwd(), "static/img")
    os.makedirs(img_dir, exist_ok=True)
    img_path = os.path.join(img_dir, img_name)

    try:
        plt.savefig(img_path, bbox_inches="tight", dpi=200)
        plt.close()
        logging.info(f"✅ Gráfico generado correctamente: {img_path}")
        return send_from_directory(img_dir, img_name)
    except Exception as e:
        logging.error(f"❌ Error al guardar el gráfico: {e}")
        return "Error interno del servidor", 500



@planta_bp.route('/grafico1')
def create_plot1():
    print("create_plot1")
    df1 = Query_Netezza()
    if not df1:
        return "Error al obtener datos de Teradata", 500
    df1 = pd.DataFrame(df1)
    #print(df1)
    return generar_grafico(df1, "grafico1.png")

@planta_bp.route('/grafico2')
def create_plot2():
    df2 = Query_Netezza2()
    if not df2:
        return "Error al obtener datos de Teradata", 500
    df2 = pd.DataFrame(df2)
    return generar_grafico(df2, "grafico2.png")
