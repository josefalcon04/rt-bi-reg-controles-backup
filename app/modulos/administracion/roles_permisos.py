from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from app.servicios.bases.netezza import conectar_netezza


# =========================================================
# BLUEPRINT
# =========================================================

roles_permisos_bp = Blueprint(
    "roles_permisos",
    __name__,
    url_prefix="/administracion/roles-permisos"
)


# =========================================================
# LISTAR ROLES Y PERMISOS
# =========================================================

@roles_permisos_bp.route("/")
def index():

    conn = None
    cursor = None

    try:

        conn = conectar_netezza()
        cursor = conn.cursor()


        # =================================================
        # ROLES
        # =================================================

        cursor.execute("""
            SELECT
                ID_ROL,
                NOMBRE_ROL,
                DESCRIPCION,
                ESTADO
            FROM CONTROL_MAKO..TABLERO_ROLES
            WHERE ESTADO = 'A'
            ORDER BY ID_ROL
        """)

        roles = cursor.fetchall()


        # =================================================
        # PERMISOS
        # =================================================

        cursor.execute("""
            SELECT
                ID_PERMISO,
                CODIGO,
                DESCRIPCION,
                ESTADO
            FROM CONTROL_MAKO..TABLERO_PERMISOS
            WHERE ESTADO = 'A'
            ORDER BY ID_PERMISO
        """)

        permisos = cursor.fetchall()


        # =================================================
        # RELACIONES ROL - PERMISO
        # =================================================

        cursor.execute("""
            SELECT
                ID_ROL,
                ID_PERMISO
            FROM CONTROL_MAKO..TABLERO_ROL_PERMISOS
            ORDER BY ID_ROL, ID_PERMISO
        """)

        relaciones = cursor.fetchall()


        # =================================================
        # CONSTRUIR DICCIONARIO
        # =================================================

        permisos_por_rol = {}


        for relacion in relaciones:

            id_rol = int(relacion[0])
            id_permiso = int(relacion[1])


            if id_rol not in permisos_por_rol:

                permisos_por_rol[id_rol] = []


            permisos_por_rol[id_rol].append(
                id_permiso
            )


        print(
            "=========================================="
        )

        print(
            "[ROLES]",
            len(roles)
        )

        print(
            "[PERMISOS]",
            len(permisos)
        )

        print(
            "[RELACIONES]",
            len(relaciones)
        )

        print(
            "[PERMISOS POR ROL]",
            permisos_por_rol
        )

        print(
            "=========================================="
        )


        return render_template(
            "administracion/roles_permisos.html",
            roles=roles,
            permisos=permisos,
            permisos_por_rol=permisos_por_rol
        )


    except Exception as e:

        print(
            "=========================================="
        )

        print(
            "[ERROR ROLES_PERMISOS]"
        )

        print(
            str(e)
        )

        print(
            "=========================================="
        )


        flash(
            f"Error al cargar roles y permisos: {str(e)}",
            "error"
        )


        # IMPORTANTE:
        # No ocultamos el problema devolviendo
        # simplemente una pantalla vacía.

        return render_template(
            "administracion/roles_permisos.html",
            roles=[],
            permisos=[],
            permisos_por_rol={}
        )


    finally:

        if cursor:

            cursor.close()


        if conn:

            conn.close()



# =========================================================
# GUARDAR PERMISOS
# =========================================================

@roles_permisos_bp.route(
    "/guardar",
    methods=["POST"]
)
def guardar():

    conn = None
    cursor = None

    try:

        # =================================================
        # ROL
        # =================================================

        id_rol = request.form.get(
            "id_rol",
            ""
        ).strip()


        if not id_rol:

            flash(
                "Debe seleccionar un rol.",
                "error"
            )

            return redirect(
                url_for(
                    "roles_permisos.index"
                )
            )


        id_rol = int(id_rol)


        # =================================================
        # PERMISOS
        # =================================================

        permisos_seleccionados = request.form.getlist(
            "permisos"
        )


        permisos_seleccionados = [

            int(id_permiso)

            for id_permiso in permisos_seleccionados

            if str(id_permiso).isdigit()

        ]


        # =================================================
        # CONEXIÓN
        # =================================================

        conn = conectar_netezza()
        cursor = conn.cursor()


        # =================================================
        # VALIDAR ROL
        # =================================================

        cursor.execute("""
            SELECT
                COUNT(*)
            FROM CONTROL_MAKO..TABLERO_ROLES
            WHERE ID_ROL = ?
              AND ESTADO = 'A'
        """, (
            id_rol,
        ))


        resultado = cursor.fetchone()


        if not resultado or resultado[0] == 0:

            flash(
                "El rol seleccionado no existe o está inactivo.",
                "error"
            )

            return redirect(
                url_for(
                    "roles_permisos.index"
                )
            )


        # =================================================
        # ELIMINAR RELACIONES ACTUALES
        # =================================================

        cursor.execute("""
            DELETE FROM CONTROL_MAKO..TABLERO_ROL_PERMISOS
            WHERE ID_ROL = ?
        """, (
            id_rol,
        ))


        # =================================================
        # INSERTAR NUEVAS RELACIONES
        # =================================================

        for id_permiso in permisos_seleccionados:

            cursor.execute("""
                INSERT INTO CONTROL_MAKO..TABLERO_ROL_PERMISOS
                (
                    ID_ROL,
                    ID_PERMISO
                )
                VALUES
                (
                    ?,
                    ?
                )
            """, (
                id_rol,
                id_permiso
            ))


        # =================================================
        # COMMIT
        # =================================================

        conn.commit()


        flash(
            "Permisos del rol actualizados correctamente.",
            "success"
        )


    except ValueError:

        if conn:

            conn.rollback()


        flash(
            "El rol seleccionado no es válido.",
            "error"
        )


    except Exception as e:

        if conn:

            conn.rollback()


        print(
            "[ERROR GUARDAR ROLES_PERMISOS]",
            str(e)
        )


        flash(
            f"Error al guardar permisos: {str(e)}",
            "error"
        )


    finally:

        if cursor:

            cursor.close()


        if conn:

            conn.close()


    return redirect(
        url_for(
            "roles_permisos.index"
        )
    )