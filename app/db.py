import nzpy

# Conexión a la base de datos
def conectar_netezza():
    try:
        conn = nzpy.connect(
            host="10.4.35.1", 
            database="SB_BI",
            port=5480, 
            user="jfalconf", 
            password="jfalconf23!"
        )
        print("Conexión exitosa a Netezza")
        return conn
    except Exception as e:
        print(f"Error en la conexión: {e}")
        return None
