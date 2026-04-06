from app.db import conectar_netezza


def ejecutar_query(sql):

    conn = conectar_netezza()

    try:

        cursor = conn.cursor()

        cursor.execute(sql)

        columnas = [col[0] for col in cursor.description]

        filas = cursor.fetchall()

        resultado = []

        for fila in filas:

            resultado.append(
                dict(zip(columnas, fila))
            )

        return resultado

    finally:

        conn.close()