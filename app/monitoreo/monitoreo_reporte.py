from flask import Flask, render_template, request, jsonify, Blueprint, url_for
from app.db import conectar_netezza  # Importa la conexión centralizada

monitoreo_norma_bp = Blueprint('monitoreo_norma', __name__)

def obtener_reportes():
    conn = conectar_netezza()
    cursor = conn.cursor()
    
    # Consulta SQL para obtener los reportes
    cursor.execute("""
    SELECT NOMBRE_REPORTE, INDICADOR_COLOR, FRECUENCIA, NOMBRE_ORIGINAL
FROM (
    SELECT DISTINCT 
        CASE 
            WHEN NOMBRE_PROCESO_REPO = 'INEI CUADRO 1 - BLOQUE 1' THEN 'INEI1-B01'
            WHEN NOMBRE_PROCESO_REPO = 'INEI CUADRO 1 - BLOQUE 2' THEN 'INEI1-B03'
            WHEN NOMBRE_PROCESO_REPO = 'INEI CUADRO 1 - BLOQUE 3' THEN 'INEI1-B03'
            WHEN NOMBRE_PROCESO_REPO = 'INEI CUADRO 2' THEN 'INEI2-B00'
            WHEN NOMBRE_PROCESO_REPO = 'INFORME TRAFICO (RT)' THEN 'TRAFI-RT1'
            ELSE NOMBRE_PROCESO_REPO
        END AS nombre_reporte,    
        CASE
            WHEN EJECUCION = 'EXITO' THEN 'green'
            WHEN EJECUCION = 'PENDIENTE' THEN 'yellow'
            WHEN EJECUCION = 'ERROR' THEN 'red'
            ELSE 'grey'
        END AS indicador_color,
        frecuencia_repo AS frecuencia,
        NOMBRE_PROCESO_REPO AS nombre_original,
        periodo,
        MAX(PERIODO) OVER (PARTITION BY 
            CASE 
                WHEN NOMBRE_PROCESO_REPO = 'INEI CUADRO 1 - BLOQUE 1' THEN 'INEI1-B01'
                WHEN NOMBRE_PROCESO_REPO = 'INEI CUADRO 1 - BLOQUE 2' THEN 'INEI1-B03'
                WHEN NOMBRE_PROCESO_REPO = 'INEI CUADRO 1 - BLOQUE 3' THEN 'INEI1-B03'
                WHEN NOMBRE_PROCESO_REPO = 'INEI CUADRO 2' THEN 'INEI2-B00'
                WHEN NOMBRE_PROCESO_REPO = 'INFORME TRAFICO (RT)' THEN 'TRAFI-RT1'
                ELSE NOMBRE_PROCESO_REPO
            END, frecuencia_repo) AS MAX_PERIODO
    FROM CONTROL_MAKO..T_AGR_NORMA_CONTROL
    WHERE SUBSTRING(PERIODO, 1, 4) IN ('2024', '2025')
) AS X
WHERE PERIODO = MAX_PERIODO  -- Solo tomamos el máximo periodo por grupo
ORDER BY frecuencia, nombre_reporte;

    """)

    resultados = cursor.fetchall()

    reportes_trimestrales = []
    reportes_mensuales = []
    reportes_semestrales = []
    reportes_anuales = []
    
    # Agrupamos los reportes por frecuencia
    for reporte in resultados:
        nombre_reporte = reporte[0]
        indicador_color = reporte[1]
        frecuencia = reporte[2]
        nombre_original = reporte[3]  # Nombre original en la base de datos

        reporte_data = {
            'nombre': nombre_reporte,
            'indicador': indicador_color,
            'nombre_original': nombre_original
        }

        if frecuencia == 'TRIMESTRAL':
            reportes_trimestrales.append(reporte_data)
        elif frecuencia == 'MENSUAL':
            reportes_mensuales.append(reporte_data)
        elif frecuencia == 'SEMESTRAL':
            reportes_semestrales.append(reporte_data)
        elif frecuencia == 'ANUAL':
            reportes_anuales.append(reporte_data)

    conn.close()
    
    return {
        'reportes_trimestrales': reportes_trimestrales,
        'reportes_mensuales': reportes_mensuales,
        'reportes_semestrales': reportes_semestrales,
        'reportes_anuales': reportes_anuales,
    }

@monitoreo_norma_bp.route('/reportes')
def monitoreo_reporte():
    """Renderiza la página de monitoreo con los reportes."""
    reportes = obtener_reportes()
    #print(reportes)  
    return render_template('monitoreo_norma.html', **reportes)

@monitoreo_norma_bp.route('/detalle')
def detalle_reporte():
    nombre_reporte = request.args.get("nombre")
    #print(nombre_reporte)  # Para depuración
    if not nombre_reporte:
        return "Reporte no encontrado", 404

    conn = conectar_netezza()
    cursor = conn.cursor()

    query = """
    SELECT DISTINCT
        NOMBRE_PROCESO_REPO AS nombre_reporte, 
        frecuencia_repo AS frecuencia, 
        DIA_EJECUCION_REPO, 
        EJECUCION AS indicador_color, 
        PERIODO 
    FROM CONTROL_MAKO..T_AGR_NORMA_CONTROL
    WHERE NOMBRE_PROCESO_REPO = ?
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
        return render_template("detalle_reporte.html", reporte=reporte)
    else:
        return "Reporte no encontrado", 404

# Nueva ruta para actualizar los datos sin recargar la página
@monitoreo_norma_bp.route('/actualizar_datos')
def actualizar_datos():
    reportes = obtener_reportes()
    return jsonify(reportes)  # Devuelve los datos en formato JSON
