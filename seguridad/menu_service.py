from app.servicios.bases.connection_manager import conectar_netezza
from seguridad.favoritos_service import obtener_favoritos


def obtener_menus_usuario(id_usuario):
    """
    Obtiene el árbol de menús permitido para el usuario
    y marca cuáles son favoritos.

    Flujo:

        USUARIO
            ↓
        ROL
            ↓
        ROL_PERMISOS
            ↓
        PERMISOS
            ↓
        MENUS
    """

    conn = None
    cursor = None

    try:

        conn = conectar_netezza()
        cursor = conn.cursor()

        # ==========================================
        # MENÚS PERMITIDOS PARA EL USUARIO
        # ==========================================

        sql = """
        SELECT DISTINCT
            M.ID_MENU,
            M.NOMBRE_MENU,
            M.URL,
            M.BLUEPRINT,
            M.ICONO,
            M.ORDEN_MENU,
            M.ID_MENU_PADRE,
            M.ID_PERMISO,
            M.VISIBLE
        FROM CONTROL_MAKO..TABLERO_MENUS M

        INNER JOIN CONTROL_MAKO..TABLERO_PERMISOS P
            ON M.ID_PERMISO = P.ID_PERMISO

        INNER JOIN CONTROL_MAKO..TABLERO_ROL_PERMISOS RP
            ON P.ID_PERMISO = RP.ID_PERMISO

        INNER JOIN CONTROL_MAKO..TABLERO_USUARIOS U
            ON U.ID_ROL = RP.ID_ROL

        WHERE U.ID_USUARIO = ?
          AND U.ESTADO = 'A'
          AND M.ESTADO = 'A'
          AND M.VISIBLE = 'S'
          AND P.ESTADO = 'A'

        ORDER BY
            M.ORDEN_MENU,
            M.ID_MENU
        """

        cursor.execute(
            sql,
            (id_usuario,)
        )

        filas = cursor.fetchall()

        # ==========================================
        # LOG DE CONTROL
        # ==========================================

        print("==========================================")
        print("MENU SERVICE")
        print("ID_USUARIO:", id_usuario)
        print("MENUS ENCONTRADOS:", len(filas))

        for fila in filas:

            print(
                "MENU:",
                fila[0],
                "|",
                fila[1],
                "| PERMISO:",
                fila[7]
            )

        print("==========================================")

        # ==========================================
        # FAVORITOS DEL USUARIO
        # ==========================================

        favoritos_usuario = obtener_favoritos(
            id_usuario
        )

        # ==========================================
        # CONSTRUCCIÓN DE MENÚS
        # ==========================================

        todos = []

        favoritos = []

        for fila in filas:

            url = fila[2] or ""

            es_externo = (
                url.startswith("http://")
                or
                url.startswith("https://")
            )

            menu = {

                "id_menu": fila[0],

                "nombre": fila[1],

                "url": url,

                "blueprint": fila[3],

                "icono": fila[4],

                "orden": fila[5],

                "padre": fila[6],

                "id_permiso": fila[7],

                "es_externo": es_externo,

                "favorito": (
                    fila[0]
                    in favoritos_usuario
                ),

                "hijos": []

            }

            todos.append(menu)

            if menu["favorito"]:

                favoritos.append(menu)

        # ==========================================
        # MENÚS PRINCIPALES
        # ==========================================

        menus = []

        for menu in todos:

            if menu["padre"] == 0:

                menus.append(menu)

        # ==========================================
        # SUBMENÚS
        # ==========================================

        for menu in todos:

            if menu["padre"] != 0:

                for padre in menus:

                    if (
                        padre["id_menu"]
                        == menu["padre"]
                    ):

                        padre["hijos"].append(
                            menu
                        )

                        break

        # ==========================================
        # ORDENAR HIJOS
        # ==========================================

        for padre in menus:

            padre["hijos"].sort(
                key=lambda x: (
                    x["orden"]
                    if x["orden"] is not None
                    else 999999
                )
            )

        return menus, favoritos

    except Exception as e:

        print("==========================================")
        print("ERROR EN MENU SERVICE")
        print("ID_USUARIO:", id_usuario)
        print("ERROR:", str(e))
        print("==========================================")

        return [], []

    finally:

        if cursor:

            cursor.close()

        if conn:

            conn.close()
def obtener_permisos_usuario(id_usuario):
    """
    Obtiene todos los permisos activos del usuario.

    Flujo:

        USUARIO
            ↓
        ROL
            ↓
        ROL_PERMISOS
            ↓
        PERMISOS
    """

    conn = None
    cursor = None

    try:

        conn = conectar_netezza()
        cursor = conn.cursor()

        sql = """
        SELECT DISTINCT
            P.CODIGO
        FROM CONTROL_MAKO..TABLERO_USUARIOS U

        INNER JOIN CONTROL_MAKO..TABLERO_ROL_PERMISOS RP
            ON U.ID_ROL = RP.ID_ROL

        INNER JOIN CONTROL_MAKO..TABLERO_PERMISOS P
            ON RP.ID_PERMISO = P.ID_PERMISO

        WHERE U.ID_USUARIO = ?
          AND U.ESTADO = 'A'
          AND P.ESTADO = 'A'

        ORDER BY P.CODIGO
        """

        cursor.execute(
            sql,
            (id_usuario,)
        )

        filas = cursor.fetchall()

        permisos = [
            fila[0]
            for fila in filas
            if fila[0]
        ]

        print("==========================================")
        print("PERMISOS SERVICE")
        print("ID_USUARIO:", id_usuario)
        print("PERMISOS:", permisos)
        print("==========================================")

        return permisos

    except Exception as e:

        print("==========================================")
        print("ERROR EN PERMISOS SERVICE")
        print("ID_USUARIO:", id_usuario)
        print("ERROR:", str(e))
        print("==========================================")

        return []

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()            