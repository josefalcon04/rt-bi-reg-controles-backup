from flask import Blueprint, render_template
from app.db import conectar_teradata

monitoreo_tera_bp = Blueprint(
    'monitoreo_tera',
    __name__
)

@monitoreo_tera_bp.route('/monitoreo-teradata')
def obtener_datos():

    conn = conectar_teradata()

    if conn is None:
        return "No se pudo conectar a Teradata", 500

    cursor = None

    try:

        cursor = conn.cursor()

        query = """
        SELECT
        NombreLayout,TipoSchd,ejecutable,FecIniEjec_TS,FecFinEjec_TS,FecIni,HorIni,
        HorMaxEjec,FecCreaTS,desEstado
        FROM PE_REG_P_FG_CONFIG.VW_SCHEDULE_MATRIZ
        """

        cursor.execute(query)

        columnas = [desc[0] for desc in cursor.description]

        resultados = cursor.fetchall()

        data = [
            dict(zip(columnas, fila))
            for fila in resultados
        ]

        total = len(data)

        finalizados = sum(
            1 for x in data
            if x.get("DesEstado") == "Schedule Finalizado"
        )

        pendientes = sum(
            1 for x in data
            if x.get("DesEstado") == "Schedule Pendiente"
        )

        errores = sum(
            1 for x in data
            if "error" in str(
                x.get("DesEstado", "")
            ).lower()
        )

        return render_template(
            "monitoreo_tera.html",
            datos=data,
            total=total,
            finalizados=finalizados,
            pendientes=pendientes,
            errores=errores
        )

    except Exception as e:

        print(f"Error al obtener datos: {e}")

        return f"Error: {e}", 500

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()