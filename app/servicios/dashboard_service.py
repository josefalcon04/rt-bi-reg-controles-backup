# ============================================================
# DASHBOARD SERVICE
# ============================================================
#
# Responsabilidad:
#   - Identificar una fuente Netezza / Teradata.
#   - Ejecutar SOLO consultas SELECT.
#   - Obtener una muestra de datos.
#   - Analizar columnas.
#   - Identificar dimensiones, métricas y fechas.
#   - Normalizar métricas numéricas.
#   - Entregar información al DashboardPlanner.
#
# IMPORTANTE:
#   - NO hace INSERT.
#   - NO hace UPDATE.
#   - NO hace DELETE.
#   - NO hace DROP.
#   - NO hace TRUNCATE.
#   - NO hace CREATE.
#
# ============================================================

import os
import re

import pandas as pd

from app.servicios.bases.connection_manager import (
    conectar_netezza,
    conectar_teradata
)


class DashboardService:

    def __init__(self):

        self.nombre = "dashboard_service"

    # ========================================================
    # ANALIZAR FUENTE
    # ========================================================

    def analizar_fuente(
        self,
        motor,
        database,
        objeto,
        limite_muestra=5000
    ):

        print("\n" + "=" * 70)
        print("[DASHBOARD SERVICE] ANALIZANDO FUENTE")
        print("=" * 70)

        motor = str(
            motor or ""
        ).upper().strip()

        database = str(
            database or ""
        ).strip()

        objeto = str(
            objeto or ""
        ).strip()

        if motor not in (
            "NETEZZA",
            "TERADATA"
        ):

            raise ValueError(
                "Motor no soportado: "
                + motor
            )

        if not database:

            raise ValueError(
                "La base de datos es obligatoria."
            )

        if not objeto:

            raise ValueError(
                "La tabla o vista es obligatoria."
            )

        # ----------------------------------------------------
        # Normalizar objeto
        # ----------------------------------------------------

        objeto = objeto.replace(
            "`",
            ""
        ).strip()

        # ----------------------------------------------------
        # Obtener datos
        # ----------------------------------------------------

        df = self.obtener_muestra(
            motor=motor,
            database=database,
            objeto=objeto,
            limite=limite_muestra
        )

        # ----------------------------------------------------
        # Normalizar tipos de columnas
        # ----------------------------------------------------
        #
        # Importante:
        # Netezza puede devolver determinados campos
        # numéricos como object/string.
        #
        # Ejemplo:
        #
        # TOTAL -> object
        #
        # Si contiene valores numéricos, lo convertimos
        # antes de entregarlo al Planner y Builder.
        #
        # ----------------------------------------------------

        df = self._normalizar_columnas(
            df
        )

        # ----------------------------------------------------
        # Analizar columnas
        # ----------------------------------------------------

        columnas = []

        dimensiones = []

        metricas = []

        fechas = []

        for columna in df.columns:

            nombre = str(
                columna
            )

            serie = df[columna]

            tipo = str(
                serie.dtype
            )

            cardinalidad = int(
                serie.nunique(
                    dropna=True
                )
            )

            informacion = {

                "nombre": nombre,

                "tipo": tipo,

                "nulos": int(
                    serie.isna().sum()
                ),

                "cardinalidad":
                    cardinalidad
            }

            columnas.append(
                informacion
            )

            # ------------------------------------------------
            # FECHA
            # ------------------------------------------------

            if self._es_fecha(
                nombre,
                serie
            ):

                fechas.append(
                    informacion
                )

                continue

            # ------------------------------------------------
            # MÉTRICA
            # ------------------------------------------------

            if self._es_metrica(
                nombre,
                serie
            ):

                metricas.append(
                    informacion
                )

                continue

            # ------------------------------------------------
            # DIMENSIÓN
            # ------------------------------------------------

            if self._es_dimension(
                nombre,
                serie
            ):

                dimensiones.append(
                    informacion
                )

        resultado = {

            "estado":
                "ok",

            "motor":
                motor,

            "database":
                database,

            "objeto":
                objeto,

            "columnas":
                columnas,

            "dimensiones":
                dimensiones,

            "metricas":
                metricas,

            "fechas":
                fechas,

            "filas_muestra":
                len(df),

            "columnas_muestra":
                len(df.columns)
        }

        print(
            "[DASHBOARD SERVICE] "
            f"Filas: {len(df)}"
        )

        print(
            "[DASHBOARD SERVICE] "
            f"Columnas: {len(df.columns)}"
        )

        print(
            "[DASHBOARD SERVICE] "
            f"Dimensiones: {len(dimensiones)}"
        )

        print(
            "[DASHBOARD SERVICE] "
            f"Métricas: {len(metricas)}"
        )

        print(
            "[DASHBOARD SERVICE] "
            f"Fechas: {len(fechas)}"
        )

        print("=" * 70)

        return resultado

    # ========================================================
    # NORMALIZAR COLUMNAS
    # ========================================================

    def _normalizar_columnas(
        self,
        df
    ):

        if df is None:

            return df

        if df.empty:

            return df

        print(
            "[DASHBOARD SERVICE] "
            "Normalizando tipos de columnas..."
        )

        for columna in df.columns:

            nombre = str(
                columna
            )

            serie = df[columna]

            # ------------------------------------------------
            # Si ya es numérica, no hacemos nada
            # ------------------------------------------------

            if pd.api.types.is_numeric_dtype(
                serie
            ):

                continue

            # ------------------------------------------------
            # No convertir fechas reales
            # ------------------------------------------------

            if pd.api.types.is_datetime64_any_dtype(
                serie
            ):

                continue

            # ------------------------------------------------
            # Intentar conversión numérica
            # ------------------------------------------------
            #
            # errors='coerce' convierte valores no numéricos
            # en NaN.
            #
            # Luego verificamos qué porcentaje de los valores
            # originales pudo convertirse correctamente.
            #
            # ------------------------------------------------

            convertido = pd.to_numeric(
                serie,
                errors="coerce"
            )

            total_validos = serie.notna().sum()

            convertidos_validos = convertido.notna().sum()

            if total_validos > 0:

                porcentaje = (
                    convertidos_validos
                    /
                    total_validos
                )

            else:

                porcentaje = 0

            # ------------------------------------------------
            # Si prácticamente todos los valores son
            # numéricos, convertimos la columna.
            # ------------------------------------------------

            if porcentaje >= 0.95:

                df[columna] = convertido

                print(
                    "[DASHBOARD SERVICE] "
                    f"Columna convertida a numérica: "
                    f"{nombre}"
                )

        return df

    # ========================================================
    # OBTENER MUESTRA
    # ========================================================

    def obtener_muestra(
        self,
        motor,
        database,
        objeto,
        limite=5000,
        columnas=None
    ):

        sql = self._construir_sql_muestra(
            motor=motor,
            database=database,
            objeto=objeto,
            limite=limite,
            columnas=columnas
        )

        # ----------------------------------------------------
        # SEGURIDAD
        # ----------------------------------------------------

        self._validar_sql_solo_lectura(
            sql
        )

        print(
            "[DASHBOARD SERVICE] SQL:"
        )

        print(sql)

        conexion = self._obtener_conexion(
            motor
        )

        try:

            df = pd.read_sql(
                sql,
                conexion
            )

        finally:

            try:

                conexion.close()

            except Exception:

                pass

        return df

    # ========================================================
    # OBTENER DATOS
    # ========================================================
    #
    # Método público utilizado por AgenteDashboard.
    #
    # ========================================================

    def obtener_datos(
        self,
        motor,
        database,
        objeto,
        limite=5000
    ):

        df = self.obtener_muestra(
            motor=motor,
            database=database,
            objeto=objeto,
            limite=limite
        )

        df = self._normalizar_columnas(
            df
        )

        return df

    # ========================================================
    # CONSTRUIR SELECT
    # ========================================================

    def _construir_sql_muestra(
        self,
        motor,
        database,
        objeto,
        limite=5000,
        columnas=None
    ):

        limite = int(
            limite
        )

        if limite <= 0:

            limite = 5000

        # ----------------------------------------------------
        # Validación de identificadores
        # ----------------------------------------------------

        self._validar_identificador(
            database
        )

        self._validar_objeto(
            objeto
        )

        # ----------------------------------------------------
        # Columnas físicas opcionales.
        # Nunca se interpolan nombres no validados.
        # ----------------------------------------------------
        if columnas:
            columnas_limpias = []
            for columna in columnas:
                nombre = str(columna).strip()
                if not re.match(r"^[A-Za-z_][A-Za-z0-9_$#]*$", nombre):
                    raise ValueError(
                        "Nombre de columna inválido: " + nombre
                    )
                columnas_limpias.append(nombre)
            select_columnas = ", ".join(columnas_limpias)
        else:
            select_columnas = "*"

        if motor.upper() == "NETEZZA":

            # ------------------------------------------------
            # Netezza:
            #
            # ESQUEMA..TABLA
            #
            # ------------------------------------------------

            return (
                "SELECT " + select_columnas + " FROM "
                f"{database}..{objeto} "
                f"LIMIT {limite}"
            )

        if motor.upper() == "TERADATA":

            # ------------------------------------------------
            # Teradata:
            #
            # ESQUEMA.TABLA
            #
            # ------------------------------------------------

            return (
                "SELECT TOP "
                f"{limite} {select_columnas} FROM "
                f"{database}.{objeto}"
            )

        raise ValueError(
            "Motor no soportado: "
            + str(motor)
        )

    # ========================================================
    # CONEXIÓN
    # ========================================================

    def _obtener_conexion(
        self,
        motor
    ):

        motor = str(
            motor
        ).upper()

        # ====================================================
        # NETEZZA
        # ====================================================

        if motor == "NETEZZA":

            return self._conexion_netezza()

        # ====================================================
        # TERADATA
        # ====================================================

        if motor == "TERADATA":

            return self._conexion_teradata()

        raise ValueError(
            "Motor no soportado: "
            + motor
        )

    # ========================================================
    # CONEXIÓN NETEZZA
    # ========================================================

    def _conexion_netezza(self):

        print(
            "[DASHBOARD SERVICE] "
            "Solicitando conexión Netezza al "
            "connection_manager..."
        )

        try:

            conexion = conectar_netezza()

            if conexion is None:

                raise RuntimeError(
                    "connection_manager devolvió "
                    "una conexión Netezza vacía."
                )

            print(
                "[DASHBOARD SERVICE] "
                "Conexión Netezza OK"
            )

            return conexion

        except Exception as e:

            print(
                "[DASHBOARD SERVICE] "
                f"Error conectando a Netezza: {str(e)}"
            )

            raise

    # ========================================================
    # CONEXIÓN TERADATA
    # ========================================================

    def _conexion_teradata(
        self
    ):

        try:
        
            conexion = conectar_teradata()
        
            if conexion is None:
        
                raise RuntimeError(
                    "connection_manager devolvió "
                "una conexión Teradata vacía."
                )
        
            print(
                "[DASHBOARD SERVICE] "
                "Conexión Teradata OK"
                )
        
            return conexion
        
        except Exception as e:
        
            print(
                    "[DASHBOARD SERVICE] "
                    f"Error conectando a Teradata: {str(e)}"
            )
        
            raise

    # ========================================================
    # VALIDACIÓN SQL SOLO LECTURA
    # ========================================================

    def _validar_sql_solo_lectura(
        self,
        sql
    ):

        if not sql:

            raise PermissionError(
                "SQL vacío."
            )

        texto = str(
            sql
        ).strip()

        # ----------------------------------------------------
        # Eliminar comentarios
        # ----------------------------------------------------

        texto = re.sub(
            r"/\*.*?\*/",
            " ",
            texto,
            flags=re.DOTALL
        )

        texto = re.sub(
            r"--.*?$",
            " ",
            texto,
            flags=re.MULTILINE
        )

        texto = texto.strip()

        # ----------------------------------------------------
        # Debe comenzar con SELECT
        # ----------------------------------------------------

        if not re.match(
            r"^SELECT\b",
            texto,
            flags=re.IGNORECASE
        ):

            raise PermissionError(
                "SQL BLOQUEADO: "
                "el DashboardService únicamente "
                "permite consultas SELECT."
            )

        # ----------------------------------------------------
        # Operaciones prohibidas
        # ----------------------------------------------------

        operaciones = [

            "INSERT",
            "UPDATE",
            "DELETE",
            "DROP",
            "TRUNCATE",
            "CREATE",
            "ALTER",
            "MERGE",
            "UPSERT",
            "GRANT",
            "REVOKE",
            "RENAME"
        ]

        for operacion in operaciones:

            patron = (
                r"\b"
                + operacion
                + r"\b"
            )

            if re.search(
                patron,
                texto,
                flags=re.IGNORECASE
            ):

                raise PermissionError(
                    "SQL BLOQUEADO: "
                    f"operación '{operacion}' "
                    "no permitida."
                )

        # ----------------------------------------------------
        # Bloquear múltiples sentencias
        # ----------------------------------------------------

        partes = [

            parte.strip()

            for parte in texto.split(";")

            if parte.strip()
        ]

        if len(partes) > 1:

            raise PermissionError(
                "SQL BLOQUEADO: "
                "no se permiten múltiples "
                "sentencias."
            )

        return True

    # ========================================================
    # VALIDAR IDENTIFICADOR
    # ========================================================

    def _validar_identificador(
        self,
        valor
    ):

        valor = str(
            valor or ""
        ).strip()

        if not re.match(
            r"^[A-Za-z0-9_$#]+$",
            valor
        ):

            raise ValueError(
                "Identificador inválido: "
                + valor
            )

    # ========================================================
    # VALIDAR TABLA / VISTA
    # ========================================================

    def _validar_objeto(
        self,
        objeto
    ):

        objeto = str(
            objeto or ""
        ).strip()

        if not re.match(
            r"^[A-Za-z0-9_$#]+$",
            objeto
        ):

            raise ValueError(
                "Nombre de tabla/vista inválido: "
                + objeto
            )

    # ========================================================
    # DETECTAR FECHA
    # ========================================================

    def _es_fecha(
        self,
        nombre,
        serie
    ):

        nombre_upper = str(
            nombre
        ).upper()

        palabras_fecha = [

            "FECHA",
            "DATE",
            "TIMESTAMP",
            "DATETIME",
            "PERIODO",
            "PERÍODO",
            "MES",
            "YEAR",
            "ANIO",
            "AÑO",
            "TRIMESTRE",
            "QUARTER"
        ]

        for palabra in palabras_fecha:

            if palabra in nombre_upper:

                return True

        if pd.api.types.is_datetime64_any_dtype(
            serie
        ):

            return True

        return False

    # ========================================================
    # DETECTAR MÉTRICA
    # ========================================================

    def _es_metrica(
        self,
        nombre,
        serie
    ):

        nombre_upper = str(
            nombre
        ).upper()

        palabras = [

            "TOTAL",
            "MONTO",
            "IMPORTE",
            "CANTIDAD",
            "COUNT",
            "QTY",
            "VOLUMEN",
            "VALOR",
            "SALDO",
            "PRECIO",
            "AMOUNT",
            "NUMBER",
            "NUMERO",
            "NÚMERO",
            "SUM",
            "SUMA",
            "PROMEDIO",
            "PROM",
            "MEDIA",
            "RATIO",
            "PORCENTAJE",
            "PCT"
        ]

        # ----------------------------------------------------
        # Primero revisar nombre.
        #
        # Esto permite reconocer TOTAL aunque haya llegado
        # originalmente como object.
        # ----------------------------------------------------

        for palabra in palabras:

            if palabra in nombre_upper:

                return True

        # ----------------------------------------------------
        # Segundo: revisar tipo.
        # ----------------------------------------------------

        if pd.api.types.is_numeric_dtype(
            serie
        ):

            return True

        # ----------------------------------------------------
        # Tercero: intentar determinar si una columna object
        # representa realmente valores numéricos.
        # ----------------------------------------------------

        if pd.api.types.is_object_dtype(
            serie
        ):

            convertido = pd.to_numeric(
                serie,
                errors="coerce"
            )

            total_validos = serie.notna().sum()

            convertidos_validos = convertido.notna().sum()

            if total_validos > 0:

                porcentaje = (
                    convertidos_validos
                    /
                    total_validos
                )

                if porcentaje >= 0.95:

                    return True

        return False

    # ========================================================
    # DETECTAR DIMENSIÓN
    # ========================================================

    def _es_dimension(
        self,
        nombre,
        serie
    ):

        # ----------------------------------------------------
        # Si es numérica, normalmente no es dimensión.
        # ----------------------------------------------------

        if pd.api.types.is_numeric_dtype(
            serie
        ):

            cardinalidad = serie.nunique(
                dropna=True
            )

            # Numéricas con poca cardinalidad pueden
            # representar categorías.
            if cardinalidad <= 30:

                return True

            return False

        # ----------------------------------------------------
        # Texto / object
        # ----------------------------------------------------

        if pd.api.types.is_object_dtype(
            serie
        ):

            return True

        if pd.api.types.is_string_dtype(
            serie
        ):

            return True

        # ----------------------------------------------------
        # Categóricas
        # ----------------------------------------------------

        if str(
            serie.dtype
        ) == "category":

            return True

        return False

    # ========================================================
    # RESUMEN
    # ========================================================

    def generar_resumen(
        self,
        analisis
    ):

        if not analisis:

            return ""

        lineas = [

            "📊 ANÁLISIS DE FUENTE",

            "",

            f"Motor: "
            f"{analisis.get('motor', '')}",

            f"Base de datos: "
            f"{analisis.get('database', '')}",

            f"Objeto: "
            f"{analisis.get('objeto', '')}",

            "",

            "Dimensiones:"
        ]

        for dimension in analisis.get(
            "dimensiones",
            []
        ):

            lineas.append(
                "• "
                + dimension["nombre"]
            )

        lineas.append(
            ""
        )

        lineas.append(
            "Métricas:"
        )

        for metrica in analisis.get(
            "metricas",
            []
        ):

            lineas.append(
                "• "
                + metrica["nombre"]
            )

        lineas.append(
            ""
        )

        lineas.append(
            "Fechas:"
        )

        for fecha in analisis.get(
            "fechas",
            []
        ):

            lineas.append(
                "• "
                + fecha["nombre"]
            )

        return "\n".join(
            lineas
        )