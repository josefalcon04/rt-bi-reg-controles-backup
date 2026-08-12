from flask import Blueprint
from flask import request
from flask import jsonify
from flask import session

from seguridad.favoritos_service import toggle_favorito


favoritos_bp = Blueprint(
    "favoritos",
    __name__
)


@favoritos_bp.route(
    "/favoritos/toggle",
    methods=["POST"]
)
def favorito_toggle():

    datos = request.get_json()

    id_menu = int(datos["id_menu"])

    id_usuario = session["usuario_id"]

    favorito = toggle_favorito(
        id_usuario,
        id_menu
    )

    return jsonify({

        "ok": True,

        "favorito": favorito

    })