# app/servicios/netezza_service.py

from app.servicios.bases.connection_manager import conectar_netezza



def ejecutar_query(sql):


    comandos_bloqueados = [
        "DROP",
        "DELETE",
        "UPDATE",
        "INSERT",
        "ALTER",
        "TRUNCATE"
    ]


    sql_upper = sql.upper()



    if any(
        cmd in sql_upper
        for cmd in comandos_bloqueados
    ):

        raise Exception(
            "Consulta no permitida. "
            "Solo operaciones SELECT."
        )



    conn = None
    cursor = None


    try:

        conn = conectar_netezza()

        cursor = conn.cursor()


        cursor.execute(sql)



        if cursor.description is None:

            return []



        columnas = [
            col[0]
            for col in cursor.description
        ]



        filas = cursor.fetchall()



        return [

            dict(
                zip(columnas, fila)
            )

            for fila in filas

        ]



    except Exception as e:

        raise Exception(
            f"Error ejecutando query Netezza: {str(e)}"
        )



    finally:


        if cursor:

            cursor.close()


        if conn:

            conn.close()