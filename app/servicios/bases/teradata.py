import teradatasql

def conectar_teradata():
    try:
        conn = teradatasql.connect(
            host="vantage.gp.inet",
            user="jfalconf",
            password="Chiki161827A06.",
            logmech="LDAP"
        )

        print("Conexión exitosa a Teradata")
        return conn

    except Exception as e:
        print(f"Error en la conexión Teradata: {e}")
        return None