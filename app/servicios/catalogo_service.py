# ============================================================
# SERVICIO DE CATÁLOGO DE CONSULTAS
# ============================================================

import re
import unicodedata
import pandas as pd

from app.servicios.bases.connection_manager import (
    conectar_netezza,
    conectar_teradata
)


class CatalogoService:

    # --------------------------------------------------------
    # TABLA DEL CATÁLOGO
    # --------------------------------------------------------

    TABLA_CATALOGO = "CONTROL_MAKO..TABLERO_CATALOGO_CONSULTAS"

    # --------------------------------------------------------
    # NORMALIZAR TEXTO
    # --------------------------------------------------------

    def normalizar_texto(self, texto):

        if not texto:
            return ""

        texto = str(texto).lower().strip()

        # Quitar tildes
        texto = unicodedata.normalize(
            "NFD",
            texto
        )

        texto = "".join(
            c
            for c in texto
            if unicodedata.category(c) != "Mn"
        )

        # Normalizar espacios
        texto = re.sub(
            r"\s+",
            " ",
            texto
        )

        return texto

    # --------------------------------------------------------
    # OBTENER CATÁLOGO
    #
    # El catálogo siempre está almacenado en Netezza.
    # --------------------------------------------------------

    def obtener_catalogo(self):

        sql = f"""
        SELECT
            ID_CONSULTA,
            TIPO_CONSULTA,
            GRUPO,
            AGENTE,
            DESCRIPCION,
            PALABRAS_CLAVE,
            SQL_TEMPLATE,
            PARAMETROS,
            BASE_DATOS,
            TIPO_EJECUCION,
            PRIORIDAD,
            ACTIVO
        FROM {self.TABLA_CATALOGO}
        WHERE ACTIVO = 1
        ORDER BY PRIORIDAD DESC
        """

        conn = None

        try:

            conn = conectar_netezza()

            df = pd.read_sql(
                sql,
                conn
            )

            print(
                f"[CATALOGO] Registros cargados: {len(df)}"
            )

            return df

        except Exception as e:

            print(
                f"[ERROR CATALOGO] {str(e)}"
            )

            raise

        finally:

            if conn:

                try:
                    conn.close()
                except Exception:
                    pass

    # --------------------------------------------------------
    # BUSCAR POR TIPO
    # --------------------------------------------------------

    def buscar_por_tipo(self, tipo_consulta):

        print(
            f"[CATALOGO] Buscando tipo: {tipo_consulta}"
        )

        df = self.obtener_catalogo()

        if df is None or df.empty:

            print(
                "[CATALOGO] Catálogo vacío."
            )

            return None

        tipo = self.normalizar_texto(
            tipo_consulta
        )

        resultado = df[
            df["TIPO_CONSULTA"]
            .astype(str)
            .apply(self.normalizar_texto)
            == tipo
        ]

        if resultado.empty:

            print(
                "[CATALOGO] No se encontró el tipo."
            )

            return None

        print(
            f"[CATALOGO] Registros encontrados: "
            f"{len(resultado)}"
        )

        return resultado

    # --------------------------------------------------------
    # BUSCAR POR PALABRAS CLAVE
    # --------------------------------------------------------

    def buscar_por_palabras(self, pregunta):

        print(
            f"[CATALOGO] Analizando pregunta: {pregunta}"
        )

        pregunta_normalizada = self.normalizar_texto(
            pregunta
        )

        print(
            f"[CATALOGO] Pregunta normalizada: "
            f"{pregunta_normalizada}"
        )

        df = self.obtener_catalogo()

        if df is None or df.empty:

            print(
                "[CATALOGO] Catálogo vacío."
            )

            return None

        # ----------------------------------------------------
        # Quitar números para identificar la intención.
        #
        # Ejemplo:
        #
        # "ultimos 5 schedules ejecutados"
        #
        # se convierte en:
        #
        # "ultimos schedules ejecutados"
        #
        # El número se utilizará posteriormente como parámetro.
        # ----------------------------------------------------

        pregunta_sin_numeros = re.sub(
            r"\b\d+\b",
            " ",
            pregunta_normalizada
        )

        pregunta_sin_numeros = re.sub(
            r"\s+",
            " ",
            pregunta_sin_numeros
        ).strip()

        mejor_resultado = None
        mejor_puntaje = 0

        # ----------------------------------------------------
        # EVALUAR CADA REGISTRO DEL CATÁLOGO
        # ----------------------------------------------------

        for _, fila in df.iterrows():

            tipo = fila["TIPO_CONSULTA"]

            palabras = fila["PALABRAS_CLAVE"]

            if not palabras:

                continue

            lista_palabras = str(
                palabras
            ).split("|")

            puntaje = 0

            # ------------------------------------------------
            # EVALUAR CADA PALABRA CLAVE
            # ------------------------------------------------

            for palabra in lista_palabras:

                palabra_normalizada = (
                    self.normalizar_texto(
                        palabra
                    )
                )

                if not palabra_normalizada:

                    continue

                # --------------------------------------------
                # 1. COINCIDENCIA DIRECTA
                # --------------------------------------------

                if (
                    palabra_normalizada
                    in pregunta_normalizada
                ):

                    puntaje += (
                        len(
                            palabra_normalizada.split()
                        ) * 10
                    )

                    continue

                # --------------------------------------------
                # 2. COINCIDENCIA IGNORANDO NÚMEROS
                #
                # Ejemplo:
                #
                # catálogo:
                # "ultimos schedules ejecutados"
                #
                # pregunta:
                # "ultimos 5 schedules ejecutados"
                # --------------------------------------------

                palabra_sin_numeros = re.sub(
                    r"\b\d+\b",
                    " ",
                    palabra_normalizada
                )

                palabra_sin_numeros = re.sub(
                    r"\s+",
                    " ",
                    palabra_sin_numeros
                ).strip()

                if (
                    palabra_sin_numeros
                    and
                    palabra_sin_numeros
                    in pregunta_sin_numeros
                ):

                    puntaje += (
                        len(
                            palabra_sin_numeros.split()
                        ) * 10
                    )

                    continue

                # --------------------------------------------
                # 3. COINCIDENCIA POR PALABRAS
                # --------------------------------------------

                palabras_clave = (
                    palabra_normalizada.split()
                )

                palabras_pregunta = set(
                    pregunta_sin_numeros.split()
                )

                coincidencias = sum(
                    1
                    for palabra_clave
                    in palabras_clave
                    if palabra_clave
                    in palabras_pregunta
                )

                if coincidencias:

                    porcentaje = (
                        coincidencias
                        / len(palabras_clave)
                    )

                    # Consideramos válida la coincidencia
                    # cuando al menos el 50% de las palabras
                    # clave aparecen en la pregunta.

                    if porcentaje >= 0.5:

                        puntaje += int(
                            porcentaje * 10
                        )

            print(
                f"[CATALOGO] Evaluando: "
                f"{tipo} | Puntaje: {puntaje}"
            )

            # ------------------------------------------------
            # GUARDAR MEJOR COINCIDENCIA
            # ------------------------------------------------

            if puntaje > mejor_puntaje:

                mejor_puntaje = puntaje

                mejor_resultado = fila

        # ----------------------------------------------------
        # SIN COINCIDENCIA
        # ----------------------------------------------------

        if mejor_resultado is None:

            print(
                "[CATALOGO] No se encontró coincidencia."
            )

            return None

        # ----------------------------------------------------
        # COINCIDENCIA ENCONTRADA
        # ----------------------------------------------------

        print(
            f"[CATALOGO] Coincidencia encontrada: "
            f"{mejor_resultado['TIPO_CONSULTA']}"
        )

        print(
            f"[CATALOGO] Puntaje: "
            f"{mejor_puntaje}"
        )

        print(
            f"[CATALOGO] Grupo: "
            f"{mejor_resultado['GRUPO']}"
        )

        print(
            f"[CATALOGO] Agente: "
            f"{mejor_resultado['AGENTE']}"
        )

        print(
            f"[CATALOGO] Base de datos: "
            f"{mejor_resultado['BASE_DATOS']}"
        )

        print(
            f"[CATALOGO] Tipo ejecución: "
            f"{mejor_resultado['TIPO_EJECUCION']}"
        )

        return mejor_resultado.to_frame().T

    # --------------------------------------------------------
    # EXTRAER PARÁMETROS DE LA PREGUNTA
    # --------------------------------------------------------

    def extraer_parametros(
        self,
        pregunta,
        fila
    ):

        parametros = {}

        configuracion = fila.get(
            "PARAMETROS"
        )

        if not configuracion:

            return parametros

        configuracion = str(
            configuracion
        ).upper()

        # ----------------------------------------------------
        # LIMITE
        #
        # Ejemplo:
        #
        # "últimos 5 schedules"
        #
        # obtiene:
        #
        # LIMITE = 5
        # ----------------------------------------------------

        if "LIMITE" in configuracion:

            match = re.search(
                r"\b(\d+)\b",
                pregunta
            )

            if match:

                parametros["LIMITE"] = int(
                    match.group(1)
                )

            else:

                # Valor por defecto
                parametros["LIMITE"] = 10

        return parametros

    # --------------------------------------------------------
    # CONSTRUIR SQL
    # --------------------------------------------------------

    def construir_sql(
        self,
        pregunta,
        fila
    ):

        sql_template = fila["SQL_TEMPLATE"]

        if not sql_template:

            raise Exception(
                "El catálogo no tiene SQL_TEMPLATE."
            )

        parametros = self.extraer_parametros(
            pregunta,
            fila
        )

        sql = str(
            sql_template
        )

        # ----------------------------------------------------
        # REEMPLAZAR PARÁMETROS
        # ----------------------------------------------------

        for nombre, valor in parametros.items():

            sql = sql.replace(
                "{" + nombre + "}",
                str(valor)
            )

        # ----------------------------------------------------
        # LIMPIEZA DEL SQL
        # ----------------------------------------------------

        sql = re.sub(
            r"\s+",
            " ",
            sql
        ).strip()

        print(
            f"[CATALOGO SQL] {sql}"
        )

        return sql

    # --------------------------------------------------------
    # OBTENER CONEXIÓN SEGÚN BASE_DATOS
    # --------------------------------------------------------

    def obtener_conexion(
        self,
        base_datos
    ):

        if not base_datos:

            raise Exception(
                "El catálogo no tiene BASE_DATOS."
            )

        bd = self.normalizar_texto(
            base_datos
        )

        print(
            f"[CATALOGO] Conector solicitado: {bd}"
        )

        # ----------------------------------------------------
        # NETEZZA
        # ----------------------------------------------------

        if bd in (
            "netezza",
            "nz"
        ):

            print(
                "[CATALOGO] Ejecutando SQL en NETEZZA"
            )

            return conectar_netezza()

        # ----------------------------------------------------
        # TERADATA
        # ----------------------------------------------------

        if bd in (
            "teradata",
            "td"
        ):

            print(
                "[CATALOGO] Ejecutando SQL en TERADATA"
            )

            return conectar_teradata()

        # ----------------------------------------------------
        # BASE NO SOPORTADA
        # ----------------------------------------------------

        raise Exception(
            f"Base de datos no soportada: {base_datos}"
        )

    # --------------------------------------------------------
    # EJECUTAR CONSULTA DEL CATÁLOGO
    # --------------------------------------------------------

    def ejecutar_catalogo(
        self,
        pregunta,
        fila
    ):

        sql = self.construir_sql(
            pregunta,
            fila
        )

        base_datos = fila["BASE_DATOS"]

        conn = None

        try:

            conn = self.obtener_conexion(
                base_datos
            )

            df = pd.read_sql(
                sql,
                conn
            )

            print(
                f"[CATALOGO] Consulta ejecutada correctamente."
            )

            print(
                f"[CATALOGO] Registros obtenidos: "
                f"{len(df)}"
            )

            return {
                "tipo": "catalogo",

                "tipo_consulta":
                    fila["TIPO_CONSULTA"],

                "grupo":
                    fila["GRUPO"],

                "agente":
                    fila["AGENTE"],

                "base_datos":
                    fila["BASE_DATOS"],

                "tipo_ejecucion":
                    fila["TIPO_EJECUCION"],

                "descripcion":
                    fila["DESCRIPCION"],

                "sql":
                    sql,

                "datos":
                    df
            }

        except Exception as e:

            print(
                f"[ERROR CATALOGO EJECUCION] "
                f"{str(e)}"
            )

            raise

        finally:

            if conn:

                try:
                    conn.close()

                except Exception:
                    pass

    # --------------------------------------------------------
    # RESOLVER
    #
    # Flujo:
    #
    # Pregunta
    #    ↓
    # buscar_por_palabras()
    #    ↓
    # catálogo
    #    ↓
    # BASE_DATOS
    #    ↓
    # construir SQL
    #    ↓
    # ejecutar en BD correspondiente
    # --------------------------------------------------------

    def resolver(self, pregunta):

        fila = self.buscar_por_palabras(pregunta)

        if fila is None:
            return None

        registro = fila.iloc[0]

        # Construir SQL con los parámetros detectados en la pregunta.
        sql = self.construir_sql(pregunta, registro)

        # Ejecutar la consulta aquí para que el resultado del catálogo
        # contenga los datos reales y no solamente los metadatos.
        resultado = self.ejecutar_catalogo(pregunta, registro)
        df = resultado.get("datos")

        # Convertir DataFrame a una estructura serializable por Flask/JSON.
        if isinstance(df, pd.DataFrame):
            datos = df.where(pd.notnull(df), None).to_dict(orient="records")
        else:
            datos = df

        print(
            f"[CATALOGO] Datos preparados para Router: "
            f"{len(datos) if isinstance(datos, list) else 0}"
        )

        return {
            "tipo": "catalogo",
            "tipo_consulta": registro["TIPO_CONSULTA"],
            "grupo": registro["GRUPO"],
            "agente": registro["AGENTE"],
            "base_datos": registro["BASE_DATOS"],
            "tipo_ejecucion": registro["TIPO_EJECUCION"],
            "descripcion": registro["DESCRIPCION"],
            "sql": sql,
            "datos": datos
        }


    # ============================================================
    # EJECUTAR CONSULTA RESUELTA DEL CATÁLOGO
    # ============================================================

    def ejecutar_resuelto(self, resultado):

        if not resultado:
            raise Exception(
                "No existe una consulta resuelta para ejecutar."
            )

        # Si resolver() ya obtuvo datos, reutilizarlos y evitar una segunda
        # ejecución de la misma consulta cuando el Router llame este método.
        if "datos" in resultado and resultado.get("datos") is not None:
            print("[CATALOGO] Reutilizando datos ya obtenidos por resolver().")
            return {
                "ok": True,
                "datos": resultado.get("datos"),
                "base_datos": resultado.get("base_datos"),
                "sql": resultado.get("sql")
            }

        sql = resultado.get("sql")
        base_datos = resultado.get("base_datos")

        if not sql:
            raise Exception(
                "La consulta resuelta no contiene SQL."
            )

        if not base_datos:
            raise Exception(
                "La consulta resuelta no indica BASE_DATOS."
            )

        base_datos = str(base_datos).strip().upper()

        print(
            f"[CATALOGO] Ejecutando SQL en {base_datos}"
        )

        print(
            f"[CATALOGO SQL] {sql}"
        )

        # ========================================================
        # IMPORTS DE CONEXIÓN
        # ========================================================

        from app.servicios.bases.connection_manager import (
            conectar_netezza,
            conectar_teradata
        )

        import pandas as pd

        conn = None

        try:

            # ====================================================
            # SELECCIONAR CONECTOR SEGÚN EL CATÁLOGO
            # ====================================================

            if base_datos == "NETEZZA":

                print(
                    "[CATALOGO] Conector solicitado: netezza"
                )

                conn = conectar_netezza()

            elif base_datos == "TERADATA":

                print(
                    "[CATALOGO] Conector solicitado: teradata"
                )

                conn = conectar_teradata()

            else:

                raise Exception(
                    f"Base de datos no soportada: {base_datos}"
                )

            # ====================================================
            # EJECUTAR CONSULTA
            # ====================================================

            print(
                f"[CATALOGO] Ejecutando SQL en {base_datos}"
            )

            df = pd.read_sql(
                sql,
                conn
            )

            print(
                "[CATALOGO] Consulta ejecutada correctamente."
            )

            print(
                f"[CATALOGO] Registros obtenidos: {len(df)}"
            )

            return {
                "ok": True,
                "datos": df,
                "base_datos": base_datos,
                "sql": sql
            }

        except Exception as e:

            print(
                f"[CATALOGO] ERROR ejecutando consulta: {e}"
            )

            raise

        finally:

            if conn is not None:

                try:
                    conn.close()

                except Exception:
                    pass
# ============================================================
# INSTANCIA ÚNICA
# ============================================================

catalogo_service = CatalogoService()