from flask import session
from datetime import datetime


def iniciar_sesion(usuario):
    """
    Crea la sesión del usuario autenticado.
    """

    session.clear()

    session.permanent = True

    session["usuario_id"] = usuario["id_usuario"]
    session["usuario"] = usuario["usuario"]
    session["nombre"] = usuario["nombre"]

    # Información adicional para futuras funcionalidades
    session["email"] = usuario.get("email", "")
    session["rol"] = usuario["id_rol"]
    session["rol_nombre"] = usuario.get("rol_nombre", "")

    # Fechas de control
    ahora = datetime.now().isoformat()

    session["login_time"] = ahora
    session["ultimo_acceso"] = ahora


def actualizar_actividad():
    """
    Actualiza la última actividad del usuario.
    """

    if "usuario_id" in session:
        session["ultimo_acceso"] = datetime.now().isoformat()


def cerrar_sesion():
    """
    Elimina completamente la sesión.
    """

    session.clear()


def usuario_logueado():
    """
    Retorna True si existe una sesión activa.
    """

    return "usuario_id" in session


def obtener_usuario():
    """
    Devuelve la información del usuario autenticado.
    """

    if "usuario_id" not in session:
        return None

    return {

        "id_usuario": session["usuario_id"],
        "usuario": session["usuario"],
        "nombre": session["nombre"],
        "email": session.get("email"),
        "rol": session["rol"],
        "rol_nombre": session.get("rol_nombre"),
        "login_time": session.get("login_time"),
        "ultimo_acceso": session.get("ultimo_acceso")

    }
