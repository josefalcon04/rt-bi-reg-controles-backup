import logging
import time
import pandas as pd

from app.servicios.bases.connection_manager import conectar_teradata


def Query_Teradata_LAC(anio=None, departamento=None):
    """
    Consulta la tendencia mensual de teléfonos únicos de Planta LAC.

    - anio=None/TODOS: devuelve todo el histórico.
    - departamento=None/TODOS: devuelve todos los departamentos.
    """
    inicio = time.time()

    logging.info(
        "[LAC][1] Inicio Query_Teradata_LAC | anio=%s | departamento=%s",
        anio,
        departamento
    )

    conn = conectar_teradata()

    if not conn:
        logging.error("[LAC][ERROR] No se pudo conectar a Teradata")
        return []

    try:
        condiciones = []
        parametros = []

        # Filtro por año.
        if anio and str(anio).upper() != "TODOS":
            anio_int = int(anio)
            condiciones.append(
                "PERIODO >= DATE '%04d-01-01' "
                "AND PERIODO < DATE '%04d-01-01'"
                % (anio_int, anio_int + 1)
            )

        # Filtro por departamento.
        if departamento and str(departamento).upper() != "TODOS":
            departamento_limpio = str(departamento).strip().upper()

            if departamento_limpio == "SIN DEPARTAMENTO":
                condiciones.append("DEPARTAMENTO_LAC IS NULL")
            else:
                condiciones.append(
                    "TRIM(DEPARTAMENTO_LAC) = '%s'"
                    % departamento_limpio.replace("'", "''")
                )

        where_sql = ""
        if condiciones:
            where_sql = "\nWHERE " + "\n  AND ".join(condiciones)

        sql = f"""
            SELECT
                PERIODO,
                COALESCE(TRIM(DEPARTAMENTO_LAC), 'SIN DEPARTAMENTO') AS DEPARTAMENTO,
                COUNT(DISTINCT TCNTEL_FORMAT) AS CANTIDAD_TELEFONOS_UNICOS
            FROM PE_PROD_ESL_VIEW.VW_PLANTA_LAC
            {where_sql}
            GROUP BY 1, 2
            ORDER BY 1 ASC, 2
        """

        logging.info(
            "[LAC][2] Ejecutando SQL | anio=%s | departamento=%s",
            anio,
            departamento
        )
        logging.info(
            "[LAC][SQL] %s",
            " ".join(sql.split())
        )

        logging.info("[LAC][4] Ejecutando SQL en Teradata...")
        df = pd.read_sql(sql, conn)

        segundos = round(time.time() - inicio, 2)

        logging.info(
            "[LAC][5] SQL terminado OK | filas=%s | tiempo=%ss",
            len(df),
            segundos
        )

        # Normalizar nombres de columnas porque pandas puede devolver
        # algunos nombres en minúscula según el driver.
        df.columns = [str(col).strip().upper() for col in df.columns]

        return df.to_dict(orient="records")

    except Exception as error:
        logging.exception("[LAC][ERROR] Error ejecutando Query_Teradata_LAC: %s", error)
        return []

    finally:
        try:
            conn.close()
            logging.info("[LAC][6] Conexión Teradata cerrada")
        except Exception:
            pass


def Query_Filtros_Teradata_LAC():
    """
    Obtiene los años y departamentos disponibles para los filtros.
    """
    inicio = time.time()

    logging.info("[LAC][FILTROS][1] Consultando años y departamentos...")

    conn = conectar_teradata()

    if not conn:
        logging.error("[LAC][FILTROS][ERROR] No se pudo conectar a Teradata")
        return {
            "anios": [],
            "departamentos": []
        }

    try:
        sql = """
            SELECT
                EXTRACT(YEAR FROM PERIODO) AS ANIO,
                COALESCE(TRIM(DEPARTAMENTO_LAC), 'SIN DEPARTAMENTO') AS DEPARTAMENTO
            FROM PE_PROD_ESL_VIEW.VW_PLANTA_LAC
            GROUP BY 1, 2
            ORDER BY 1 DESC, 2
        """

        logging.info("[LAC][FILTROS][2] Ejecutando SQL de filtros...")
        df = pd.read_sql(sql, conn)

        df.columns = [str(col).strip().upper() for col in df.columns]

        anios = sorted(
            {
                int(valor)
                for valor in df["ANIO"].dropna().tolist()
            },
            reverse=True
        )

        departamentos = sorted(
            {
                str(valor).strip()
                for valor in df["DEPARTAMENTO"].dropna().tolist()
                if str(valor).strip()
            }
        )

        segundos = round(time.time() - inicio, 2)

        logging.info(
            "[LAC][FILTROS][3] OK | años=%s | departamentos=%s | tiempo=%ss",
            len(anios),
            len(departamentos),
            segundos
        )

        return {
            "anios": anios,
            "departamentos": departamentos
        }

    except Exception as error:
        logging.exception(
            "[LAC][FILTROS][ERROR] Error obteniendo filtros: %s",
            error
        )

        return {
            "anios": [],
            "departamentos": []
        }

    finally:
        try:
            conn.close()
        except Exception:
            pass


def preparar_datos_lac(datos):
    """
    Convierte los datos de Teradata a un DataFrame preparado para Plotly.

    PERIODO viene desde Teradata como DATE, por ejemplo:
    2026-09-01
    """
    columnas = [
        "PERIODO",
        "DEPARTAMENTO",
        "CANTIDAD_TELEFONOS_UNICOS"
    ]

    if not datos:
        return pd.DataFrame(columns=columnas + ["FECHA", "PERIODO_LABEL", "ANIO"])

    df = pd.DataFrame(datos)

    # Normalizar nombres de columnas.
    df.columns = [str(col).strip().upper() for col in df.columns]

    if any(col not in df.columns for col in columnas):
        logging.error(
            "[LAC] Columnas esperadas no encontradas: %s | encontradas: %s",
            columnas,
            list(df.columns)
        )
        return pd.DataFrame(columns=columnas + ["FECHA", "PERIODO_LABEL", "ANIO"])

    # PERIODO es DATE en Teradata.
    df["FECHA"] = pd.to_datetime(
        df["PERIODO"],
        errors="coerce"
    )

    df = df.dropna(subset=["FECHA"]).copy()

    df["DEPARTAMENTO"] = (
        df["DEPARTAMENTO"]
        .fillna("SIN DEPARTAMENTO")
        .astype(str)
        .str.strip()
    )

    df["CANTIDAD_TELEFONOS_UNICOS"] = pd.to_numeric(
        df["CANTIDAD_TELEFONOS_UNICOS"],
        errors="coerce"
    ).fillna(0)

    df["ANIO"] = df["FECHA"].dt.year

    meses = [
        "Ene", "Feb", "Mar", "Abr", "May", "Jun",
        "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"
    ]

    df["PERIODO_LABEL"] = df["FECHA"].apply(
        lambda fecha: f"{meses[fecha.month - 1]}-{fecha.strftime('%y')}"
    )

    df = df.sort_values(
        ["FECHA", "DEPARTAMENTO"]
    ).reset_index(drop=True)

    return df


def dataframe_lac_a_json(df):
    """
    Convierte el DataFrame preparado a JSON para el endpoint Flask.
    """
    if df.empty:
        return []

    resultado = []

    for _, fila in df.iterrows():
        resultado.append({
            "periodo": fila["FECHA"].strftime("%Y-%m-%d"),
            "periodo_label": fila["PERIODO_LABEL"],
            "anio": int(fila["ANIO"]),
            "departamento": str(fila["DEPARTAMENTO"]),
            "cantidad": int(fila["CANTIDAD_TELEFONOS_UNICOS"])
        })

    return resultado
