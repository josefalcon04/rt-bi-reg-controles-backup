from app.servicios.bases.connection_manager import conectar_netezza


# ==========================================
# Obtiene los favoritos del usuario
# ==========================================

def obtener_favoritos(id_usuario):

    conn = conectar_netezza()
    cursor = conn.cursor()

    sql = """
    SELECT ID_MENU
    FROM CONTROL_MAKO..TABLERO_FAVORITOS
    WHERE ID_USUARIO = ?
    """

    cursor.execute(sql, (id_usuario,))

    favoritos = [fila[0] for fila in cursor.fetchall()]

    cursor.close()
    conn.close()

    return favoritos


# ==========================================
# Verifica si un menú ya es favorito
# ==========================================

def es_favorito(id_usuario, id_menu):

    conn = conectar_netezza()
    cursor = conn.cursor()

    sql = """
    SELECT COUNT(*)
    FROM CONTROL_MAKO..TABLERO_FAVORITOS
    WHERE ID_USUARIO = ?
      AND ID_MENU = ?
    """

    cursor.execute(sql, (id_usuario, id_menu))

    existe = cursor.fetchone()[0] > 0

    cursor.close()
    conn.close()

    return existe


# ==========================================
# Agregar favorito
# ==========================================

def agregar_favorito(id_usuario, id_menu):

    conn = conectar_netezza()
    cursor = conn.cursor()

    sql = """
    INSERT INTO CONTROL_MAKO..TABLERO_FAVORITOS
    (
        ID_USUARIO,
        ID_MENU
    )
    VALUES
    (?, ?)
    """

    cursor.execute(sql, (id_usuario, id_menu))

    conn.commit()

    cursor.close()
    conn.close()


# ==========================================
# Eliminar favorito
# ==========================================

def eliminar_favorito(id_usuario, id_menu):

    conn = conectar_netezza()
    cursor = conn.cursor()

    sql = """
    DELETE
    FROM CONTROL_MAKO..TABLERO_FAVORITOS
    WHERE ID_USUARIO = ?
      AND ID_MENU = ?
    """

    cursor.execute(sql, (id_usuario, id_menu))

    conn.commit()

    cursor.close()
    conn.close()


# ==========================================
# Alternar favorito
# ==========================================

def toggle_favorito(id_usuario, id_menu):

    if es_favorito(id_usuario, id_menu):

        eliminar_favorito(id_usuario, id_menu)

        return False

    agregar_favorito(id_usuario, id_menu)

    return True