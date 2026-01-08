from flask import Flask, render_template  # Asegúrate de importar render_template
from app.calendario import calendario_bp  # Importa el blueprint de calendario
from app.monitoreo import monitoreo_norma_bp  # Importa el blueprint de monitoreo
from app.monitoreo import monitoreo_input_bp  # Importa el blueprint de monitoreo
from app.planta import planta_bp  # Importa el blueprint de planta de control
from app.caracteres import caracteres_bp  # Importa el blueprint de caracteres
#from app.chatbox import chatbox_bp  # Importa el blueprint de chatbox
from app.planta import planta_mtc_bp  # Importa el blueprint de planta de control
from app.planta import NRIPO_033_034_bp  # Importa el blueprint de reporte 33 y 34
from app.notificaciones.notificaciones import notificaciones_bp  # importa tu blueprint
from app.planta import NRIPO_035_bp  # Importa el blueprint de reporte 35
from app.planta import planta_tisa_bp  # Importa el blueprint de planta TISA
from app.planta import planta_usua_mtc_bp  # Importa el blueprint de planta USUA MTC
from app.planta import planta_trfacu_bp # Importa el blueprint de planta USUA MTC
from documentacion import documentacion_bp

app = Flask(__name__)

# Registra los blueprints
app.register_blueprint(calendario_bp)
app.register_blueprint(monitoreo_norma_bp)
app.register_blueprint(monitoreo_input_bp)
app.register_blueprint(planta_bp)
app.register_blueprint(caracteres_bp)
#app.register_blueprint(chatbox_bp)
app.register_blueprint(planta_mtc_bp)
app.register_blueprint(NRIPO_033_034_bp)
app.register_blueprint(notificaciones_bp)
app.register_blueprint(NRIPO_035_bp)
app.register_blueprint(planta_tisa_bp)
app.register_blueprint(planta_usua_mtc_bp)
app.register_blueprint(planta_trfacu_bp)
app.register_blueprint(documentacion_bp)

@app.route('/')
def menu():
    # Usar render_template correctamente
    return render_template('menu.html')  # Renderiza la página 'menu.html'

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0',port=8080)
