from app.servicios.bases.connection_manager import conectar_netezza


def obtener_permisos(id_rol):

    conn = None
    cursor = None

    try:

        conn = conectar_netezza()
        cursor = conn.cursor()

        sql = """
            SELECT
                P.CODIGO
            FROM CONTROL_MAKO..TABLERO_PERMISOS P
            INNER JOIN CONTROL_MAKO..TABLERO_ROL_PERMISOS RP
                ON RP.ID_PERMISO = P.ID_PERMISO
            WHERE RP.ID_ROL = %s
              AND P.ESTADO = 'A'
        """

        cursor.execute(
            sql,
            (id_rol,)
        )

        permisos = [
            fila[0]
            for fila in cursor.fetchall()
        ]

        return permisos

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()