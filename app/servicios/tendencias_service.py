# app/servicios/tendencias_service.py

from app.servicios.netezza_service import ejecutar_query



def buscar_consulta_tendencia(pregunta):


    sql = """

    SELECT
        *
    FROM CONTROL_MAKO..TABLERO_IA_CATALOGO_CONSULTAS
    WHERE ACTIVO='S'

    """


    catalogo = ejecutar_query(sql)



    if not catalogo:

        return None



    pregunta = pregunta.lower()



    mejor_match = None
    mayor_score = 0



    for fila in catalogo:


        palabras = (
            fila.get(
                "PALABRAS_CLAVE",
                ""
            )
            or ""
        ).lower()



        lista = [
            x.strip()
            for x in palabras.split(",")
        ]



        score = sum(

            1
            for palabra in lista
            if palabra and palabra in pregunta

        )



        if score > mayor_score:

            mayor_score = score

            mejor_match = fila



    return mejor_match