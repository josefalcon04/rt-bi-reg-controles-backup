from flask import Flask, render_template
from app.core.blueprint_registry import register_blueprints


def create_app():

    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static"
    )

    app.secret_key = "clave_segura_bi_assistant"

    register_blueprints(app)


    @app.route('/')
    def menu():
        return render_template('menu.html')


    @app.route('/tendencias_plantas')
    def tendencias_plantas():
        return render_template('tendencias_plantas.html')


    @app.route('/tendencias_reportes')
    def tendencias_reportes():
        return render_template('tendencias_reportes.html')


    return app