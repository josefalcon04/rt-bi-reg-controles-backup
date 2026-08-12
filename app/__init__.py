from flask import Flask, render_template, redirect, url_for, session, request
from datetime import datetime, timedelta

from app.core.blueprint_registry import register_blueprints

from seguridad.login import login_bp
from seguridad.logout import logout_bp
from seguridad.cambiar_password import cambiar_password_bp
from seguridad.menu_service import obtener_menus_usuario


def create_app():

    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static"
    )

    app.secret_key = "clave_segura_bi_assistant"

    # Tiempo máximo de sesión
    app.permanent_session_lifetime = timedelta(minutes=20)

    # ==========================================
    # Blueprints de seguridad
    # ==========================================

    app.register_blueprint(login_bp)
    app.register_blueprint(logout_bp)
    app.register_blueprint(cambiar_password_bp)

    # ==========================================
    # Blueprints de la aplicación
    # ==========================================

    register_blueprints(app)

    # ==========================================
    # Menú disponible para TODAS las plantillas
    # ==========================================

    @app.context_processor
    def cargar_menu():

        if "usuario_id" not in session:

            return dict(menus=[])

        menus, favoritos = obtener_menus_usuario(
            session["usuario_id"]
        )

        return dict(

            menus=menus,

            favoritos=favoritos

)

    # ==========================================
    # Validación de sesión
    # ==========================================

    @app.before_request
    def validar_sesion():

        rutas_publicas = [
            "login.login",
            "logout.logout",
            "static"
        ]

        if request.endpoint in rutas_publicas:
            return

        if "usuario_id" not in session:
            return redirect(url_for("login.login"))

        ahora = datetime.now()

        ultimo = session.get("ultimo_acceso")

        if ultimo:

            try:

                ultimo = datetime.fromisoformat(ultimo)

                if (ahora - ultimo) > timedelta(minutes=20):

                    session.clear()

                    return redirect(
                        url_for(
                            "login.login",
                            mensaje="Su sesión expiró por inactividad."
                        )
                    )

            except Exception:

                session.clear()

                return redirect(
                    url_for("login.login")
                )

        session["ultimo_acceso"] = ahora.isoformat()
        session.permanent = True
        session.modified = True

    # ==========================================
    # Menú principal
    # ==========================================

    @app.route("/")
    def menu():

        return render_template("inicio.html")

    # ==========================================
    # Tendencias
    # ==========================================

    @app.route("/tendencias_plantas")
    def tendencias_plantas():

        return render_template("tendencias_plantas.html")

    @app.route("/tendencias_reportes")
    def tendencias_reportes():

        return render_template("tendencias_reportes.html")

    return app

    
