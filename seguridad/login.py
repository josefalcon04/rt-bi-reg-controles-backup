from flask import Blueprint
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for

import re

from seguridad.usuarios import autenticar
from seguridad.session import iniciar_sesion
from seguridad.menu_service import (
    obtener_menus_usuario,
    obtener_permisos_usuario
)



login_bp = Blueprint(
    "login",
    __name__,
    url_prefix="/login"
)


@login_bp.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        usuario = request.form["usuario"].strip()
        password = request.form["password"]

        # ===============================
        # Validación del usuario
        # ===============================

        if not re.fullmatch(r"[A-Za-z0-9._-]{3,50}", usuario):

            return render_template(
                "login.html",
                error="Usuario o contraseña incorrectos."
            )

        # ===============================
        # Validación de longitud
        # ===============================

        if len(password) > 128:

            return render_template(
                "login.html",
                error="Usuario o contraseña incorrectos."
            )

        # ===============================
        # Autenticación
        # ===============================

        datos = autenticar(usuario, password)
        print(datos)

        if datos is None:

            return render_template(
                "login.html",
                error="Usuario o contraseña incorrectos."
            )

        iniciar_sesion(datos)

        # -----------------------------
        # Cargar menús del usuario
        # -----------------------------

        from flask import session

        session["menus"] = obtener_menus_usuario(
            datos["id_usuario"]
        )
        session["permisos"] = obtener_permisos_usuario(
            datos["id_usuario"]
        )

        return redirect(url_for("menu"))

    return render_template("login.html")