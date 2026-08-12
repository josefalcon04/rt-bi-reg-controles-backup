from app.modulos.calendario import calendario_bp  # Importa el blueprint de calendario
from app.modulos.monitoreo import monitoreo_norma_bp  # Importa el blueprint de monitoreo
from app.modulos.monitoreo import monitoreo_input_bp  # Importa el blueprint de monitoreo
from app.modulos.planta import planta_control_bp  # Importa el blueprint de planta de control
from app.modulos.caracteres import caracteres_bp  # Importa el blueprint de caracteres
from app.modulos.chatbox import chatbox_bp  # Importa el blueprint de chatbox
from app.modulos.planta import planta_mtc_bp  # Importa el blueprint de planta de control
from app.modulos.planta import NRIPO_033_034_bp  # Importa el blueprint de reporte 33 y 34
from app.modulos.notificaciones import notificaciones_bp  # importa tu blueprint
from app.modulos.planta import NRIPO_035_bp  # Importa el blueprint de reporte 35
from app.modulos.planta import planta_tisa_bp  # Importa el blueprint pip install plotlyde planta TISA
from app.modulos.planta import planta_usua_mtc_bp  # Importa el blueprint de planta USUA MTC
from app.modulos.planta import planta_trfacu_bp # Importa el blueprint de planta USUA MTC
from app.documentacion import documentacion_bp # Importa el blueprint de documentacion
from app.modulos.devoluciones import devoluciones_bp # Importa el blueprint de planta USUA MTC
from app.modulos.pases.pases import pases_bp  # Importa el blueprint de pases
from app.modulos.monitoreo_teradata import monitoreo_tera_bp  # Importa el blueprint de monitoreo Teradata
from app.modulos.monitor_agentes.monitor import monitor_agentes_bp
from app.modulos.favoritos import favoritos_bp
from app.modulos.tendencias.tendencias import tendencias_bp
from app.modulos.administracion.administracion import administracion_bp
from app.modulos.administracion.usuarios import usuarios_bp
from app.modulos.administracion.roles import roles_bp
from app.modulos.administracion.permisos import permisos_bp
from app.modulos.administracion.menus import menus_bp
from app.modulos.administracion.roles_permisos import roles_permisos_bp
from app.modulos.administracion.accesos_usuario import accesos_usuario_bp

# Registra los blueprints
def register_blueprints(app):
    app.register_blueprint(calendario_bp)
    app.register_blueprint(monitoreo_norma_bp)
    app.register_blueprint(monitoreo_input_bp)
    app.register_blueprint(planta_control_bp)
    app.register_blueprint(caracteres_bp)
    app.register_blueprint(chatbox_bp)
    app.register_blueprint(planta_mtc_bp)
    app.register_blueprint(NRIPO_033_034_bp)
    app.register_blueprint(notificaciones_bp)
    app.register_blueprint(NRIPO_035_bp)
    app.register_blueprint(planta_tisa_bp)
    app.register_blueprint(planta_usua_mtc_bp)
    app.register_blueprint(planta_trfacu_bp)
    app.register_blueprint(documentacion_bp)
    app.register_blueprint(devoluciones_bp)
    app.register_blueprint(pases_bp)  # Registra el blueprint de pases
    app.register_blueprint(monitoreo_tera_bp)  # Registra el blueprint de monitoreo Teradata
    app.register_blueprint(monitor_agentes_bp) 
    app.register_blueprint(favoritos_bp) 
    app.register_blueprint(tendencias_bp)
    app.register_blueprint(administracion_bp)
    app.register_blueprint(usuarios_bp)
    app.register_blueprint(roles_bp)
    app.register_blueprint(permisos_bp)
    app.register_blueprint(menus_bp)
    app.register_blueprint(roles_permisos_bp)
    app.register_blueprint(accesos_usuario_bp)
