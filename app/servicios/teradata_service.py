# app/servicios/teradata_service.py
import pandas as pd
from app.servicios.bases.db import conectar_teradata # Reutilizamos tu conexión centralizada

def ejecutar_query_teradata(query):
    try:
        conn = conectar_teradata() # Llamada a tu función existente
        df = pd.read_sql(query, conn)
        conn.close()
        return df.to_dict(orient='records')
    except Exception as e:
        print(f"[ERROR TERADATA] {str(e)}")
        return []