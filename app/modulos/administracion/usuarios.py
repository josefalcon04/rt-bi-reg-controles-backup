from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from werkzeug.security import generate_password_hash

from app.servicios.bases.netezza import conectar_netezza


# =========================================================
# BLUEPRINT
# =========================================================

usuarios_bp = Blueprint(
    "usuarios",
    __name__,
    url_prefix="/administracion/usuarios"
)


# =========================================================
# LISTADO DE USUARIOS
# =========================================================

@usuarios_bp.route("/")
def index():

    conn = None
    cursor = None

    try:

        conn = conectar_netezza()
        cursor = conn.cursor()

        # -------------------------------------------------
        # USUARIOS
        # -------------------------------------------------

        cursor.execute("""
            SELECT
                U.ID_USUARIO,
                U.USUARIO,
                U.NOMBRE_COMPLETO,
                U.EMAIL,
                U.ID_ROL,
                R.NOMBRE_ROL,
                U.ESTADO,
                U.FECHA_CREACION,
                U.ULTIMO_LOGIN
            FROM CONTROL_MAKO..TABLERO_USUARIOS U
            INNER JOIN CONTROL_MAKO..TABLERO_ROLES R
                ON U.ID_ROL = R.ID_ROL
            ORDER BY U.ID_USUARIO
        """)

        usuarios = cursor.fetchall()

        # -------------------------------------------------
        # ROLES ACTIVOS
        # -------------------------------------------------

        cursor.execute("""
            SELECT
                ID_ROL,
                NOMBRE_ROL
            FROM CONTROL_MAKO..TABLERO_ROLES
            WHERE ESTADO = 'A'
            ORDER BY NOMBRE_ROL
        """)

        roles = cursor.fetchall()

        return render_template(
            "administracion/usuarios.html",
            usuarios=usuarios,
            roles=roles
        )

    except Exception as e:

        print(
            f"[ERROR] Usuarios: {str(e)}"
        )

        flash(
            f"Error al consultar usuarios: {str(e)}",
            "error"
        )

        return render_template(
            "administracion/usuarios.html",
            usuarios=[],
            roles=[]
        )

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# CREAR USUARIO
# =========================================================

@usuarios_bp.route("/crear", methods=["POST"])
def crear():

    conn = None
    cursor = None

    try:

        usuario = request.form.get(
            "usuario",
            ""
        ).strip()

        nombre = request.form.get(
            "nombre_completo",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        id_rol = request.form.get(
            "id_rol",
            ""
        )

        # -------------------------------------------------
        # VALIDACIONES
        # -------------------------------------------------

        if not usuario:

            flash(
                "El usuario es obligatorio.",
                "error"
            )

            return redirect(
                url_for("usuarios.index")
            )

        if not password:

            flash(
                "La contraseña es obligatoria.",
                "error"
            )

            return redirect(
                url_for("usuarios.index")
            )

        if not id_rol:

            flash(
                "Debe seleccionar un rol.",
                "error"
            )

            return redirect(
                url_for("usuarios.index")
            )

        # -------------------------------------------------
        # CONEXIÓN
        # -------------------------------------------------

        conn = conectar_netezza()
        cursor = conn.cursor()

        # -------------------------------------------------
        # VALIDAR USUARIO EXISTENTE
        # -------------------------------------------------

        cursor.execute("""
            SELECT COUNT(*)
            FROM CONTROL_MAKO..TABLERO_USUARIOS
            WHERE UPPER(USUARIO) = UPPER(?)
        """, (usuario,))

        existe = cursor.fetchone()[0]

        if existe > 0:

            flash(
                "El usuario ya existe.",
                "error"
            )

            return redirect(
                url_for("usuarios.index")
            )

        # -------------------------------------------------
        # OBTENER NUEVO ID
        # -------------------------------------------------

        cursor.execute("""
            SELECT
                COALESCE(
                    MAX(ID_USUARIO),
                    0
                ) + 1
            FROM CONTROL_MAKO..TABLERO_USUARIOS
        """)

        id_usuario = cursor.fetchone()[0]

        # -------------------------------------------------
        # HASH DE PASSWORD
        # -------------------------------------------------

        password_hash = generate_password_hash(
            password
        )

        # -------------------------------------------------
        # INSERTAR USUARIO
        # -------------------------------------------------

        cursor.execute("""
            INSERT INTO CONTROL_MAKO..TABLERO_USUARIOS
            (
                ID_USUARIO,
                USUARIO,
                NOMBRE_COMPLETO,
                EMAIL,
                PASSWORD_HASH,
                ID_ROL,
                ESTADO
            )
            VALUES
            (
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                'A'
            )
        """, (
            id_usuario,
            usuario,
            nombre,
            email,
            password_hash,
            int(id_rol)
        ))

        conn.commit()

        flash(
            "Usuario creado correctamente.",
            "success"
        )

    except Exception as e:

        if conn:
            conn.rollback()

        print(
            f"[ERROR] Crear usuario: {str(e)}"
        )

        flash(
            f"Error al crear usuario: {str(e)}",
            "error"
        )

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()

    return redirect(
        url_for("usuarios.index")
    )


# =========================================================
# EDITAR USUARIO
# =========================================================

@usuarios_bp.route(
    "/editar/<int:id_usuario>",
    methods=["POST"]
)
def editar(id_usuario):

    conn = None
    cursor = None

    try:

        nombre = request.form.get(
            "nombre_completo",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        id_rol = request.form.get(
            "id_rol",
            ""
        )

        password = request.form.get(
            "password",
            ""
        )

        # -------------------------------------------------
        # VALIDACIONES
        # -------------------------------------------------

        if not id_rol:

            flash(
                "Debe seleccionar un rol.",
                "error"
            )

            return redirect(
                url_for("usuarios.index")
            )

        # -------------------------------------------------
        # CONEXIÓN
        # -------------------------------------------------

        conn = conectar_netezza()
        cursor = conn.cursor()

        # -------------------------------------------------
        # ACTUALIZAR DATOS
        # -------------------------------------------------

        cursor.execute("""
            UPDATE CONTROL_MAKO..TABLERO_USUARIOS
            SET
                NOMBRE_COMPLETO = ?,
                EMAIL = ?,
                ID_ROL = ?
            WHERE ID_USUARIO = ?
        """, (
            nombre,
            email,
            int(id_rol),
            id_usuario
        ))

        # -------------------------------------------------
        # CAMBIAR PASSWORD
        # -------------------------------------------------

        if password:

            password_hash = generate_password_hash(
                password
            )

            cursor.execute("""
                UPDATE CONTROL_MAKO..TABLERO_USUARIOS
                SET PASSWORD_HASH = ?
                WHERE ID_USUARIO = ?
            """, (
                password_hash,
                id_usuario
            ))

        # -------------------------------------------------
        # COMMIT
        # -------------------------------------------------

        conn.commit()

        flash(
            "Usuario actualizado correctamente.",
            "success"
        )

    except Exception as e:

        if conn:
            conn.rollback()

        print(
            f"[ERROR] Editar usuario: {str(e)}"
        )

        flash(
            f"Error al actualizar usuario: {str(e)}",
            "error"
        )

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()

    return redirect(
        url_for("usuarios.index")
    )


# =========================================================
# ACTIVAR / DESACTIVAR
# =========================================================

@usuarios_bp.route(
    "/estado/<int:id_usuario>",
    methods=["POST"]
)
def cambiar_estado(id_usuario):

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
            FROM CONTROL_MAKO..TABLERO_USUARIOS
            WHERE ID_USUARIO = ?
        """, (id_usuario,))

        resultado = cursor.fetchone()

        if not resultado:

            flash(
                "Usuario no encontrado.",
                "error"
            )

            return redirect(
                url_for("usuarios.index")
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
        # ACTUALIZAR ESTADO
        # -------------------------------------------------

        cursor.execute("""
            UPDATE CONTROL_MAKO..TABLERO_USUARIOS
            SET ESTADO = ?
            WHERE ID_USUARIO = ?
        """, (
            nuevo_estado,
            id_usuario
        ))

        conn.commit()

        flash(
            "Estado del usuario actualizado.",
            "success"
        )

    except Exception as e:

        if conn:
            conn.rollback()

        print(
            f"[ERROR] Cambiar estado: {str(e)}"
        )

        flash(
            f"Error al cambiar estado: {str(e)}",
            "error"
        )

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()

    return redirect(
        url_for("usuarios.index")
    )