from flask import Blueprint, render_template
from app.db import conectar_netezza  # Importa la conexión centralizada
import pandas as pd
from datetime import datetime
from calendar import monthrange


calendario_bp = Blueprint('calendario', __name__)


def obtener_datos():
    query = """
SELECT 
    NOMBRE_PROCESO_REPO,
    FRECUENCIA_REPO,
    CASE 
        WHEN FRECUENCIA_REPO = 'ANUAL' THEN '#00BFFF'  -- CELESTE
        WHEN FRECUENCIA_REPO = 'SEMESTRAL' THEN '#FFA500'  -- NARANJA
        WHEN FRECUENCIA_REPO = 'TRIMESTRAL' THEN '#008000'  -- VERDE
        WHEN FRECUENCIA_REPO = 'MENSUAL' THEN '#FFFF00'  -- AMARILLO
    END AS COLOR_RESULTADO,
CASE 
        WHEN FRECUENCIA_REPO = 'ANUAL' THEN TO_CHAR(CURRENT_DATE, 'YYYY') || SUBSTRING( DIA_EJECUCION_REPO,3,2) || SUBSTRING( DIA_EJECUCION_REPO,1,2)
        WHEN FRECUENCIA_REPO = 'SEMESTRAL' THEN TO_CHAR(CURRENT_DATE, 'YYYY') || LPAD( SUBSTRING( DIA_EJECUCION_REPO,3,2)  ,2, '0') || SUBSTRING( DIA_EJECUCION_REPO,1,2) || '|' || '2025' || LPAD( SUBSTRING( DIA_EJECUCION_REPO,3,2) + 6 ,2, '0') || SUBSTRING( DIA_EJECUCION_REPO,1,2)
		WHEN FRECUENCIA_REPO = 'MENSUAL' THEN 
		TO_CHAR(CURRENT_DATE, 'YYYY') || LPAD( SUBSTRING( DIA_EJECUCION_REPO,3,2)  ,2, '0') || SUBSTRING( DIA_EJECUCION_REPO,1,2) || '|' ||
		TO_CHAR(CURRENT_DATE, 'YYYY') || LPAD( SUBSTRING( DIA_EJECUCION_REPO,3,2) + 1 ,2, '0') || SUBSTRING( DIA_EJECUCION_REPO,1,2)|| '|' ||
		TO_CHAR(CURRENT_DATE, 'YYYY') || LPAD( SUBSTRING( DIA_EJECUCION_REPO,3,2) + 2 ,2, '0') || SUBSTRING( DIA_EJECUCION_REPO,1,2)|| '|' ||
		TO_CHAR(CURRENT_DATE, 'YYYY') || LPAD( SUBSTRING( DIA_EJECUCION_REPO,3,2) + 3 ,2, '0') || SUBSTRING( DIA_EJECUCION_REPO,1,2)|| '|' ||
		TO_CHAR(CURRENT_DATE, 'YYYY') || LPAD( SUBSTRING( DIA_EJECUCION_REPO,3,2) + 4 ,2, '0') || SUBSTRING( DIA_EJECUCION_REPO,1,2)|| '|' ||
		TO_CHAR(CURRENT_DATE, 'YYYY') || LPAD( SUBSTRING( DIA_EJECUCION_REPO,3,2) + 5 ,2, '0') || SUBSTRING( DIA_EJECUCION_REPO,1,2)|| '|' ||
		TO_CHAR(CURRENT_DATE, 'YYYY') || LPAD( SUBSTRING( DIA_EJECUCION_REPO,3,2) + 6 ,2, '0') || SUBSTRING( DIA_EJECUCION_REPO,1,2)|| '|' ||
		TO_CHAR(CURRENT_DATE, 'YYYY') || LPAD( SUBSTRING( DIA_EJECUCION_REPO,3,2) + 7 ,2, '0') || SUBSTRING( DIA_EJECUCION_REPO,1,2)|| '|' ||
		TO_CHAR(CURRENT_DATE, 'YYYY') || LPAD( SUBSTRING( DIA_EJECUCION_REPO,3,2) + 8 ,2, '0') || SUBSTRING( DIA_EJECUCION_REPO,1,2)|| '|' ||
		TO_CHAR(CURRENT_DATE, 'YYYY') || LPAD( SUBSTRING( DIA_EJECUCION_REPO,3,2) + 9 ,2, '0') || SUBSTRING( DIA_EJECUCION_REPO,1,2)|| '|' ||
		TO_CHAR(CURRENT_DATE, 'YYYY') || LPAD( SUBSTRING( DIA_EJECUCION_REPO,3,2) + 10 ,2, '0') || SUBSTRING( DIA_EJECUCION_REPO,1,2)|| '|' ||
		TO_CHAR(CURRENT_DATE, 'YYYY') || LPAD( SUBSTRING( DIA_EJECUCION_REPO,3,2) + 11 ,2, '0') || SUBSTRING( DIA_EJECUCION_REPO,1,2)
		WHEN FRECUENCIA_REPO = 'TRIMESTRAL' THEN 
		TO_CHAR(CURRENT_DATE, 'YYYY') || LPAD( SUBSTRING( DIA_EJECUCION_REPO,3,2)  ,2, '0')    || SUBSTRING( DIA_EJECUCION_REPO,1,2) || '|' ||
		TO_CHAR(CURRENT_DATE, 'YYYY') || LPAD( SUBSTRING( DIA_EJECUCION_REPO,3,2) + 3 ,2, '0') || SUBSTRING( DIA_EJECUCION_REPO,1,2)|| '|' ||
		TO_CHAR(CURRENT_DATE, 'YYYY') || LPAD( SUBSTRING( DIA_EJECUCION_REPO,3,2) + 6 ,2, '0') || SUBSTRING( DIA_EJECUCION_REPO,1,2)|| '|' ||
		TO_CHAR(CURRENT_DATE, 'YYYY') || LPAD( SUBSTRING( DIA_EJECUCION_REPO,3,2) + 9 ,2, '0') || SUBSTRING( DIA_EJECUCION_REPO,1,2)
    	END AS CAMPO_RESULTADO
FROM CONTROL_MAKO..T_CATA_REPORTES_NORMA
UNION ALL
SELECT 
    CASE
    	WHEN NOMBRE_INPUT = 'T_INP_PLT_CHRN_FJ' THEN 'PLANTA_CONTROL'
    	WHEN NOMBRE_INPUT = 'T_INP_PLT_MTC' THEN 'PLANTA_MTC'
    ELSE NOMBRE_INPUT 
    END AS NOMBRE_PROCESO_REPO,
    CASE 
	    WHEN NOMBRE_INPUT = 'T_INP_PLT_CHRN_FJ' OR NOMBRE_INPUT = 'T_INP_PLT_MTC' THEN 'PLANTA'
    	ELSE FRECUENCIA_INPUT END AS FRECUENCIA_REPO,
    CASE 
        WHEN FRECUENCIA_INPUT = 'ANUAL' THEN '#00BFFF'  -- CELESTE
        WHEN FRECUENCIA_INPUT = 'SEMESTRAL' THEN '#FFA500'  -- NARANJA
        WHEN FRECUENCIA_INPUT = 'TRIMESTRAL' THEN '#008000'  -- VERDE
        WHEN FRECUENCIA_INPUT = 'PLANTA' THEN '#FFFF00'  -- AMARILLO
        WHEN FRECUENCIA_INPUT = 'DIARIO' THEN '#FF00BF'  -- ROSADO
        ELSE '#FF1B00'
    END AS COLOR_RESULTADO,
	CASE 
        WHEN FRECUENCIA_INPUT = 'ANUAL' THEN TO_CHAR(CURRENT_DATE, 'YYYY') || SUBSTRING( DIA_EJECUCION_INPUT,3,2) || SUBSTRING( DIA_EJECUCION_INPUT,1,2)
        WHEN FRECUENCIA_INPUT = 'SEMESTRAL' THEN TO_CHAR(CURRENT_DATE, 'YYYY') || LPAD( SUBSTRING( DIA_EJECUCION_INPUT,3,2)  ,2, '0') || SUBSTRING( DIA_EJECUCION_INPUT,1,2) || '|' || '2025' || LPAD( SUBSTRING( DIA_EJECUCION_INPUT,3,2) + 6 ,2, '0') || SUBSTRING( DIA_EJECUCION_INPUT,1,2)
        WHEN FRECUENCIA_INPUT = 'DIARIO' THEN 'ALL'
		WHEN FRECUENCIA_INPUT = 'MENSUAL' THEN 
		TO_CHAR(CURRENT_DATE, 'YYYY') || LPAD( SUBSTRING( DIA_EJECUCION_INPUT,3,2)  ,2, '0') || SUBSTRING( DIA_EJECUCION_INPUT,1,2) || '|' ||
		TO_CHAR(CURRENT_DATE, 'YYYY') || LPAD( SUBSTRING( DIA_EJECUCION_INPUT,3,2) + 1 ,2, '0') || SUBSTRING( DIA_EJECUCION_INPUT,1,2)|| '|' ||
		TO_CHAR(CURRENT_DATE, 'YYYY') || LPAD( SUBSTRING( DIA_EJECUCION_INPUT,3,2) + 2 ,2, '0') || SUBSTRING( DIA_EJECUCION_INPUT,1,2)|| '|' ||
		TO_CHAR(CURRENT_DATE, 'YYYY') || LPAD( SUBSTRING( DIA_EJECUCION_INPUT,3,2) + 3 ,2, '0') || SUBSTRING( DIA_EJECUCION_INPUT,1,2)|| '|' ||
		TO_CHAR(CURRENT_DATE, 'YYYY') || LPAD( SUBSTRING( DIA_EJECUCION_INPUT,3,2) + 4 ,2, '0') || SUBSTRING( DIA_EJECUCION_INPUT,1,2)|| '|' ||
		TO_CHAR(CURRENT_DATE, 'YYYY') || LPAD( SUBSTRING( DIA_EJECUCION_INPUT,3,2) + 5 ,2, '0') || SUBSTRING( DIA_EJECUCION_INPUT,1,2)|| '|' ||
		TO_CHAR(CURRENT_DATE, 'YYYY') || LPAD( SUBSTRING( DIA_EJECUCION_INPUT,3,2) + 6 ,2, '0') || SUBSTRING( DIA_EJECUCION_INPUT,1,2)|| '|' ||
		TO_CHAR(CURRENT_DATE, 'YYYY') || LPAD( SUBSTRING( DIA_EJECUCION_INPUT,3,2) + 7 ,2, '0') || SUBSTRING( DIA_EJECUCION_INPUT,1,2)|| '|' ||
		TO_CHAR(CURRENT_DATE, 'YYYY') || LPAD( SUBSTRING( DIA_EJECUCION_INPUT,3,2) + 8 ,2, '0') || SUBSTRING( DIA_EJECUCION_INPUT,1,2)|| '|' ||
		TO_CHAR(CURRENT_DATE, 'YYYY') || LPAD( SUBSTRING( DIA_EJECUCION_INPUT,3,2) + 9 ,2, '0') || SUBSTRING( DIA_EJECUCION_INPUT,1,2)|| '|' ||
		TO_CHAR(CURRENT_DATE, 'YYYY') || LPAD( SUBSTRING( DIA_EJECUCION_INPUT,3,2) + 10 ,2, '0') || SUBSTRING( DIA_EJECUCION_INPUT,1,2)|| '|' ||
		TO_CHAR(CURRENT_DATE, 'YYYY') || LPAD( SUBSTRING( DIA_EJECUCION_INPUT,3,2) + 11 ,2, '0') || SUBSTRING( DIA_EJECUCION_INPUT,1,2)
		WHEN FRECUENCIA_INPUT = 'TRIMESTRAL' THEN 
		TO_CHAR(CURRENT_DATE, 'YYYY') || LPAD( SUBSTRING( DIA_EJECUCION_INPUT,3,2)  ,2, '0') || SUBSTRING( DIA_EJECUCION_INPUT,1,2) || '|' ||
		TO_CHAR(CURRENT_DATE, 'YYYY') || LPAD( SUBSTRING( DIA_EJECUCION_INPUT,3,2) + 3 ,2, '0') || SUBSTRING( DIA_EJECUCION_INPUT,1,2)|| '|' ||
		TO_CHAR(CURRENT_DATE, 'YYYY') || LPAD( SUBSTRING( DIA_EJECUCION_INPUT,3,2) + 6 ,2, '0') || SUBSTRING( DIA_EJECUCION_INPUT,1,2)|| '|' ||
		TO_CHAR(CURRENT_DATE, 'YYYY') || LPAD( SUBSTRING( DIA_EJECUCION_INPUT,3,2) + 9 ,2, '0') || SUBSTRING( DIA_EJECUCION_INPUT,1,2)
    	END AS CAMPO_RESULTADO
FROM CONTROL_MAKO..T_CATA_INPUTS_NORMA
WHERE FRECUENCIA_REPO NOT IN ('DIARIO','UNICA_VEZ')
--AND NOMBRE_PROCESO_REPO = 'T_AGR_NRM_TRAF_MOVIL_DPTOTECNO'
;
    """
    
    try:
        conn = conectar_netezza()
        df = pd.read_sql(query, conn)
        #print(df)
        conn.close()
        return df
    except Exception as e:
        print(f"Error al obtener datos: {e}")
        return None

def generar_calendario(df):
    # Traducción de los nombres de los meses
    meses_es = {
        "January": "Enero", "February": "Febrero", "March": "Marzo",
        "April": "Abril", "May": "Mayo", "June": "Junio",
        "July": "Julio", "August": "Agosto", "September": "Septiembre",
        "October": "Octubre", "November": "Noviembre", "December": "Diciembre"
    }

    # Definir los colores de forma estática
    colores = {
        'ANUAL': '#00BFFF',  # CELESTE
        'SEMESTRAL': '#FFA500',  # NARANJA
        'TRIMESTRAL': '#008000',  # VERDE
        'MENSUAL': '#FFFF00',  # AMARILLO
        'PLANTA': '#FF1B00',  # ROJO
        'DIARIO': '#FF00BF' # PURPURA
    }
    
    calendario = {}

    for mes in range(1, 13):
        primer_dia = datetime(2025, mes, 1)
        offset = (primer_dia.weekday() + 1) % 7
        mes_nombre_es = meses_es[primer_dia.strftime('%B')]  # Traducir mes
        calendario[mes_nombre_es] = {"offset": offset, "dias": {}}

    for _, row in df.iterrows():        

        fechas = row["CAMPO_RESULTADO"].split("|")
        for fecha in fechas:
            if len(fecha) != 8 or not fecha.isdigit():
                print(f"⚠️ Fecha inválida en la base de datos: {fecha}")
                #print(df)
                continue  # Saltar fechas incorrectas

            anio, mes, dia = int(fecha[:4]), int(fecha[4:6]), int(fecha[6:8])

            if not (1 <= mes <= 12):
                print(f"⚠️ Mes fuera de rango: {mes} en fecha {fecha}")
                continue  # Evitar error de mes inválido

            try:
                mes_str = meses_es[datetime(anio, mes, 1).strftime('%B')]  # Traducir mes

                if dia not in calendario[mes_str]["dias"]:
                    calendario[mes_str]["dias"][dia] = []

                # Usar el color basado en la frecuencia del reporte
                color = colores.get(row["FRECUENCIA_REPO"], "#CCCCCC")

                calendario[mes_str]["dias"][dia].append(
                    (row["NOMBRE_PROCESO_REPO"], color)
                )
            except ValueError as e:
                print(f"⚠️ Error al procesar fecha {fecha}: {e}")
                continue  # Evitar crasheo si hay fechas raras

    return calendario

@calendario_bp.route('/calendario')

def mostrar_calendario():
    df = obtener_datos()
    #print(df)
    if df is not None:
        calendario_es = generar_calendario(df)
        return render_template("calendario.html", calendario=calendario_es) 
    else:
        return render_template("error.html", mensaje="Error al obtener los datos del calendario.")
