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

menus_bp = Blueprint(
    "menus",
    __name__,
    url_prefix="/administracion/menus"
)


# =========================================================
# LISTADO DE MENÚS
# =========================================================

@menus_bp.route("/")
def index():

    conn = None
    cursor = None

    try:

        conn = conectar_netezza()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                M.ID_MENU,
                M.NOMBRE_MENU,
                M.URL,
                M.BLUEPRINT,
                M.ICONO,
                M.ORDEN_MENU,
                M.ID_MENU_PADRE,
                M.ID_PERMISO,
                M.VISIBLE,
                M.ESTADO,
                P.CODIGO
            FROM CONTROL_MAKO..TABLERO_MENUS M
            LEFT JOIN CONTROL_MAKO..TABLERO_PERMISOS P
                ON M.ID_PERMISO = P.ID_PERMISO
            ORDER BY
                M.ID_MENU_PADRE,
                M.ORDEN_MENU,
                M.ID_MENU
        """)

        menus_admin = cursor.fetchall()

        # -------------------------------------------------
        # LISTA DE MENÚS PADRE
        # -------------------------------------------------

        cursor.execute("""
            SELECT
                ID_MENU,
                NOMBRE_MENU
            FROM CONTROL_MAKO..TABLERO_MENUS
            WHERE ID_MENU_PADRE = 0
              AND ESTADO = 'A'
            ORDER BY
                ORDEN_MENU,
                ID_MENU
        """)

        menus_padre = cursor.fetchall()

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
            ORDER BY
                ID_PERMISO
        """)

        permisos = cursor.fetchall()

        return render_template(
            "administracion/menus.html",
            menus_admin=menus_admin,
            menus_padre=menus_padre,
            permisos=permisos
        )

    except Exception as e:

        print(
            f"[ERROR] Menús: {str(e)}"
        )

        flash(
            f"Error al consultar menús: {str(e)}",
            "error"
        )

        return render_template(
            "administracion/menus.html",
            menus_admin=[],
            menus_padre=[],
            permisos=[]
        )

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# CREAR MENÚ
# =========================================================

@menus_bp.route(
    "/crear",
    methods=["POST"]
)
def crear():

    conn = None
    cursor = None

    try:

        nombre_menu = request.form.get(
            "nombre_menu",
            ""
        ).strip()

        url = request.form.get(
            "url",
            ""
        ).strip()

        blueprint = request.form.get(
            "blueprint",
            ""
        ).strip()

        icono = request.form.get(
            "icono",
            ""
        ).strip()

        orden_menu = request.form.get(
            "orden_menu",
            "0"
        ).strip()

        id_menu_padre = request.form.get(
            "id_menu_padre",
            "0"
        ).strip()

        id_permiso = request.form.get(
            "id_permiso",
            ""
        ).strip()

        visible = request.form.get(
            "visible",
            "S"
        ).strip().upper()

        # -------------------------------------------------
        # VALIDACIONES
        # -------------------------------------------------

        if not nombre_menu:

            flash(
                "El nombre del menú es obligatorio.",
                "error"
            )

            return redirect(
                url_for("menus.index")
            )

        if not url:

            flash(
                "La URL del menú es obligatoria.",
                "error"
            )

            return redirect(
                url_for("menus.index")
            )

        if not id_permiso:

            flash(
                "Debes seleccionar un permiso.",
                "error"
            )

            return redirect(
                url_for("menus.index")
            )

        # -------------------------------------------------
        # CONVERSIÓN DE VALORES
        # -------------------------------------------------

        try:

            orden_menu = int(orden_menu)

        except ValueError:

            orden_menu = 0


        try:

            id_menu_padre = int(id_menu_padre)

        except ValueError:

            id_menu_padre = 0


        try:

            id_permiso = int(id_permiso)

        except ValueError:

            flash(
                "El permiso seleccionado no es válido.",
                "error"
            )

            return redirect(
                url_for("menus.index")
            )


        # -------------------------------------------------
        # VALIDAR VISIBLE
        # -------------------------------------------------

        if visible not in ("S", "N"):

            visible = "S"


        # -------------------------------------------------
        # CONEXIÓN
        # -------------------------------------------------

        conn = conectar_netezza()
        cursor = conn.cursor()


        # -------------------------------------------------
        # OBTENER NUEVO ID
        # -------------------------------------------------

        cursor.execute("""
            SELECT
                COALESCE(
                    MAX(ID_MENU),
                    0
                ) + 1
            FROM CONTROL_MAKO..TABLERO_MENUS
        """)

        id_menu = cursor.fetchone()[0]


        # -------------------------------------------------
        # INSERTAR
        # -------------------------------------------------

        cursor.execute("""
            INSERT INTO CONTROL_MAKO..TABLERO_MENUS
            (
                ID_MENU,
                NOMBRE_MENU,
                URL,
                BLUEPRINT,
                ICONO,
                ORDEN_MENU,
                ID_MENU_PADRE,
                ID_PERMISO,
                VISIBLE,
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
                ?,
                ?,
                ?,
                'A'
            )
        """, (
            id_menu,
            nombre_menu,
            url,
            blueprint,
            icono,
            orden_menu,
            id_menu_padre,
            id_permiso,
            visible
        ))

        conn.commit()

        flash(
            "Menú creado correctamente.",
            "success"
        )

    except Exception as e:

        if conn:
            conn.rollback()

        print(
            f"[ERROR] Crear menú: {str(e)}"
        )

        flash(
            f"Error al crear menú: {str(e)}",
            "error"
        )

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()

    return redirect(
        url_for("menus.index")
    )


# =========================================================
# EDITAR MENÚ
# =========================================================

@menus_bp.route(
    "/editar/<int:id_menu>",
    methods=["POST"]
)
def editar(id_menu):

    conn = None
    cursor = None

    try:

        nombre_menu = request.form.get(
            "nombre_menu",
            ""
        ).strip()

        url = request.form.get(
            "url",
            ""
        ).strip()

        blueprint = request.form.get(
            "blueprint",
            ""
        ).strip()

        icono = request.form.get(
            "icono",
            ""
        ).strip()

        orden_menu = request.form.get(
            "orden_menu",
            "0"
        ).strip()

        id_menu_padre = request.form.get(
            "id_menu_padre",
            "0"
        ).strip()

        id_permiso = request.form.get(
            "id_permiso",
            ""
        ).strip()

        visible = request.form.get(
            "visible",
            "S"
        ).strip().upper()


        # -------------------------------------------------
        # VALIDACIONES
        # -------------------------------------------------

        if not nombre_menu:

            flash(
                "El nombre del menú es obligatorio.",
                "error"
            )

            return redirect(
                url_for("menus.index")
            )


        if not url:

            flash(
                "La URL del menú es obligatoria.",
                "error"
            )

            return redirect(
                url_for("menus.index")
            )


        if not id_permiso:

            flash(
                "Debes seleccionar un permiso.",
                "error"
            )

            return redirect(
                url_for("menus.index")
            )


        # -------------------------------------------------
        # CONVERSIONES
        # -------------------------------------------------

        try:

            orden_menu = int(orden_menu)

        except ValueError:

            orden_menu = 0


        try:

            id_menu_padre = int(id_menu_padre)

        except ValueError:

            id_menu_padre = 0


        try:

            id_permiso = int(id_permiso)

        except ValueError:

            flash(
                "El permiso seleccionado no es válido.",
                "error"
            )

            return redirect(
                url_for("menus.index")
            )


        if visible not in ("S", "N"):

            visible = "S"


        # -------------------------------------------------
        # CONEXIÓN
        # -------------------------------------------------

        conn = conectar_netezza()
        cursor = conn.cursor()


        # -------------------------------------------------
        # EVITAR QUE UN MENÚ SEA SU PROPIO PADRE
        # -------------------------------------------------

        if id_menu_padre == id_menu:

            flash(
                "Un menú no puede ser su propio padre.",
                "error"
            )

            return redirect(
                url_for("menus.index")
            )


        # -------------------------------------------------
        # ACTUALIZAR
        # -------------------------------------------------

        cursor.execute("""
            UPDATE CONTROL_MAKO..TABLERO_MENUS
            SET
                NOMBRE_MENU = ?,
                URL = ?,
                BLUEPRINT = ?,
                ICONO = ?,
                ORDEN_MENU = ?,
                ID_MENU_PADRE = ?,
                ID_PERMISO = ?,
                VISIBLE = ?
            WHERE ID_MENU = ?
        """, (
            nombre_menu,
            url,
            blueprint,
            icono,
            orden_menu,
            id_menu_padre,
            id_permiso,
            visible,
            id_menu
        ))

        conn.commit()

        flash(
            "Menú actualizado correctamente.",
            "success"
        )

    except Exception as e:

        if conn:
            conn.rollback()

        print(
            f"[ERROR] Editar menú: {str(e)}"
        )

        flash(
            f"Error al actualizar menú: {str(e)}",
            "error"
        )

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()

    return redirect(
        url_for("menus.index")
    )


# =========================================================
# ACTIVAR / DESACTIVAR MENÚ
# =========================================================

@menus_bp.route(
    "/estado/<int:id_menu>",
    methods=["POST"]
)
def cambiar_estado(id_menu):

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
            FROM CONTROL_MAKO..TABLERO_MENUS
            WHERE ID_MENU = ?
        """, (
            id_menu,
        ))

        resultado = cursor.fetchone()


        if not resultado:

            flash(
                "Menú no encontrado.",
                "error"
            )

            return redirect(
                url_for("menus.index")
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
            UPDATE CONTROL_MAKO..TABLERO_MENUS
            SET
                ESTADO = ?
            WHERE ID_MENU = ?
        """, (
            nuevo_estado,
            id_menu
        ))

        conn.commit()

        flash(
            "Estado del menú actualizado correctamente.",
            "success"
        )

    except Exception as e:

        if conn:
            conn.rollback()

        print(
            f"[ERROR] Cambiar estado menú: {str(e)}"
        )

        flash(
            f"Error al cambiar estado del menú: {str(e)}",
            "error"
        )

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()

    return redirect(
        url_for("menus.index")
    )


# =========================================================
# MOSTRAR / OCULTAR MENÚ
# =========================================================

@menus_bp.route(
    "/visible/<int:id_menu>",
    methods=["POST"]
)
def cambiar_visible(id_menu):

    conn = None
    cursor = None

    try:

        conn = conectar_netezza()
        cursor = conn.cursor()


        # -------------------------------------------------
        # OBTENER VISIBILIDAD ACTUAL
        # -------------------------------------------------

        cursor.execute("""
            SELECT
                VISIBLE
            FROM CONTROL_MAKO..TABLERO_MENUS
            WHERE ID_MENU = ?
        """, (
            id_menu,
        ))

        resultado = cursor.fetchone()


        if not resultado:

            flash(
                "Menú no encontrado.",
                "error"
            )

            return redirect(
                url_for("menus.index")
            )


        visible_actual = resultado[0]


        # -------------------------------------------------
        # NUEVO VALOR
        # -------------------------------------------------

        nueva_visibilidad = (
            "N"
            if visible_actual == "S"
            else "S"
        )


        # -------------------------------------------------
        # ACTUALIZAR
        # -------------------------------------------------

        cursor.execute("""
            UPDATE CONTROL_MAKO..TABLERO_MENUS
            SET
                VISIBLE = ?
            WHERE ID_MENU = ?
        """, (
            nueva_visibilidad,
            id_menu
        ))

        conn.commit()

        flash(
            "Visibilidad del menú actualizada correctamente.",
            "success"
        )

    except Exception as e:

        if conn:
            conn.rollback()

        print(
            f"[ERROR] Cambiar visibilidad menú: {str(e)}"
        )

        flash(
            f"Error al cambiar visibilidad: {str(e)}",
            "error"
        )

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()

    return redirect(
        url_for("menus.index")
    )