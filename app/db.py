import nzpy
import teradatasql

# Conexión a la base de datos
def conectar_netezza():
    try:
        conn = nzpy.connect(
            host="10.4.35.1", 
            database="SB_BI",
            port=5480, 
            user="APP_MONITOR_BI", 
            password="P3ru2026%!"
        )
        print("Conexión exitosa a Netezza")
        return conn
    except Exception as e:
        print(f"Error en la conexión: {e}")
        return None

def conectar_teradata():
    try:
        conn = teradatasql.connect(
            host="vantage.gp.inet",
            user="jfalconf",
            password="Chiki161827A05.",
            logmech="LDAP"
        )

        print("Conexión exitosa a Teradata")
        return conn

    except Exception as e:
        print(f"Error en la conexión Teradata: {e}")
        return None