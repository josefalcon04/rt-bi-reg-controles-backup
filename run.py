from flask import Flask, render_template  # Asegúrate de importar render_template
from app.calendario import calendario_bp  # Importa el blueprint de calendario
from app.monitoreo import monitoreo_norma_bp  # Importa el blueprint de monitoreo
from app.monitoreo import monitoreo_input_bp  # Importa el blueprint de monitoreo
from app.planta import planta_bp  # Importa el blueprint de planta de control

app = Flask(__name__)

# Registra los blueprints
app.register_blueprint(calendario_bp)
app.register_blueprint(monitoreo_norma_bp)
app.register_blueprint(monitoreo_input_bp)
app.register_blueprint(planta_bp)

@app.route('/')
def menu():
    # Usar render_template correctamente
    return render_template('menu.html')  # Renderiza la página 'menu.html'

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0',port=8082)
