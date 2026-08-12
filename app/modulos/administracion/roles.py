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

roles_bp = Blueprint(
    "roles",
    __name__,
    url_prefix="/administracion/roles"
)


# =========================================================
# LISTADO DE ROLES
# =========================================================

@roles_bp.route("/")
def index():

    conn = None
    cursor = None

    try:

        conn = conectar_netezza()
        cursor = conn.cursor()

        # -------------------------------------------------
        # ROLES
        # -------------------------------------------------

        cursor.execute("""
            SELECT
                ID_ROL,
                NOMBRE_ROL,
                DESCRIPCION,
                ESTADO,
                FECHA_CREACION
            FROM CONTROL_MAKO..TABLERO_ROLES
            ORDER BY ID_ROL
        """)

        roles = cursor.fetchall()

        # -------------------------------------------------
        # PERMISOS
        # -------------------------------------------------

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

        return render_template(
            "administracion/roles.html",
            roles=roles,
            permisos=permisos
        )

    except Exception as e:

        print(
            f"[ERROR] Roles: {str(e)}"
        )

        flash(
            f"Error al consultar roles: {str(e)}",
            "error"
        )

        return render_template(
            "administracion/roles.html",
            roles=[],
            permisos=[]
        )

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# CREAR ROL
# =========================================================

@roles_bp.route("/crear", methods=["POST"])
def crear():

    conn = None
    cursor = None

    try:

        nombre_rol = request.form.get(
            "nombre_rol",
            ""
        ).strip()

        descripcion = request.form.get(
            "descripcion",
            ""
        ).strip()

        # -------------------------------------------------
        # VALIDACIONES
        # -------------------------------------------------

        if not nombre_rol:

            flash(
                "El nombre del rol es obligatorio.",
                "error"
            )

            return redirect(
                url_for("roles.index")
            )

        # -------------------------------------------------
        # CONEXIÓN
        # -------------------------------------------------

        conn = conectar_netezza()
        cursor = conn.cursor()

        # -------------------------------------------------
        # VALIDAR ROL EXISTENTE
        # -------------------------------------------------

        cursor.execute("""
            SELECT COUNT(*)
            FROM CONTROL_MAKO..TABLERO_ROLES
            WHERE UPPER(NOMBRE_ROL) = UPPER(?)
        """, (
            nombre_rol,
        ))

        existe = cursor.fetchone()[0]

        if existe > 0:

            flash(
                "El rol ya existe.",
                "error"
            )

            return redirect(
                url_for("roles.index")
            )

        # -------------------------------------------------
        # OBTENER NUEVO ID
        # -------------------------------------------------

        cursor.execute("""
            SELECT
                COALESCE(
                    MAX(ID_ROL),
                    0
                ) + 1
            FROM CONTROL_MAKO..TABLERO_ROLES
        """)

        id_rol = cursor.fetchone()[0]

        # -------------------------------------------------
        # INSERTAR ROL
        # -------------------------------------------------

        cursor.execute("""
            INSERT INTO CONTROL_MAKO..TABLERO_ROLES
            (
                ID_ROL,
                NOMBRE_ROL,
                DESCRIPCION,
                ESTADO
            )
            VALUES
            (
                ?,
                ?,
                ?,
                'A'
            )
        """, (
            id_rol,
            nombre_rol,
            descripcion
        ))

        conn.commit()

        flash(
            "Rol creado correctamente.",
            "success"
        )

    except Exception as e:

        if conn:
            conn.rollback()

        print(
            f"[ERROR] Crear rol: {str(e)}"
        )

        flash(
            f"Error al crear rol: {str(e)}",
            "error"
        )

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()

    return redirect(
        url_for("roles.index")
    )


# =========================================================
# EDITAR ROL
# =========================================================

@roles_bp.route(
    "/editar/<int:id_rol>",
    methods=["POST"]
)
def editar(id_rol):

    conn = None
    cursor = None

    try:

        nombre_rol = request.form.get(
            "nombre_rol",
            ""
        ).strip()

        descripcion = request.form.get(
            "descripcion",
            ""
        ).strip()

        # -------------------------------------------------
        # VALIDACIONES
        # -------------------------------------------------

        if not nombre_rol:

            flash(
                "El nombre del rol es obligatorio.",
                "error"
            )

            return redirect(
                url_for("roles.index")
            )

        # -------------------------------------------------
        # CONEXIÓN
        # -------------------------------------------------

        conn = conectar_netezza()
        cursor = conn.cursor()

        # -------------------------------------------------
        # VALIDAR NOMBRE DUPLICADO
        # -------------------------------------------------

        cursor.execute("""
            SELECT COUNT(*)
            FROM CONTROL_MAKO..TABLERO_ROLES
            WHERE UPPER(NOMBRE_ROL) = UPPER(?)
              AND ID_ROL <> ?
        """, (
            nombre_rol,
            id_rol
        ))

        existe = cursor.fetchone()[0]

        if existe > 0:

            flash(
                "Ya existe otro rol con ese nombre.",
                "error"
            )

            return redirect(
                url_for("roles.index")
            )

        # -------------------------------------------------
        # ACTUALIZAR
        # -------------------------------------------------

        cursor.execute("""
            UPDATE CONTROL_MAKO..TABLERO_ROLES
            SET
                NOMBRE_ROL = ?,
                DESCRIPCION = ?
            WHERE ID_ROL = ?
        """, (
            nombre_rol,
            descripcion,
            id_rol
        ))

        conn.commit()

        flash(
            "Rol actualizado correctamente.",
            "success"
        )

    except Exception as e:

        if conn:
            conn.rollback()

        print(
            f"[ERROR] Editar rol: {str(e)}"
        )

        flash(
            f"Error al actualizar rol: {str(e)}",
            "error"
        )

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()

    return redirect(
        url_for("roles.index")
    )


# =========================================================
# ACTIVAR / DESACTIVAR ROL
# =========================================================

@roles_bp.route(
    "/estado/<int:id_rol>",
    methods=["POST"]
)
def cambiar_estado(id_rol):

    conn = None
    cursor = None

    try:

        conn = conectar_netezza()
        cursor = conn.cursor()

        # -------------------------------------------------
        # OBTENER ESTADO ACTUAL
        # -------------------------------------------------

        cursor.execute("""
            SELECT
                ESTADO
            FROM CONTROL_MAKO..TABLERO_ROLES
            WHERE ID_ROL = ?
        """, (
            id_rol,
        ))

        resultado = cursor.fetchone()

        if not resultado:

            flash(
                "Rol no encontrado.",
                "error"
            )

            return redirect(
                url_for("roles.index")
            )

        estado_actual = resultado[0]

        # -------------------------------------------------
        # NUEVO ESTADO
        # -------------------------------------------------

        nuevo_estado = (
            "I"
            if estado_actual == "A"
            else "A"
        )

        # -------------------------------------------------
        # ACTUALIZAR
        # -------------------------------------------------

        cursor.execute("""
            UPDATE CONTROL_MAKO..TABLERO_ROLES
            SET
                ESTADO = ?
            WHERE ID_ROL = ?
        """, (
            nuevo_estado,
            id_rol
        ))

        conn.commit()

        flash(
            "Estado del rol actualizado correctamente.",
            "success"
        )

    except Exception as e:

        if conn:
            conn.rollback()

        print(
            f"[ERROR] Cambiar estado rol: {str(e)}"
        )

        flash(
            f"Error al cambiar estado del rol: {str(e)}",
            "error"
        )

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()

    return redirect(
        url_for("roles.index")
    )


# =========================================================
# OBTENER PERMISOS DE UN ROL
# =========================================================

@roles_bp.route(
    "/permisos/<int:id_rol>"
)
def obtener_permisos(id_rol):

    conn = None
    cursor = None

    try:

        conn = conectar_netezza()
        cursor = conn.cursor()

        # -------------------------------------------------
        # PERMISOS DISPONIBLES
        # -------------------------------------------------

        cursor.execute("""
            SELECT
                ID_PERMISO,
                CODIGO,
                DESCRIPCION
            FROM CONTROL_MAKO..TABLERO_PERMISOS
            WHERE ESTADO = 'A'
            ORDER BY ID_PERMISO
        """)

        permisos = cursor.fetchall()

        # -------------------------------------------------
        # PERMISOS ASIGNADOS AL ROL
        # -------------------------------------------------

        cursor.execute("""
            SELECT
                ID_PERMISO
            FROM CONTROL_MAKO..TABLERO_ROL_PERMISOS
            WHERE ID_ROL = ?
            ORDER BY ID_PERMISO
        """, (
            id_rol,
        ))

        permisos_asignados = [
            fila[0]
            for fila in cursor.fetchall()
        ]

        return render_template(
            "administracion/rol_permisos.html",
            id_rol=id_rol,
            permisos=permisos,
            permisos_asignados=permisos_asignados
        )

    except Exception as e:

        print(
            f"[ERROR] Obtener permisos rol: {str(e)}"
        )

        flash(
            f"Error al consultar permisos: {str(e)}",
            "error"
        )

        return redirect(
            url_for("roles.index")
        )

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# GUARDAR PERMISOS DEL ROL
# =========================================================

@roles_bp.route(
    "/permisos/<int:id_rol>/guardar",
    methods=["POST"]
)
def guardar_permisos(id_rol):

    conn = None
    cursor = None

    try:

        # -------------------------------------------------
        # PERMISOS SELECCIONADOS
        # -------------------------------------------------

        permisos_seleccionados = request.form.getlist(
            "permisos"
        )

        conn = conectar_netezza()
        cursor = conn.cursor()

        # -------------------------------------------------
        # ELIMINAR PERMISOS ACTUALES
        # -------------------------------------------------

        cursor.execute("""
            DELETE FROM CONTROL_MAKO..TABLERO_ROL_PERMISOS
            WHERE ID_ROL = ?
        """, (
            id_rol,
        ))

        # -------------------------------------------------
        # INSERTAR NUEVOS PERMISOS
        # -------------------------------------------------

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
                int(id_permiso)
            ))

        # -------------------------------------------------
        # COMMIT
        # -------------------------------------------------

        conn.commit()

        flash(
            "Permisos del rol actualizados correctamente.",
            "success"
        )

    except Exception as e:

        if conn:
            conn.rollback()

        print(
            f"[ERROR] Guardar permisos rol: {str(e)}"
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
        url_for("roles.index")
    )