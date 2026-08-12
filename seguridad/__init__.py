from flask import Blueprint


seguridad_bp = Blueprint(
    "seguridad",
    __name__,
    url_prefix="/seguridad"
)


from . import login