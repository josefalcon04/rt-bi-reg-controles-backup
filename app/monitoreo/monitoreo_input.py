from flask import Flask, render_template, request, jsonify, Blueprint, url_for
from app.db import conectar_netezza  # Importa la conexión centralizada

monitoreo_input_bp = Blueprint('monitoreo_input', __name__)

def obtener_reportes():
    conn = conectar_netezza()
    cursor = conn.cursor()
    
    # Consulta SQL para obtener los reportes
    cursor.execute("""
    SELECT NOMBRE_INPUT, INDICADOR_COLOR, FRECUENCIA
FROM (
    SELECT DISTINCT 
        NOMBRE_INPUT,    
        CASE
            WHEN ESTADO = 'EXITO' THEN 'green'
            WHEN ESTADO = 'PENDIENTE' THEN 'yellow'
            WHEN ESTADO = 'ERROR' THEN 'red'
            ELSE 'grey'
        END AS indicador_color,
        FRECUENCIA_INPUT AS frecuencia,
        periodo,
        MAX(PERIODO) OVER (PARTITION BY 
             NOMBRE_INPUT,FRECUENCIA_INPUT) AS MAX_PERIODO
    FROM CONTROL_MAKO..T_AGR_INPUT_CONTROL
    WHERE SUBSTRING(PERIODO, 1, 4) >= '2024'
) AS X
WHERE PERIODO = MAX_PERIODO 
ORDER BY frecuencia, NOMBRE_INPUT;

    """)

    resultados = cursor.fetchall()

    reportes_trimestrales = []
    reportes_mensuales = []
    reportes_semestrales = []
    reportes_diario = []
    reportes_unicavez = []
    
    # Agrupamos los reportes por frecuencia
    for reporte in resultados:
        nombre_input = reporte[0]
        indicador_color = reporte[1]
        frecuencia = reporte[2]


        reporte_data = {
            'nombre': nombre_input,
            'indicador': indicador_color
        }

        if frecuencia == 'TRIMESTRAL':
            reportes_trimestrales.append(reporte_data)
        elif frecuencia == 'MENSUAL':
            reportes_mensuales.append(reporte_data)
        elif frecuencia == 'SEMESTRAL':
            reportes_semestrales.append(reporte_data)
        elif frecuencia == 'DIARIO':
            reportes_diario.append(reporte_data)
        elif frecuencia == 'UNICA_VEZ':
            reportes_unicavez.append(reporte_data)

    conn.close()
    
    return {
        'reportes_trimestrales': reportes_trimestrales,
        'reportes_mensuales': reportes_mensuales,
        'reportes_semestrales': reportes_semestrales,
        'reportes_diario': reportes_diario,
        'reportes_unicavez': reportes_unicavez
    }

@monitoreo_input_bp.route('/input')
def monitoreo_input():
    """Renderiza la página de monitoreo con los reportes."""
    reportes = obtener_reportes()
    #print(reportes)  
    return render_template('monitoreo_input.html', **reportes)

@monitoreo_input_bp.route('/detalle_input')
def detalle_input():
    nombre_reporte = request.args.get("nombre")
    #print(nombre_reporte)  # Para depuración
    if not nombre_reporte:
        return "Reporte no encontrado", 404

    conn = conectar_netezza()
    cursor = conn.cursor()

    query = """
    SELECT DISTINCT
        NOMBRE_INPUT AS nombre_input, 
        FRECUENCIA_INPUT AS frecuencia, 
        DIA_EJECUCION_INPUT, 
        ESTADO AS indicador_color, 
        PERIODO 
    FROM CONTROL_MAKO..T_AGR_INPUT_CONTROL
    WHERE NOMBRE_INPUT = ?;
    """
    cursor.execute(query, (nombre_reporte,))
    row = cursor.fetchone()
    
    conn.close()

    if row:
        reporte = {
            "nombre": row[0],
            "frecuencia": row[1],
            "ultima_ejecucion": row[2],
            "estado": row[3],
            "descripcion": row[4]
        }
        return render_template("detalle_input.html", reporte=reporte)
    else:
        return "Reporte no encontrado", 404

# Nueva ruta para actualizar los datos sin recargar la página
@monitoreo_input_bp.route('/actualizar_datos')
def actualizar_datos():
    reportes = obtener_reportes()
    return jsonify(reportes)  # Devuelve los datos en formato JSON
