#from flask import Blueprint, request, jsonify, render_template
#import requests
#import json
#import re
#from app.db import conectar_netezza  # Importa la conexión centralizada
#
## Crear blueprint para el chatbox
#chatbox_bp = Blueprint('chatbox', __name__)
#
## ========= FUNCIÓN PARA CONSULTAR EL CATÁLOGO ============
#def buscar_catalogo_reportes(pregunta):
#    conn = conectar_netezza()
#    cursor = conn.cursor()
#
#    pregunta_limpia = re.sub(r"[¿?¡!]", "", pregunta.lower()).strip()
#
#    # ?? Lógica especial para conteos específicos
#    if "trimestral" in pregunta_limpia and "cuántos" in pregunta_limpia:
#        try:
#            cursor.execute("SELECT COUNT(*) FROM CONTROL_MAKO..T_CATA_REPORTES_NORMA WHERE UPPER(FRECUENCIA_REPO) = 'TRIMESTRAL'")
#            resultado = cursor.fetchone()[0]
#            return f"?? Tienes {resultado} reportes trimestrales registrados en la norma."
#        except Exception as e:
#            return f"? Error al consultar cantidad de reportes: {str(e)}"
#        finally:
#            cursor.close()
#            conn.close()
#
#    # ?? Consulta por coincidencia textual en nombre/alcances
#    query = """
#    SELECT 
#        A.SECUENCIA_REPORTE, A.NOMBRE_PROCESO_REPO, A.TIPO_REPO, A.FRECUENCIA_REPO, 
#        A.DIA_EJECUCION_REPO, A.HORA_EJECUCION_REPO, A.FRAME_EJECUTA_SP, A.LOG_NOMBRE_SP, 
#        A.ALCANCE_FUNCIONAL, A.ALCANCE_TECNICO, A.TABLA_HISTORICA,
#        B.SECUENCIA_INPUT, B.NOMBRE_INPUT, B.FRECUENCIA_INPUT, 
#        B.DIA_EJECUCION_INPUT, B.HORA_EJECUCION_INPUT, B.FILTRO_CAMPO, B.SCHEMA_INPUT 
#    FROM CONTROL_MAKO..T_CATA_REPORTES_NORMA A 
#    JOIN CONTROL_MAKO..T_CATA_INPUTS_NORMA B 
#        ON POSITION('|' || B.SECUENCIA_INPUT || '|' IN '|' || A.RELACION || '|') > 0 
#    WHERE LOWER(A.NOMBRE_PROCESO_REPO) LIKE ?
#       OR LOWER(A.ALCANCE_FUNCIONAL) LIKE ?
#       OR LOWER(A.ALCANCE_TECNICO) LIKE ?
#    LIMIT 5
#    """
#
#    try:
#        like_str = f"%{pregunta_limpia}%"
#        cursor.execute(query, (like_str, like_str, like_str))
#        filas = cursor.fetchall()
#
#        if not filas:
#            return "?? No se encontraron reportes relacionados con tu búsqueda."
#
#        respuesta = "?? Reportes encontrados:\n\n"
#        for fila in filas:
#            (
#                sec_repo, nombre_repo, tipo_repo, frec_repo, dia_repo, hora_repo,
#                sp_repo, log_sp, alc_func, alc_tec, tabla_hist,
#                sec_input, nom_input, frec_input, dia_input, hora_input,
#                filtro, schema_input
#            ) = fila
#
#            respuesta += f"""• **{nombre_repo}**
#  - Tipo: {tipo_repo} | Frecuencia: {frec_repo}
#  - Día/Hora de ejecución: {dia_repo} / {hora_repo}
#  - Tabla histórica: `{tabla_hist}`
#  - SP de ejecución: `{sp_repo}` | LOG: `{log_sp}`
#  - ?? Input: {nom_input} (Frecuencia: {frec_input}, Filtro: {filtro}, Esquema: {schema_input})
#  - Funcional: {alc_func}
#  - Técnico: {alc_tec}\n\n"""
#
#    except Exception as e:
#        respuesta = f"? Error al consultar reportes: {str(e)}"
#
#    finally:
#        cursor.close()
#        conn.close()
#
#    return respuesta
#
## ====== INTERFAZ DE USUARIO (HTML) ========
#@chatbox_bp.route('/chatbox')
#def chatbox_home():
#    return render_template('chatbox.html')
#
## ====== PREGUNTA DEL USUARIO (POST) =======
#@chatbox_bp.route('/chatbox/preguntar', methods=['POST'])
#def preguntar():
#    pregunta = request.json.get('pregunta', '')
#
#    if any(p in pregunta.lower() for p in ['reporte', 'input', 'frecuencia', 'ejecución', 'histórica', 'filtro']):
#        respuesta = buscar_catalogo_reportes(pregunta)
#    else:
#        try:
#            # Solicitar respuesta al modelo (Ollama)
#            response = requests.post(
#                'http://localhost:11434/api/generate',
#                headers={"Content-Type": "application/json"},
#                data=json.dumps({
#                    "model": "llama3",
#                    "prompt": pregunta,
#                    "stream": False
#                })
#            )
#            data = response.json()
#            respuesta_llama = data.get('response', '').strip()
#
#            # Buscar SQL tipo SELECT en la respuesta
#            match = re.search(r"(SELECT\s.+?;)", respuesta_llama, re.IGNORECASE | re.DOTALL)
#            if match:
#                sql = match.group(1).strip().rstrip(';')
#
#                # Validación básica para seguridad
#                if not sql.lower().startswith("select"):
#                    respuesta = f"{respuesta_llama}\n\n?? Consulta detectada no es del tipo SELECT. No se ejecuta por seguridad."
#                else:
#                    try:
#                        conn = conectar_netezza()
#                        cursor = conn.cursor()
#                        cursor.execute(sql)
#
#                        columnas = [desc[0] for desc in cursor.description]
#                        filas = cursor.fetchall()
#
#                        if not filas:
#                            resultado_sql = "? Consulta ejecutada, pero no se encontraron resultados."
#                        else:
#                            resultado_sql = "?? Resultado SQL:\n"
#                            for fila in filas[:3]:  # Limita a 3 registros
#                                fila_dict = dict(zip(columnas, fila))
#                                resultado_sql += "- " + ", ".join(f"{k}: {v}" for k, v in fila_dict.items()) + "\n"
#
#                    except Exception as sql_error:
#                        resultado_sql = f"? Error al ejecutar la SQL: {str(sql_error)}"
#                    finally:
#                        cursor.close()
#                        conn.close()
#
#                    respuesta = f"{respuesta_llama}\n\n{resultado_sql}"
#            else:
#                respuesta = respuesta_llama
#
#        except Exception as e:
#            respuesta = f"? Error al comunicarse con el modelo: {str(e)}"
#
#    return jsonify({'respuesta': respuesta})