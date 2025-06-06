from flask import Blueprint, render_template
from app.db import conectar_netezza  # Importa la conexión centralizada

caracteres_bp = Blueprint('caracteres', __name__)

@caracteres_bp.route('/caracteres')

def mostrar_caracteres():
    conn = conectar_netezza()
    cursor = conn.cursor()
    
    query = """
    SELECT 
T_SCHEMA,  NOMBRE_TABLA,  CAMPO,  TIPO_CAMPO,  FLAG_NULOS,  TOT_NULOS,  PERIODOS_NULOS,  FLAG_EXTR,  TOT_EXTR,  PERIODOS_EXTR,  FECHA_CARGA
FROM (
SELECT 
CODIGO,  T_SCHEMA,  NOMBRE_TABLA,  CAMPO,  TIPO_CAMPO,  FLAG_NULOS,  TOT_NULOS,  PERIODOS_NULOS,  FLAG_EXTR,  TOT_EXTR,  PERIODOS_EXTR,  FECHA_CARGA,
ROW_NUMBER() OVER (PARTITION BY NOMBRE_TABLA,CAMPO, FECHA_CARGA ORDER BY NOMBRE_TABLA, FECHA_CARGA) AS NUM_FILA
FROM CONTROL_MAKO..T_AGR_CALIDAD_NORMA
--WHERE FLAG_EXTR = 'SI' OR FLAG_NULOS = 'SI'
) AS X 
WHERE X.NUM_FILA = 1
ORDER BY FLAG_NULOS desc,FLAG_EXTR desc
    """
    cursor.execute(query)
    resultados = cursor.fetchall()

    columnas = [desc[0] for desc in cursor.description]
    data = [dict(zip(columnas, fila)) for fila in resultados]

    cursor.close()
    conn.close()

    return render_template("caracteres.html", datos=data)
