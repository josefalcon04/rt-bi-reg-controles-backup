from app.servicios.netezza_service import ejecutar_query


def buscar_consulta_tendencia(pregunta):

    sql = f"""
    SELECT *
    FROM CONTROL_MAKO..TABLERO_IA_CATALOGO_CONSULTAS
    WHERE ACTIVO='S'
    """

    catalogo = ejecutar_query(sql)

    pregunta = pregunta.lower()

    for fila in catalogo:

        palabras = (
            fila["PALABRAS_CLAVE"] or ""
        ).lower()

        lista_palabras = palabras.split(",")

        for palabra in lista_palabras:

            if palabra.strip() in pregunta:

                return fila

    return None