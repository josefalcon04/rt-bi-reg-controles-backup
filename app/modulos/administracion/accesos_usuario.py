from flask import (
    Blueprint,
    render_template
)

from app.servicios.bases.netezza import conectar_netezza


# =========================================================
# BLUEPRINT
# =========================================================

accesos_usuario_bp = Blueprint(
    "accesos_usuario",
    __name__,
    url_prefix="/administracion/accesos-usuario"
)


# =========================================================
# CONSULTA DE ACCESOS POR USUARIO
# =========================================================

@accesos_usuario_bp.route("/")
def index():

    conn = None
    cursor = None

    try:

        conn = conectar_netezza()
        cursor = conn.cursor()


        # =================================================
        # USUARIOS ACTIVOS
        # =================================================

        cursor.execute("""
            SELECT
                U.ID_USUARIO,
                U.USUARIO,
                U.NOMBRE_COMPLETO,
                U.EMAIL,
                U.ID_ROL,
                R.NOMBRE_ROL
            FROM CONTROL_MAKO..TABLERO_USUARIOS U

            INNER JOIN CONTROL_MAKO..TABLERO_ROLES R
                ON U.ID_ROL = R.ID_ROL

            WHERE U.ESTADO = 'A'
              AND R.ESTADO = 'A'

            ORDER BY
                U.NOMBRE_COMPLETO,
                U.USUARIO
        """)

        usuarios = cursor.fetchall()


        # =================================================
        # ACCESOS COMPLETOS
        # =================================================

        cursor.execute("""
            SELECT DISTINCT

                U.ID_USUARIO,
                U.USUARIO,
                U.NOMBRE_COMPLETO,

                R.ID_ROL,
                R.NOMBRE_ROL,

                P.ID_PERMISO,
                P.CODIGO,
                P.DESCRIPCION,

                M.ID_MENU,
                M.NOMBRE_MENU,
                M.URL,
                M.BLUEPRINT,
                M.ICONO,
                M.ORDEN_MENU,
                M.ID_MENU_PADRE,
                M.VISIBLE,
                M.ESTADO

            FROM CONTROL_MAKO..TABLERO_USUARIOS U

            INNER JOIN CONTROL_MAKO..TABLERO_ROLES R
                ON U.ID_ROL = R.ID_ROL

            INNER JOIN CONTROL_MAKO..TABLERO_ROL_PERMISOS RP
                ON R.ID_ROL = RP.ID_ROL

            INNER JOIN CONTROL_MAKO..TABLERO_PERMISOS P
                ON RP.ID_PERMISO = P.ID_PERMISO

            INNER JOIN CONTROL_MAKO..TABLERO_MENUS M
                ON P.ID_PERMISO = M.ID_PERMISO

            WHERE U.ESTADO = 'A'
              AND R.ESTADO = 'A'
              AND P.ESTADO = 'A'
              AND M.ESTADO = 'A'
              AND M.VISIBLE = 'S'

            ORDER BY
                U.USUARIO,
                M.ORDEN_MENU,
                M.ID_MENU
        """)

        accesos = cursor.fetchall()


        # =================================================
        # CONSTRUIR DATOS POR USUARIO
        # =================================================

        accesos_por_usuario = {}


        for fila in accesos:

            id_usuario = int(fila[0])


            if id_usuario not in accesos_por_usuario:

                accesos_por_usuario[id_usuario] = []


            accesos_por_usuario[id_usuario].append({

                "usuario": fila[1],

                "nombre_completo": fila[2],

                "id_rol": fila[3],

                "rol": fila[4],

                "id_permiso": fila[5],

                "codigo_permiso": fila[6],

                "descripcion_permiso": fila[7],

                "id_menu": fila[8],

                "nombre_menu": fila[9],

                "url": fila[10],

                "blueprint": fila[11],

                "icono": fila[12],

                "orden": fila[13],

                "id_menu_padre": fila[14],

                "visible": fila[15],

                "estado": fila[16]

            })


        # =================================================
        # LOG
        # =================================================

        print(
            "=========================================="
        )

        print(
            "[ACCESOS USUARIO]"
        )

        print(
            "[USUARIOS]",
            len(usuarios)
        )

        print(
            "[ACCESOS]",
            len(accesos)
        )

        print(
            "[USUARIOS CON ACCESOS]",
            len(accesos_por_usuario)
        )

        print(
            "=========================================="
        )


        return render_template(
            "administracion/accesos_usuario.html",
            usuarios=usuarios,
            accesos_por_usuario=accesos_por_usuario
        )


    except Exception as e:

        print(
            "=========================================="
        )

        print(
            "[ERROR ACCESOS USUARIO]"
        )

        print(
            str(e)
        )

        print(
            "=========================================="
        )


        return render_template(
            "administracion/accesos_usuario.html",
            usuarios=[],
            accesos_por_usuario={}
        )


    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()