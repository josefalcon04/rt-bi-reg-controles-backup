from app.servicios.bases.connection_manager import conectar_netezza
from seguridad.password import verificar_password


def obtener_usuario(usuario):

    conn = conectar_netezza()
    cursor = conn.cursor()

    sql = f"""
SELECT
    U.ID_USUARIO,
    U.USUARIO,
    U.NOMBRE_COMPLETO,
    U.EMAIL,
    U.PASSWORD_HASH,
    U.ID_ROL,
    R.NOMBRE_ROL,
    U.ESTADO
FROM CONTROL_MAKO..TABLERO_USUARIOS U
LEFT JOIN CONTROL_MAKO..TABLERO_ROLES R
       ON U.ID_ROL = R.ID_ROL
WHERE UPPER(U.USUARIO)=UPPER('{usuario}')
"""

    print(sql)

    cursor.execute(sql)
    fila = cursor.fetchone()

    cursor.close()
    conn.close()

    if not fila:
        return None

    return {

    "id_usuario": fila[0],
    "usuario": fila[1],
    "nombre": fila[2],
    "email": fila[3],
    "password_hash": fila[4],
    "id_rol": fila[5],
    "rol_nombre": fila[6],
    "estado": fila[7]

}


def autenticar(usuario, password):

    datos = obtener_usuario(usuario)

    if not datos:
        return None

    if datos["estado"] != "A":
        return None

    if not verificar_password(password, datos["password_hash"]):
        return None

    return datos

def actualizar_password(id_usuario, nuevo_hash):

    conn = conectar_netezza()
    cursor = conn.cursor()

    sql = f"""
    UPDATE CONTROL_MAKO..TABLERO_USUARIOS
       SET PASSWORD_HASH = '{nuevo_hash}'
     WHERE ID_USUARIO = {id_usuario}
    """

    print(sql)

    cursor.execute(sql)

    conn.commit()

    cursor.close()
    conn.close()