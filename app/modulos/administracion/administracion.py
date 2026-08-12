from flask import Blueprint, render_template


administracion_bp = Blueprint(
    "administracion",
    __name__,
    url_prefix="/administracion"
)


@administracion_bp.route("/")
def index():

    return render_template(
        "administracion.html"
    )