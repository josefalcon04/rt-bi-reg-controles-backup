from app.servicios.bases.db import conectar_netezza
import pandas as pd
import re

def consultar_logs_norma(pregunta):
    """
    Mueve aquí la lógica de consultar_logs_norma que tenías en chatbox.py.
    """
    p = pregunta.upper()
    match = re.search(r'(NRI[A-Z]*[_ ]?\d+)', p)
    
    if not match:
        return "Indica el reporte (ej. NRIPO_035) para consultar sus logs."

    reporte = match.group(1).replace(" ", "_")
    sp = f"SP_NRM_{reporte}"

    sql = f"""
        SELECT A.LOG_NOMBRE_SP, A.LOG_FECHA_INICIO, A.LOG_FECHA_FIN, A.LOG_ESTADO, 
               B.LOG_NRO_PASO, B.LOG_DETAIL
        FROM PROD_REGU_NORMA_DATA..T_NRM_LOG A
        LEFT JOIN PROD_REGU_NORMA_DATA..T_NRM_LOG_DETAIL B
            ON A.LOG_NRO_EJECUCION = B.LOG_NRO_EJECUCION
        WHERE A.LOG_NOMBRE_SP = '{sp}'
        AND A.LOG_FECHA_INICIO = (SELECT MAX(LOG_FECHA_INICIO) FROM PROD_REGU_NORMA_DATA..T_NRM_LOG WHERE LOG_NOMBRE_SP = '{sp}')
        ORDER BY B.LOG_NRO_PASO
    """

    try:
        conn = conectar_netezza()
        df = pd.read_sql(sql, conn)
        conn.close()

        if df.empty:
            return f"No encontré logs para {reporte}."

        # Aquí mantienes tu lógica de formateo de respuesta que ya tenías
        cab = df.iloc[0]
        return f"Reporte: {reporte} | Estado: {cab['LOG_ESTADO']} | Inicio: {cab['LOG_FECHA_INICIO']}"
    except Exception as e:
        return f"Error consultando logs: {str(e)}"

def consultar_alertas_norma(pregunta):
    """
    Mueve aquí la lógica de alertas. 
    Si aún no tienes la lógica, puedes empezar con una estructura base:
    """
    # Lógica de consulta a tablas de alertas en Netezza
    return "Lógica de alertas en desarrollo."