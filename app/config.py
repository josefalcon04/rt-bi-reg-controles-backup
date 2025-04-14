# config.py

class Config:
    SECRET_KEY = 'mi_clave_secreta'  # Cambia esto por una clave secreta real
    SQLALCHEMY_DATABASE_URI = 'sqlite:///mi_base_de_datos.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
