# app/servicios/teradata_service.py

import pandas as pd
from app.servicios.bases.connection_manager import conectar_teradata



def ejecutar_query_teradata(query):

    conn = None

    try:

        conn = conectar_teradata()


        df = pd.read_sql(
            query,
            conn
        )


        return df.to_dict(
            orient="records"
        )


    except Exception as e:


        raise Exception(
            f"Error ejecutando query Teradata: {str(e)}"
        )


    finally:


        if conn:

            conn.close()