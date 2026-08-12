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

permisos_bp = Blueprint(
    "permisos",
    __name__,
    url_prefix="/administracion/permisos"
)


# =========================================================
# LISTADO DE PERMISOS
# =========================================================

@permisos_bp.route("/")
def index():

    conn = None
    cursor = None

    try:

        conn = conectar_netezza()
        cursor = conn.cursor()

        # -------------------------------------------------
        # CONSULTAR PERMISOS
        # -------------------------------------------------

        cursor.execute("""
            SELECT
                ID_PERMISO,
                CODIGO,
                DESCRIPCION,
                ESTADO
            FROM CONTROL_MAKO..TABLERO_PERMISOS
            ORDER BY ID_PERMISO
        """)

        permisos = cursor.fetchall()

        return render_template(
            "administracion/permisos.html",
            permisos=permisos
        )

    except Exception as e:

        print(
            f"[ERROR] Permisos: {str(e)}"
        )

        flash(
            f"Error al consultar permisos: {str(e)}",
            "error"
        )

        return render_template(
            "administracion/permisos.html",
            permisos=[]
        )

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# CREAR PERMISO
# =========================================================

@permisos_bp.route(
    "/crear",
    methods=["POST"]
)
def crear():

    conn = None
    cursor = None

    try:

        codigo = request.form.get(
            "codigo",
            ""
        ).strip().upper()

        descripcion = request.form.get(
            "descripcion",
            ""
        ).strip()

        # -------------------------------------------------
        # VALIDACIONES
        # -------------------------------------------------

        if not codigo:

            flash(
                "El código del permiso es obligatorio.",
                "error"
            )

            return redirect(
                url_for("permisos.index")
            )

        # -------------------------------------------------
        # CONEXIÓN
        # -------------------------------------------------

        conn = conectar_netezza()
        cursor = conn.cursor()

        # -------------------------------------------------
        # VALIDAR CÓDIGO EXISTENTE
        # -------------------------------------------------

        cursor.execute("""
            SELECT COUNT(*)
            FROM CONTROL_MAKO..TABLERO_PERMISOS
            WHERE UPPER(CODIGO) = UPPER(?)
        """, (
            codigo,
        ))

        existe = cursor.fetchone()[0]

        if existe > 0:

            flash(
                "El código del permiso ya existe.",
                "error"
            )

            return redirect(
                url_for("permisos.index")
            )

        # -------------------------------------------------
        # OBTENER NUEVO ID
        # -------------------------------------------------

        cursor.execute("""
            SELECT
                COALESCE(
                    MAX(ID_PERMISO),
                    0
                ) + 1
            FROM CONTROL_MAKO..TABLERO_PERMISOS
        """)

        id_permiso = cursor.fetchone()[0]

        # -------------------------------------------------
        # INSERTAR PERMISO
        # -------------------------------------------------

        cursor.execute("""
            INSERT INTO CONTROL_MAKO..TABLERO_PERMISOS
            (
                ID_PERMISO,
                CODIGO,
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
            id_permiso,
            codigo,
            descripcion
        ))

        conn.commit()

        flash(
            "Permiso creado correctamente.",
            "success"
        )

    except Exception as e:

        if conn:
            conn.rollback()

        print(
            f"[ERROR] Crear permiso: {str(e)}"
        )

        flash(
            f"Error al crear permiso: {str(e)}",
            "error"
        )

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()

    return redirect(
        url_for("permisos.index")
    )


# =========================================================
# EDITAR PERMISO
# =========================================================

@permisos_bp.route(
    "/editar/<int:id_permiso>",
    methods=["POST"]
)
def editar(id_permiso):

    conn = None
    cursor = None

    try:

        codigo = request.form.get(
            "codigo",
            ""
        ).strip().upper()

        descripcion = request.form.get(
            "descripcion",
            ""
        ).strip()

        # -------------------------------------------------
        # VALIDACIONES
        # -------------------------------------------------

        if not codigo:

            flash(
                "El código del permiso es obligatorio.",
                "error"
            )

            return redirect(
                url_for("permisos.index")
            )

        # -------------------------------------------------
        # CONEXIÓN
        # -------------------------------------------------

        conn = conectar_netezza()
        cursor = conn.cursor()

        # -------------------------------------------------
        # VALIDAR DUPLICADO
        # -------------------------------------------------

        cursor.execute("""
            SELECT COUNT(*)
            FROM CONTROL_MAKO..TABLERO_PERMISOS
            WHERE UPPER(CODIGO) = UPPER(?)
              AND ID_PERMISO <> ?
        """, (
            codigo,
            id_permiso
        ))

        existe = cursor.fetchone()[0]

        if existe > 0:

            flash(
                "Ya existe otro permiso con ese código.",
                "error"
            )

            return redirect(
                url_for("permisos.index")
            )

        # -------------------------------------------------
        # ACTUALIZAR
        # -------------------------------------------------

        cursor.execute("""
            UPDATE CONTROL_MAKO..TABLERO_PERMISOS
            SET
                CODIGO = ?,
                DESCRIPCION = ?
            WHERE ID_PERMISO = ?
        """, (
            codigo,
            descripcion,
            id_permiso
        ))

        conn.commit()

        flash(
            "Permiso actualizado correctamente.",
            "success"
        )

    except Exception as e:

        if conn:
            conn.rollback()

        print(
            f"[ERROR] Editar permiso: {str(e)}"
        )

        flash(
            f"Error al actualizar permiso: {str(e)}",
            "error"
        )

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()

    return redirect(
        url_for("permisos.index")
    )


# =========================================================
# ACTIVAR / DESACTIVAR PERMISO
# =========================================================

@permisos_bp.route(
    "/estado/<int:id_permiso>",
    methods=["POST"]
)
def cambiar_estado(id_permiso):

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
            FROM CONTROL_MAKO..TABLERO_PERMISOS
            WHERE ID_PERMISO = ?
        """, (
            id_permiso,
        ))

        resultado = cursor.fetchone()

        if not resultado:

            flash(
                "Permiso no encontrado.",
                "error"
            )

            return redirect(
                url_for("permisos.index")
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
            UPDATE CONTROL_MAKO..TABLERO_PERMISOS
            SET
                ESTADO = ?
            WHERE ID_PERMISO = ?
        """, (
            nuevo_estado,
            id_permiso
        ))

        conn.commit()

        flash(
            "Estado del permiso actualizado correctamente.",
            "success"
        )

    except Exception as e:

        if conn:
            conn.rollback()

        print(
            f"[ERROR] Cambiar estado permiso: {str(e)}"
        )

        flash(
            f"Error al cambiar estado del permiso: {str(e)}",
            "error"
        )

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()

    return redirect(
        url_for("permisos.index")
    )