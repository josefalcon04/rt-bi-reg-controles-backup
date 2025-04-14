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

    # Verificar que las columnas necesarias existen
    required_columns = {"ESTADO", "TECNOLOGIA", "PERIODO", "CANTIDAD"}
    if not required_columns.issubset(df.columns):
        return "Error: Los datos no contienen las columnas necesarias", 500

    # Obtener parámetros de la URL
    tecnologia = request.args.get("tecnologia", "TODAS")
    estado = request.args.get("estado", "ACTIVO")
    periodos_param = request.args.get("periodo", "")    
    periodos = request.args.get("periodo", "").split(",") if request.args.get("periodo") else []

    print("Tecnología:", tecnologia)
    print("Estado:", estado)
    print("Periodos recibidos:", periodos if periodos else "TODOS")

    # Filtrar datos por estado seleccionado
    df = df[df["ESTADO"] == estado]

    # Convertir PERIODO a string y ordenar
    df["PERIODO"] = df["PERIODO"].astype(str)
    df = df.sort_values("PERIODO")

    # Asegurar que CANTIDAD es numérico
    df["CANTIDAD"] = pd.to_numeric(df["CANTIDAD"], errors="coerce")

    # Filtrar por periodos si se proporcionaron
    if periodos:
        df = df[df["PERIODO"].isin(periodos)]

    if df.empty:
        return "No hay datos disponibles para la selección", 404

    # Si no se ha calculado `max_y_global`, hacerlo ahora
    if max_y_global == 0:
        max_y_global = float(df["CANTIDAD"].max())

    # Ajustar tamaño del gráfico
    plt.figure(figsize=(14, 5))

    tecnologias_unicas = df["TECNOLOGIA"].unique()

    if tecnologia == "TODAS":
        for tech in tecnologias_unicas:
            df_tech = df[df["TECNOLOGIA"] == tech]
            color = COLORES_TECNOLOGIA.get(tech, "#000000")  # Color negro si no hay color asignado
            plt.plot(df_tech["PERIODO"], df_tech["CANTIDAD"], marker="o", linestyle="-", label=tech, color=color)
    else:
        df = df[df["TECNOLOGIA"] == tecnologia]
        if df.empty:
            return "No hay datos disponibles para la selección", 404
        color = COLORES_TECNOLOGIA.get(tecnologia, "#000000")
        plt.plot(df["PERIODO"], df["CANTIDAD"], marker="o", linestyle="-", label=tecnologia, color=color)

    plt.xlabel("Período")
    plt.ylabel("Cantidad")
    if not df["PERIODO"].empty:
        plt.xticks(df["PERIODO"].unique(), rotation=0)

    plt.ylim(0, max_y_global * 1.1)
    plt.grid(True)
    plt.legend(loc="lower center", bbox_to_anchor=(0.5, -0.2), ncol=len(tecnologias_unicas))

    # Guardar imagen
    img_dir = os.path.join(os.getcwd(), "static/img")
    os.makedirs(img_dir, exist_ok=True)
    img_path = os.path.join(img_dir, img_name)

    try:
        plt.savefig(img_path, bbox_inches='tight')
        plt.close()
        return send_from_directory(img_dir, img_name)
    except Exception as e:
        print(f"Error en generar_grafico: {str(e)}")
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
