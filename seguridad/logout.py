from flask import Blueprint
from flask import redirect
from flask import url_for

from seguridad.session import cerrar_sesion

logout_bp = Blueprint(
    "logout",
    __name__,
    url_prefix="/logout"
)


@logout_bp.route("/")
def logout():

    cerrar_sesion()

    return redirect(url_for("login.login"))