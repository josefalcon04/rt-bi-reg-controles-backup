import logging
import pandas as pd
from flask import Blueprint, jsonify
from app.db import conectar_netezza  # Tu función centralizada de conexión

notificaciones_bp = Blueprint('notificaciones', __name__)

@notificaciones_bp.route('/notificaciones')
def obtener_notificaciones():
    """
    Genera notificaciones basadas en el estado de ejecución de reportes.
    Los mensajes se construyen según los campos EJECUCION, EJECUCION_INPUT y ESTADO_REPORTE.
    """

    conn = conectar_netezza()
    if not conn:
        logging.error("❌ No se pudo conectar a Netezza")
        return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

    sql = """
    SELECT DISTINCT
        t.PERIODO,
        t.NOMBRE_PROCESO_REPO,
        t.FRECUENCIA_REPO,
        t.DIA_EJECUCION_REPO,
        t.EJECUCION,
        t.EJECUCION_INPUT,
        CASE WHEN t.ESTADO_REPORTE IS NULL THEN 'PENDIENTE' ELSE UPPER(t.ESTADO_REPORTE) END AS ESTADO_REPORTE
    FROM CONTROL_MAKO..T_AGR_NORMA_CONTROL_HIST t
    INNER JOIN (
        SELECT NOMBRE_PROCESO_REPO, MAX(PERIODO) AS MAX_PERIODO
        FROM CONTROL_MAKO..T_AGR_NORMA_CONTROL
        GROUP BY NOMBRE_PROCESO_REPO
    ) AS max_periodos 
        ON t.NOMBRE_PROCESO_REPO = max_periodos.NOMBRE_PROCESO_REPO 
       AND t.PERIODO = max_periodos.MAX_PERIODO
    WHERE (t.EJECUCION_INPUT <> 'EXITO' OR 
        t.EJECUCION <> 'EXITO' OR 
        t.ESTADO_REPORTE IS NULL) 
      AND t.PERIODO >= '202502'
    ORDER BY t.PERIODO DESC , t.NOMBRE_PROCESO_REPO ASC;
    """

    try:
        df = pd.read_sql(sql, conn)
        if df.empty:
            logging.info("✅ No hay notificaciones pendientes")
            return jsonify([])

        notificaciones = []

        for _, row in df.iterrows():
            proceso = row["NOMBRE_PROCESO_REPO"]
            periodo = str(row["PERIODO"])
            ejec = row["EJECUCION"]
            ejec_input = row["EJECUCION_INPUT"]
            estado_rep = row["ESTADO_REPORTE"]

            # --- Construcción del mensaje dinámico ---
            msg = f"[{periodo}] {proceso}: "
            detalles = []

            if ejec != "EXITO":
                detalles.append(f"Ejecución principal: {ejec}")
            if ejec_input != "EXITO":
                detalles.append(f"Input: {ejec_input}")
            if estado_rep != "EXITO" and estado_rep != "EXTRACTOR FINALIZADO":
                detalles.append(f"Estado reporte: {estado_rep}")

            if not detalles:
                detalles.append("Revisar proceso, inconsistencias detectadas")

            mensaje = msg + " | ".join(detalles)

            notificaciones.append({
                "titulo": proceso,
                "mensaje": mensaje,
                "periodo": periodo,
                "frecuencia": row["FRECUENCIA_REPO"],
                "dia": row["DIA_EJECUCION_REPO"]
            })

        return jsonify(notificaciones)

    except Exception as e:
        logging.error(f"⚠️ Error en obtener_notificaciones: {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        try:
            conn.close()
        except Exception:
            pass
