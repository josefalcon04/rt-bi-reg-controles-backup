from flask import Blueprint
from flask import request
from flask import jsonify
from flask import session

from seguridad.usuarios import obtener_usuario
from seguridad.usuarios import actualizar_password

from seguridad.password import verificar_password
from seguridad.password import generar_hash


cambiar_password_bp = Blueprint(
    "cambiar_password",
    __name__
)


@cambiar_password_bp.route(
    "/cambiar-password",
    methods=["POST"]
)
def cambiar_password():

    if "usuario_id" not in session:

        return jsonify({
            "ok": False,
            "mensaje": "Sesión expirada."
        })


    password_actual = request.form["password_actual"]

    password_nueva = request.form["password_nueva"]

    password_confirmar = request.form["password_confirmar"]


    usuario = obtener_usuario(session["usuario"])


    if usuario is None:

        return jsonify({
            "ok": False,
            "mensaje": "Usuario no encontrado."
        })


    if not verificar_password(
        password_actual,
        usuario["password_hash"]
    ):

        return jsonify({
            "ok": False,
            "mensaje": "La contraseña actual es incorrecta."
        })


    if password_nueva != password_confirmar:

        return jsonify({
            "ok": False,
            "mensaje": "Las contraseñas no coinciden."
        })


    nuevo_hash = generar_hash(password_nueva)


    actualizar_password(
        usuario["id_usuario"],
        nuevo_hash
    )


    return jsonify({
        "ok": True,
        "mensaje": "Contraseña actualizada correctamente."
    })