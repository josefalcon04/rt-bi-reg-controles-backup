# app/servicios/teradata_service.py

import re
import pandas as pd

from app.servicios.bases.connection_manager import conectar_teradata


# ============================================================
# CONFIGURACIÓN METADATA TERADATA
# ============================================================

METADATA_TERADATA = {
    "tablas": "D_EWAYA_CONFIG.VW_MetadatosTecnicoscab",
    "campos": "D_EWAYA_CONFIG.VW_MetadatosTecnicosdet"
}


# ============================================================
# UTILIDADES GENERALES
# ============================================================

def _normalizar_columnas(df):
    """
    Normaliza nombres de columnas devueltos por Teradata.
    """
    if df is not None and not df.empty:
        df.columns = [
            str(col).strip().upper()
            for col in df.columns
        ]

    return df


def _normalizar_texto(texto):
    """
    Normaliza texto para búsquedas.
    """

    if texto is None:
        return ""

    texto = str(texto).strip().lower()

    reemplazos = {
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
        "ü": "u",
        "ñ": "n"
    }

    for origen, destino in reemplazos.items():
        texto = texto.replace(origen, destino)

    texto = re.sub(
        r"[^a-z0-9_ ]",
        " ",
        texto
    )

    texto = re.sub(
        r"\s+",
        " ",
        texto
    )

    return texto.strip()


def _obtener_tokens(texto):
    """
    Obtiene tokens relevantes para búsqueda de metadata.
    """

    texto = _normalizar_texto(texto)

    if not texto:
        return []

    palabras_excluir = {
        "una",
        "uno",
        "unos",
        "unas",
        "que",
        "tenga",
        "tengan",
        "tienen",
        "tiene",
        "con",
        "para",
        "por",
        "del",
        "las",
        "los",
        "un",
        "en",
        "de",
        "la",
        "el",
        "tabla",
        "tablas",
        "campo",
        "campos",
        "teradata",
        "necesito",
        "quiero",
        "dame",
        "dime",
        "buscar",
        "busca",
        "busco",
        "cuales",
        "cual",
        "cuantas",
        "cuantos",
        "hay",
        "existen",
        "existe",
        "tienen",
        "tiene",
        "donde",
        "estan",
        "este",
        "esta",
        "estas",
        "estos",
        "son",
        "mostrar",
        "muestra",
        "muestrame"
    }

    tokens = []

    for palabra in texto.split():

        if len(palabra) < 3:
            continue

        if palabra in palabras_excluir:
            continue

        tokens.append(palabra)

    return list(dict.fromkeys(tokens))


# ============================================================
# CANTIDAD SOLICITADA
# ============================================================

_NUMEROS = {
    "uno": 1,
    "una": 1,
    "dos": 2,
    "tres": 3,
    "cuatro": 4,
    "cinco": 5,
    "seis": 6,
    "siete": 7,
    "ocho": 8,
    "nueve": 9,
    "diez": 10,
    "once": 11,
    "doce": 12,
    "trece": 13,
    "catorce": 14,
    "quince": 15,
    "dieciseis": 16,
    "diecisiete": 17,
    "dieciocho": 18,
    "diecinueve": 19,
    "veinte": 20
}


def _detectar_cantidad(texto):
    """
    Detecta una cantidad explícita solicitada por el usuario.

    Ejemplos:
        dame 2 tablas -> 2
        muestra 10 tablas -> 10
        quiero tres tablas -> 3
        las primeras 5 -> 5

    Retorna:
        int o None
    """

    normalizado = _normalizar_texto(texto)

    # Números escritos como dígitos
    patrones = [
        r"\b(?:dame|mostrar|muestra|mostrarme|quiero|necesito|primeras?|primeros?)\s+(\d+)\b",
        r"\b(\d+)\s+(?:tablas?|resultados?|opciones?)\b",
        r"\btop\s+(\d+)\b"
    ]

    for patron in patrones:

        match = re.search(
            patron,
            normalizado,
            flags=re.IGNORECASE
        )

        if match:
            cantidad = int(match.group(1))

            if cantidad > 0:
                return cantidad

    # Números escritos con palabras
    for palabra, numero in _NUMEROS.items():

        patrones_palabra = [
            rf"\b(?:dame|mostrar|muestra|mostrarme|quiero|necesito)\s+{palabra}\s+(?:tablas?|resultados?|opciones?)\b",
            rf"\b{palabra}\s+(?:tablas?|resultados?|opciones?)\b"
        ]

        for patron in patrones_palabra:

            if re.search(
                patron,
                normalizado,
                flags=re.IGNORECASE
            ):
                return numero

    return None


def _detectar_modo(texto):
    """
    Detecta la intención principal de metadata.

    count:
        ¿Cuántas tablas tienen CUSTOMER_KEY?

    list:
        ¿Cuáles tienen CUSTOMER_KEY?

    detail:
        ¿Qué campos tiene ALDM_CUSTOMER?

    search:
        búsqueda general de tablas.
    """

    normalizado = _normalizar_texto(texto)

    if re.search(
        r"\b(cuantas|cuantos|cantidad|numero|numero de|total de)\b",
        normalizado
    ):
        return "count"

    if re.search(
        r"\b(cuales|que tablas|que tabla|lista|listar|dame|muestra|mostrar)\b",
        normalizado
    ):
        return "list"

    if re.search(
        r"\b(campos de|campo de|columnas de|columna de|estructura de|detalle de)\b",
        normalizado
    ):
        return "detail"

    return "search"


def _es_busqueda_por_campo(texto):
    """
    Determina si la pregunta busca explícitamente
    un campo/columna.

    Ejemplos:

        tablas que tienen CUSTOMER_KEY
        cuántas tablas tienen CUSTOMER_KEY
        qué tablas contienen CUSTOMER_KEY
        campo CUSTOMER_KEY

    No fuerza búsqueda por campo para preguntas
    generales como:

        clientes activos por periodo
    """

    normalizado = _normalizar_texto(texto)

    if re.search(
        r"\b(campo|campos|columna|columnas|field|fields)\b",
        normalizado
    ):
        return True

    if re.search(
        r"\b(tienen|tenga|tengan|contienen|contenga|contienen)\b",
        normalizado
    ):
        tokens = _obtener_tokens(normalizado)

        for token in tokens:

            if "_" in token:
                return True

            if token.isupper():
                return True

    # Identificadores técnicos tipo CUSTOMER_KEY
    for token in normalizado.split():

        if "_" in token and len(token) >= 3:
            return True

    return False


# ============================================================
# SCORE / RANKING
# ============================================================

def _score_texto(valor, tokens):
    """
    Calcula un score sencillo para ranking.
    """

    if valor is None:
        return 0

    texto = _normalizar_texto(valor)

    score = 0

    for token in tokens:

        if not token:
            continue

        if texto == token:
            score += 10

        elif f" {token} " in f" {texto} ":
            score += 6

        elif token in texto:
            score += 3

    return score


def _score_tabla(database, tabla, descripcion, tokens):
    """
    Ranking de tabla.
    """

    score = 0

    score += _score_texto(
        tabla,
        tokens
    ) * 3

    score += _score_texto(
        database,
        tokens
    )

    score += _score_texto(
        descripcion,
        tokens
    )

    return score


def _score_campo(database, tabla, campo, descripcion, tokens):
    """
    Ranking de campo.
    """

    score = 0

    score += _score_texto(
        campo,
        tokens
    ) * 5

    score += _score_texto(
        tabla,
        tokens
    ) * 2

    score += _score_texto(
        database,
        tokens
    )

    score += _score_texto(
        descripcion,
        tokens
    )

    return score


# ============================================================
# EJECUCIÓN GENERAL DE QUERIES
# ============================================================

def ejecutar_query_teradata(query):
    """
    Ejecuta una consulta SQL de SOLO LECTURA en Teradata.

    La validación ocurre ANTES de abrir la conexión.

    Esto constituye la segunda capa de seguridad,
    independiente del prompt o comportamiento del agente.
    """

    validar_sql_solo_lectura(query)

    conn = None

    try:

        print("[TERADATA] Ejecutando consulta de lectura...")

        conn = conectar_teradata()

        df = pd.read_sql(
            query,
            conn
        )

        print(
            "[TERADATA] Consulta ejecutada correctamente. "
            f"Registros: {len(df)}"
        )

        return df.to_dict(
            orient="records"
        )

    except Exception as e:

        print(
            f"[TERADATA ERROR] {str(e)}"
        )

        raise Exception(
            f"Error ejecutando query Teradata: {str(e)}"
        )

    finally:

        if conn:
            conn.close()


# ============================================================
# BUSCAR TABLAS EN METADATA
# ============================================================

def buscar_tablas_metadata(texto, limite=None):
    """
    Busca tablas en metadata.

    IMPORTANTE:
        limite=None significa que no se aplica un límite
        artificial de 5 resultados.

    El límite solamente se aplica cuando el usuario
    solicita explícitamente una cantidad.
    """

    tokens = _obtener_tokens(texto)

    print("")
    print("=" * 70)
    print("[METADATA TERADATA] BÚSQUEDA DE TABLAS")
    print("=" * 70)

    print(
        f"[METADATA TERADATA] Pregunta: {texto}"
    )

    print(
        f"[METADATA TERADATA] Tokens: {tokens}"
    )

    if not tokens:
        print(
            "[METADATA TERADATA] "
            "No existen tokens suficientes."
        )

        return []

    conn = None

    try:

        conn = conectar_teradata()

        condiciones = []
        parametros = []

        for token in tokens:

            condiciones.append(
                """
                (
                    UPPER(COALESCE(DATABASENAME, '')) LIKE ?
                    OR UPPER(COALESCE(TABLENAME, '')) LIKE ?
                    OR UPPER(COALESCE(COMMENTSTRING, '')) LIKE ?
                )
                """
            )

            patron = f"%{token.upper()}%"

            parametros.extend(
                [
                    patron,
                    patron,
                    patron
                ]
            )

        where_clause = " OR ".join(
            condiciones
        )

        query = f"""
            SELECT
                DATABASENAME,
                TABLENAME,
                COMMENTSTRING
            FROM {METADATA_TERADATA["tablas"]}
            WHERE {where_clause}
            QUALIFY ROW_NUMBER() OVER (
                PARTITION BY DATABASENAME, TABLENAME
                ORDER BY TABLENAME
            ) = 1
        """

        print(
            "[METADATA TERADATA] Consultando metadata..."
        )

        df = pd.read_sql(
            query,
            conn,
            params=parametros
        )

        df = _normalizar_columnas(df)

        print(
            "[METADATA TERADATA] "
            f"Tablas candidatas encontradas: {len(df)}"
        )

        if df.empty:
            return []

        resultados = []

        for _, row in df.iterrows():

            database = row.get(
                "DATABASENAME"
            )

            tabla = row.get(
                "TABLENAME"
            )

            descripcion = row.get(
                "COMMENTSTRING"
            )

            score = _score_tabla(
                database,
                tabla,
                descripcion,
                tokens
            )

            resultados.append(
                {
                    "motor": "TERADATA",
                    "database": database,
                    "tabla": tabla,
                    "descripcion_tabla": descripcion,
                    "score": score
                }
            )

        # Ranking
        resultados.sort(
            key=lambda x: (
                x.get("score", 0),
                str(x.get("tabla", ""))
            ),
            reverse=True
        )

        # Cantidad solicitada
        if limite is not None:

            resultados = resultados[
                :limite
            ]

        for indice, resultado in enumerate(
            resultados,
            start=1
        ):

            print(
                "[METADATA TERADATA] "
                f"#{indice} "
                f"{resultado['database']}."
                f"{resultado['tabla']} "
                f"| score={resultado.get('score', 0)}"
            )

        return resultados

    except Exception as e:

        print(
            "[METADATA TERADATA ERROR] "
            f"{str(e)}"
        )

        raise Exception(
            f"Error buscando metadata Teradata: {str(e)}"
        )

    finally:

        if conn:
            conn.close()


# ============================================================
# BUSCAR CAMPOS EN METADATA
# ============================================================

def buscar_campos_metadata(texto, limite=None):
    """
    Busca campos en metadata.

    Devuelve para el usuario únicamente:

        database
        tabla
        campo
        descripcion_campo
        score

    NO devuelve:

        tipo
        formato
        longitud
        nullable

    La metadata física queda fuera de la respuesta de usuario.
    """

    tokens = _obtener_tokens(texto)

    print("")
    print("=" * 70)
    print("[METADATA TERADATA] BÚSQUEDA DE CAMPOS")
    print("=" * 70)

    print(
        f"[METADATA TERADATA] Pregunta: {texto}"
    )

    print(
        f"[METADATA TERADATA] Tokens: {tokens}"
    )

    if not tokens:
        return []

    conn = None

    try:

        conn = conectar_teradata()

        condiciones = []
        parametros = []

        for token in tokens:

            condiciones.append(
                """
                (
                    UPPER(COALESCE(DATABASENAME, '')) LIKE ?
                    OR UPPER(COALESCE(TABLENAME, '')) LIKE ?
                    OR UPPER(COALESCE(COLUMNNAME, '')) LIKE ?
                    OR UPPER(COALESCE(COMMENTSTRING, '')) LIKE ?
                )
                """
            )

            patron = f"%{token.upper()}%"

            parametros.extend(
                [
                    patron,
                    patron,
                    patron,
                    patron
                ]
            )

        where_clause = " OR ".join(
            condiciones
        )

        query = f"""
            SELECT
                DATABASENAME,
                TABLENAME,
                COLUMNNAME,
                COMMENTSTRING
            FROM {METADATA_TERADATA["campos"]}
            WHERE {where_clause}
        """

        print(
            "[METADATA TERADATA] "
            "Consultando campos..."
        )

        df = pd.read_sql(
            query,
            conn,
            params=parametros
        )

        df = _normalizar_columnas(df)

        print(
            "[METADATA TERADATA] "
            f"Campos candidatos: {len(df)}"
        )

        if df.empty:
            return []

        resultados = []

        for _, row in df.iterrows():

            database = row.get(
                "DATABASENAME"
            )

            tabla = row.get(
                "TABLENAME"
            )

            campo = row.get(
                "COLUMNNAME"
            )

            descripcion = row.get(
                "COMMENTSTRING"
            )

            score = _score_campo(
                database,
                tabla,
                campo,
                descripcion,
                tokens
            )

            resultados.append(
                {
                    "motor": "TERADATA",
                    "database": database,
                    "tabla": tabla,
                    "campo": campo,
                    "descripcion_campo": descripcion,
                    "score": score
                }
            )

        resultados.sort(
            key=lambda x: (
                x.get("score", 0),
                str(x.get("tabla", "")),
                str(x.get("campo", ""))
            ),
            reverse=True
        )

        if limite is not None:

            resultados = resultados[
                :limite
            ]

        print(
            "[METADATA TERADATA] "
            f"Campos devueltos: {len(resultados)}"
        )

        for indice, resultado in enumerate(
            resultados,
            start=1
        ):

            print(
                "[METADATA TERADATA] "
                f"#{indice} "
                f"{resultado['database']}."
                f"{resultado['tabla']}."
                f"{resultado['campo']} "
                f"| score={resultado.get('score', 0)}"
            )

        return resultados

    except Exception as e:

        print(
            "[METADATA TERADATA ERROR] "
            f"{str(e)}"
        )

        raise Exception(
            f"Error buscando campos Teradata: {str(e)}"
        )

    finally:

        if conn:
            conn.close()


# ============================================================
# OBTENER METADATA COMPLETA DE UNA TABLA
# ============================================================

def obtener_metadata_tabla(database, tabla):
    """
    Obtiene metadata de una tabla.

    Devuelve:

        database
        tabla
        descripcion_tabla
        campos:
            campo
            descripcion

    NO expone:

        tipo
        formato
        nullable
        longitud
    """

    print("")
    print("=" * 70)
    print("[METADATA TERADATA] DETALLE DE TABLA")
    print("=" * 70)

    print(
        "[METADATA TERADATA] "
        f"Tabla: {database}.{tabla}"
    )

    conn = None

    try:

        conn = conectar_teradata()

        # ----------------------------------------------------
        # TABLA
        # ----------------------------------------------------

        query_tabla = f"""
            SELECT
                DATABASENAME,
                TABLENAME,
                COMMENTSTRING
            FROM {METADATA_TERADATA["tablas"]}
            WHERE UPPER(DATABASENAME) = ?
              AND UPPER(TABLENAME) = ?
        """

        df_tabla = pd.read_sql(
            query_tabla,
            conn,
            params=[
                database.upper(),
                tabla.upper()
            ]
        )

        df_tabla = _normalizar_columnas(
            df_tabla
        )

        if df_tabla.empty:

            print(
                "[METADATA TERADATA] "
                "Tabla no encontrada."
            )

            return None

        # ----------------------------------------------------
        # CAMPOS
        # ----------------------------------------------------

        query_campos = f"""
            SELECT
                DATABASENAME,
                TABLENAME,
                COLUMNNAME,
                COMMENTSTRING
            FROM {METADATA_TERADATA["campos"]}
            WHERE UPPER(DATABASENAME) = ?
              AND UPPER(TABLENAME) = ?
            ORDER BY COLUMNNAME
        """

        df_campos = pd.read_sql(
            query_campos,
            conn,
            params=[
                database.upper(),
                tabla.upper()
            ]
        )

        df_campos = _normalizar_columnas(
            df_campos
        )

        tabla_info = df_tabla.iloc[0]

        resultado = {
            "motor": "TERADATA",
            "database": tabla_info.get(
                "DATABASENAME"
            ),
            "tabla": tabla_info.get(
                "TABLENAME"
            ),
            "descripcion_tabla": tabla_info.get(
                "COMMENTSTRING"
            ),
            "campos": []
        }

        for _, row in df_campos.iterrows():

            resultado["campos"].append(
                {
                    "campo": row.get(
                        "COLUMNNAME"
                    ),
                    "descripcion": row.get(
                        "COMMENTSTRING"
                    )
                }
            )

        print(
            "[METADATA TERADATA] "
            f"Tabla encontrada. "
            f"Campos: {len(resultado['campos'])}"
        )

        return resultado

    except Exception as e:

        print(
            "[METADATA TERADATA ERROR] "
            f"{str(e)}"
        )

        raise Exception(
            f"Error obteniendo metadata de Teradata: {str(e)}"
        )

    finally:

        if conn:
            conn.close()


# ============================================================
# BUSCAR METADATA TERADATA
# ============================================================

def buscar_metadata_teradata(texto, limite_tablas=None):
    """
    Descubrimiento inteligente de metadata Teradata.

    Soporta:

        1. COUNT

            ¿Cuántas tablas tienen CUSTOMER_KEY?

        2. LIST

            ¿Cuáles tienen CUSTOMER_KEY?

        3. CANTIDAD EXPLÍCITA

            Dame 2 tablas con CUSTOMER_KEY.
            Dame 10 tablas con CUSTOMER_KEY.

        4. DETALLE

            ¿Qué campos tiene ALDM_CUSTOMER?

        5. BÚSQUEDA GENERAL

            clientes activos por periodo

    IMPORTANTE:

        No genera SQL de negocio.
        No ejecuta consultas de usuario.
        No realiza operaciones de escritura.
    """

    print("")
    print("=" * 70)
    print("[METADATA TERADATA] DESCUBRIMIENTO DE METADATA")
    print("=" * 70)

    print(
        f"[METADATA TERADATA] Pregunta: {texto}"
    )

    modo = _detectar_modo(
        texto
    )

    cantidad = _detectar_cantidad(
        texto
    )

    busqueda_por_campo = _es_busqueda_por_campo(
        texto
    )

    print(
        f"[METADATA TERADATA] Modo: {modo}"
    )

    if cantidad is not None:

        print(
            "[METADATA TERADATA] "
            f"Cantidad solicitada: {cantidad}"
        )

    else:

        print(
            "[METADATA TERADATA] "
            "Cantidad solicitada: NO ESPECIFICADA"
        )

    print(
        "[METADATA TERADATA] "
        f"Búsqueda por campo: "
        f"{'SI' if busqueda_por_campo else 'NO'}"
    )

    try:

        # ====================================================
        # 1. BÚSQUEDA POR CAMPO
        # ====================================================

        if busqueda_por_campo:

            print(
                "[METADATA TERADATA] "
                "Ruta semántica: CAMPOS -> TABLAS"
            )

            campos = buscar_campos_metadata(
                texto,
                limite=None
            )

            if not campos:

                return {
                    "motor": "TERADATA",
                    "pregunta": texto,
                    "modo": modo,
                    "busqueda_por_campo": True,
                    "cantidad_solicitada": cantidad,
                    "cantidad_explicita": cantidad is not None,
                    "total_candidatas": 0,
                    "total_tablas": 0,
                    "tablas": [],
                    "campos": []
                }

            # ----------------------------------------------
            # TABLAS ÚNICAS
            # ----------------------------------------------

            tablas_map = {}

            for campo in campos:

                clave = (
                    str(campo.get("database", "")),
                    str(campo.get("tabla", ""))
                )

                if clave not in tablas_map:

                    tablas_map[clave] = {
                        "motor": "TERADATA",
                        "database": campo.get(
                            "database"
                        ),
                        "tabla": campo.get(
                            "tabla"
                        ),
                        "score": campo.get(
                            "score",
                            0
                        ),
                        "campos": []
                    }

                tablas_map[clave]["campos"].append(
                    {
                        "campo": campo.get(
                            "campo"
                        ),
                        "descripcion": campo.get(
                            "descripcion_campo"
                        )
                    }
                )

            tablas = list(
                tablas_map.values()
            )

            # Ranking por tabla
            tablas.sort(
                key=lambda x: (
                    x.get("score", 0),
                    str(x.get("tabla", ""))
                ),
                reverse=True
            )

            total_tablas = len(
                tablas
            )

            print(
                "[METADATA TERADATA] "
                f"Tablas únicas encontradas por campo: "
                f"{total_tablas}"
            )

            # ----------------------------------------------
            # COUNT
            # ----------------------------------------------

            if modo == "count":

                print(
                    "[METADATA TERADATA] "
                    "COUNT por campo detectado. "
                    "No se cargará detalle de tablas."
                )

                return {
                    "motor": "TERADATA",
                    "pregunta": texto,
                    "modo": "count",
                    "busqueda_por_campo": True,
                    "cantidad_solicitada": cantidad,
                    "cantidad_explicita": cantidad is not None,
                    "total_candidatas": len(campos),
                    "total_tablas": total_tablas,
                    "tablas": [],
                    "campos": []
                }

            # ----------------------------------------------
            # LIST
            # ----------------------------------------------

            if cantidad is not None:

                tablas = tablas[
                    :cantidad
                ]

            # ----------------------------------------------
            # CARGAR DESCRIPCIÓN DE TABLA
            # ----------------------------------------------

            resultados = []

            for indice, tabla_info in enumerate(
                tablas,
                start=1
            ):

                database = tabla_info.get(
                    "database"
                )

                tabla = tabla_info.get(
                    "tabla"
                )

                print(
                    "[METADATA TERADATA] "
                    f"Cargando detalle de tabla "
                    f"#{indice}: "
                    f"{database}.{tabla}"
                )

                detalle = obtener_metadata_tabla(
                    database,
                    tabla
                )

                if not detalle:
                    continue

                # Campos que realmente coinciden
                campos_encontrados = (
                    tabla_info.get(
                        "campos",
                        []
                    )
                )

                resultados.append(
                    {
                        "motor": "TERADATA",
                        "database": detalle.get(
                            "database",
                            database
                        ),
                        "tabla": detalle.get(
                            "tabla",
                            tabla
                        ),
                        "descripcion_tabla": detalle.get(
                            "descripcion_tabla"
                        ),
                        "campos": campos_encontrados,
                        "todos_los_campos": detalle.get(
                            "campos",
                            []
                        ),
                        "score": tabla_info.get(
                            "score",
                            0
                        )
                    }
                )

            print(
                "[METADATA TERADATA] "
                f"Tablas con metadata completa: "
                f"{len(resultados)}"
            )

            return {
                "motor": "TERADATA",
                "pregunta": texto,
                "modo": modo,
                "busqueda_por_campo": True,
                "cantidad_solicitada": cantidad,
                "cantidad_explicita": cantidad is not None,
                "total_candidatas": len(campos),
                "total_tablas": total_tablas,
                "tablas": resultados,
                "campos": campos
            }

        # ====================================================
        # 2. DETALLE DE TABLA
        # ====================================================

        if modo == "detail":

            print(
                "[METADATA TERADATA] "
                "Ruta: DETALLE DE TABLA"
            )

            tablas = buscar_tablas_metadata(
                texto,
                limite=None
            )

            if not tablas:

                return {
                    "motor": "TERADATA",
                    "pregunta": texto,
                    "modo": "detail",
                    "busqueda_por_campo": False,
                    "cantidad_solicitada": cantidad,
                    "cantidad_explicita": cantidad is not None,
                    "total_tablas": 0,
                    "tablas": []
                }

            if cantidad is not None:

                tablas = tablas[
                    :cantidad
                ]

            resultados = []

            for tabla_info in tablas:

                detalle = obtener_metadata_tabla(
                    tabla_info.get("database"),
                    tabla_info.get("tabla")
                )

                if detalle:

                    resultados.append(
                        detalle
                    )

            return {
                "motor": "TERADATA",
                "pregunta": texto,
                "modo": "detail",
                "busqueda_por_campo": False,
                "cantidad_solicitada": cantidad,
                "cantidad_explicita": cantidad is not None,
                "total_tablas": len(resultados),
                "tablas": resultados
            }

        # ====================================================
        # 3. BÚSQUEDA GENERAL DE TABLAS
        # ====================================================

        print(
            "[METADATA TERADATA] "
            "Ruta semántica: TABLAS"
        )

        # Para COUNT general:
        # primero encontramos las candidatas y contamos.
        tablas = buscar_tablas_metadata(
            texto,
            limite=None
        )

        total_tablas = len(
            tablas
        )

        # ====================================================
        # COUNT
        # ====================================================

        if modo == "count":

            print(
                "[METADATA TERADATA] "
                "COUNT de tablas."
            )

            return {
                "motor": "TERADATA",
                "pregunta": texto,
                "modo": "count",
                "busqueda_por_campo": False,
                "cantidad_solicitada": cantidad,
                "cantidad_explicita": cantidad is not None,
                "total_candidatas": total_tablas,
                "total_tablas": total_tablas,
                "tablas": []
            }

        # ====================================================
        # LIST / SEARCH
        # ====================================================

        if cantidad is not None:

            tablas = tablas[
                :cantidad
            ]

        # ====================================================
        # CARGAR DETALLE
        # ====================================================

        resultados = []

        for indice, tabla_info in enumerate(
            tablas,
            start=1
        ):

            database = tabla_info.get(
                "database"
            )

            tabla = tabla_info.get(
                "tabla"
            )

            print(
                "[METADATA TERADATA] "
                f"Cargando detalle #{indice}: "
                f"{database}.{tabla}"
            )

            detalle = obtener_metadata_tabla(
                database,
                tabla
            )

            if not detalle:
                continue

            resultados.append(
                {
                    "motor": "TERADATA",
                    "database": detalle.get(
                        "database",
                        database
                    ),
                    "tabla": detalle.get(
                        "tabla",
                        tabla
                    ),
                    "descripcion_tabla": detalle.get(
                        "descripcion_tabla"
                    ),
                    "campos": detalle.get(
                        "campos",
                        []
                    ),
                    "score": tabla_info.get(
                        "score",
                        0
                    )
                }
            )

        print(
            "[METADATA TERADATA] "
            f"Tablas con metadata completa: "
            f"{len(resultados)}"
        )

        for resultado in resultados:

            print(
                "[METADATA TERADATA] "
                f"{resultado['database']}."
                f"{resultado['tabla']} | "
                f"campos={len(resultado.get('campos', []))}"
            )

        return {
            "motor": "TERADATA",
            "pregunta": texto,
            "modo": modo,
            "busqueda_por_campo": False,
            "cantidad_solicitada": cantidad,
            "cantidad_explicita": cantidad is not None,
            "total_candidatas": total_tablas,
            "total_tablas": len(resultados),
            "tablas": resultados
        }

    except Exception as e:

        print(
            "[METADATA TERADATA ERROR] "
            f"{str(e)}"
        )

        raise Exception(
            f"Error descubriendo metadata Teradata: {str(e)}"
        )


# ============================================================
# SEGURIDAD SQL - SOLO LECTURA
# ============================================================

def validar_sql_solo_lectura(sql):
    """
    Valida que una sentencia SQL sea exclusivamente
    de lectura.

    PERMITIDO:

        SELECT
        WITH ... SELECT
        EXPLAIN

    BLOQUEADO:

        INSERT
        UPDATE
        DELETE
        MERGE
        UPSERT
        DROP
        ALTER
        CREATE
        TRUNCATE
        GRANT
        REVOKE
        RENAME
        CALL
        EXEC
        EXECUTE
        REPLACE

    IMPORTANTE:

        Esta función debe ejecutarse ANTES de abrir
        la conexión a Teradata.
    """

    if not sql:

        raise ValueError(
            "SQL vacío."
        )

    consulta = str(
        sql
    ).strip()

    # ========================================================
    # ELIMINAR COMENTARIOS
    # ========================================================

    consulta = re.sub(
        r"/\*.*?\*/",
        " ",
        consulta,
        flags=re.DOTALL
    )

    consulta = re.sub(
        r"--.*?$",
        " ",
        consulta,
        flags=re.MULTILINE
    )

    consulta = consulta.strip()

    # ========================================================
    # ELIMINAR ; FINAL
    # ========================================================

    consulta = consulta.rstrip(
        ";"
    ).strip()

    if not consulta:

        raise ValueError(
            "SQL vacío."
        )

    # ========================================================
    # NO MULTI-SENTENCIA
    # ========================================================

    if ";" in consulta:

        raise PermissionError(
            "SQL BLOQUEADO: "
            "no se permiten múltiples sentencias."
        )

    # ========================================================
    # OPERACIONES PROHIBIDAS
    # ========================================================

    operaciones_prohibidas = [
        "INSERT",
        "UPDATE",
        "DELETE",
        "MERGE",
        "UPSERT",
        "DROP",
        "ALTER",
        "CREATE",
        "TRUNCATE",
        "GRANT",
        "REVOKE",
        "RENAME",
        "CALL",
        "EXEC",
        "EXECUTE",
        "REPLACE"
    ]

    patron = (
        r"\b("
        + "|".join(
            operaciones_prohibidas
        )
        + r")\b"
    )

    coincidencia = re.search(
        patron,
        consulta,
        flags=re.IGNORECASE
    )

    if coincidencia:

        operacion = coincidencia.group(
            1
        ).upper()

        raise PermissionError(
            f"SQL BLOQUEADO: operación "
            f"'{operacion}' no permitida. "
            "El sistema únicamente permite "
            "consultas de lectura."
        )

    # ========================================================
    # DEBE SER SELECT / WITH / EXPLAIN
    # ========================================================

    if not re.match(
        r"^(SELECT|WITH|EXPLAIN)\b",
        consulta,
        flags=re.IGNORECASE
    ):

        raise PermissionError(
            "SQL BLOQUEADO: únicamente se permiten "
            "consultas SELECT, WITH o EXPLAIN."
        )

    return True