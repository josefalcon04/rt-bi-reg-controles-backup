from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    Blueprint,
    url_for
)

from app.servicios.bases.connection_manager import conectar_netezza

import re
import pandas as pd
import json

from datetime import datetime, timedelta


# =========================================================
# BLUEPRINT
# =========================================================

monitoreo_norma_bp = Blueprint(
    'monitoreo_norma',
    __name__
)


# =========================================================
# OBTENER REPORTES
# =========================================================

def obtener_reportes():

    conn = conectar_netezza()
    cursor = conn.cursor()

    try:

        # =================================================
        # CONSULTA PRINCIPAL
        # =================================================

        cursor.execute("""
            SELECT
                NOMBRE_REPORTE,
                INDICADOR_COLOR,
                FRECUENCIA,
                NOMBRE_ORIGINAL
            FROM (
                SELECT DISTINCT

                    CASE

                        WHEN A.NOMBRE_PROCESO_REPO =
                            'INEI CUADRO 1 - BLOQUE 1'
                        THEN 'INEI1-B01'

                        WHEN A.NOMBRE_PROCESO_REPO =
                            'INEI CUADRO 1 - BLOQUE 2'
                        THEN 'INEI1-B03'

                        WHEN A.NOMBRE_PROCESO_REPO =
                            'INEI CUADRO 1 - BLOQUE 3'
                        THEN 'INEI1-B03'

                        WHEN A.NOMBRE_PROCESO_REPO =
                            'INEI CUADRO 2'
                        THEN 'INEI2-B00'

                        WHEN A.NOMBRE_PROCESO_REPO =
                            'INFORME TRAFICO (RT)'
                        THEN 'TRAFI-RT1'

                        ELSE A.NOMBRE_PROCESO_REPO

                    END AS nombre_reporte,


                    CASE

                        WHEN A.EJECUCION = 'EXITO'
                        THEN 'green'

                        WHEN A.EJECUCION = 'PENDIENTE'
                        THEN 'yellow'

                        WHEN A.EJECUCION = 'ERROR'
                        THEN 'red'

                        ELSE 'grey'

                    END AS indicador_color,


                    A.FRECUENCIA_REPO AS frecuencia,

                    A.NOMBRE_PROCESO_REPO AS nombre_original,

                    A.PERIODO,


                    MAX(A.PERIODO)
                    OVER (
                        PARTITION BY

                            CASE

                                WHEN A.NOMBRE_PROCESO_REPO =
                                    'INEI CUADRO 1 - BLOQUE 1'
                                THEN 'INEI1-B01'

                                WHEN A.NOMBRE_PROCESO_REPO =
                                    'INEI CUADRO 1 - BLOQUE 2'
                                THEN 'INEI1-B03'

                                WHEN A.NOMBRE_PROCESO_REPO =
                                    'INEI CUADRO 1 - BLOQUE 3'
                                THEN 'INEI1-B03'

                                WHEN A.NOMBRE_PROCESO_REPO =
                                    'INEI CUADRO 2'
                                THEN 'INEI2-B00'

                                WHEN A.NOMBRE_PROCESO_REPO =
                                    'INFORME TRAFICO (RT)'
                                THEN 'TRAFI-RT1'

                                ELSE A.NOMBRE_PROCESO_REPO

                            END,

                            A.FRECUENCIA_REPO
                    ) AS MAX_PERIODO


                FROM CONTROL_MAKO..T_AGR_NORMA_CONTROL A


                LEFT JOIN
                    CONTROL_MAKO..T_CATA_REPORTES_NORMA B

                ON
                    A.NOMBRE_PROCESO_REPO =
                    B.NOMBRE_PROCESO_REPO


                WHERE
                    SUBSTRING(A.PERIODO, 1, 2) = '20'

                    AND B.ESTADO = '1'

            ) AS X


            WHERE
                PERIODO = MAX_PERIODO


            ORDER BY
                FRECUENCIA,
                NOMBRE_REPORTE
        """)


        resultados = cursor.fetchall()


        # =================================================
        # LISTAS POR FRECUENCIA
        # =================================================

        reportes_trimestrales = []

        reportes_mensuales = []

        reportes_semestrales = []

        reportes_anuales = []


        # =================================================
        # AGRUPAR REPORTES
        # =================================================

        for reporte in resultados:

            nombre_reporte = reporte[0]

            indicador_color = reporte[1]

            frecuencia = reporte[2]

            nombre_original = reporte[3]


            reporte_data = {

                'nombre':
                    nombre_reporte,

                'indicador':
                    indicador_color,

                'nombre_original':
                    nombre_original

            }


            if frecuencia == 'TRIMESTRAL':

                reportes_trimestrales.append(
                    reporte_data
                )


            elif frecuencia == 'MENSUAL':

                reportes_mensuales.append(
                    reporte_data
                )


            elif frecuencia == 'SEMESTRAL':

                reportes_semestrales.append(
                    reporte_data
                )


            elif frecuencia == 'ANUAL':

                reportes_anuales.append(
                    reporte_data
                )


        return {

            'reportes_trimestrales':
                reportes_trimestrales,

            'reportes_mensuales':
                reportes_mensuales,

            'reportes_semestrales':
                reportes_semestrales,

            'reportes_anuales':
                reportes_anuales

        }


    finally:

        cursor.close()

        conn.close()


# =========================================================
# PANTALLA PRINCIPAL DE REPORTES
# =========================================================

@monitoreo_norma_bp.route('/reportes')
def monitoreo_reporte():

    """
    Renderiza la pantalla principal
    de monitoreo de reportes.
    """

    reportes = obtener_reportes()


    return render_template(
        'monitoreo_norma.html',
        **reportes
    )


# =========================================================
# DETALLE DEL REPORTE
# =========================================================

@monitoreo_norma_bp.route('/detalle')
def detalle_reporte():

    nombre_reporte = request.args.get(
        "nombre"
    )


    # =====================================================
    # VALIDAR REPORTE
    # =====================================================

    if not nombre_reporte:

        return (
            "Reporte no encontrado",
            404
        )


    # =====================================================
    # MODO PANEL
    # =====================================================

    modo_panel = (
        request.args.get("modo") == "panel"
        or
        request.args.get("panel") == "1"
    )


    conn = conectar_netezza()
    cursor = conn.cursor()


    try:

        # =================================================
        # INFORMACIÓN DEL REPORTE
        # =================================================

        query_info = """

            SELECT DISTINCT

                NOMBRE_PROCESO_REPO
                    AS nombre_reporte,

                UPPER(
                    FRECUENCIA_REPO
                )
                    AS frecuencia,

                DIA_EJECUCION_REPO
                    AS proxima_ejecucion,

                TO_CHAR(
                    FECHA_EJECUCION,
                    'YYYY-MM-DD'
                )
                    AS maxima_ejecucion,

                EJECUCION
                    AS estado,

                EJECUCION_INPUT,

                PERIODO


            FROM
                CONTROL_MAKO..T_AGR_NORMA_CONTROL


            WHERE
                NOMBRE_PROCESO_REPO = ?


            AND PERIODO = (

                SELECT
                    MAX(PERIODO)

                FROM
                    CONTROL_MAKO..T_AGR_NORMA_CONTROL

                WHERE
                    NOMBRE_PROCESO_REPO = ?

            )

        """


        cursor.execute(
            query_info,
            (
                nombre_reporte,
                nombre_reporte
            )
        )


        row = cursor.fetchone()


        if not row:

            return (
                "Reporte no encontrado",
                404
            )


        reporte_periodo = row[6]


        reporte = {

            "nombre":
                row[0],

            "frecuencia":
                row[1],

            "proxima_ejecucion":
                row[2],

            "estado":
                row[4],

            "maxima_ejecucion":
                row[3],

            "estado_input":
                row[5],

            "periodo":
                row[6]

        }


        # =================================================
        # OBTENER CONFIGURACIÓN DEL REPORTE
        # =================================================

        query_tabla = """

            SELECT DISTINCT

                'SELECT '
                || CAMPO_TENDENCIA1
                || ' Categoría FROM '
                || TABLA_HISTORICA
                || ' GROUP BY '
                || AGRUPA_TENDENCIA1,


                'SELECT '
                || CAMPO_TENDENCIA2
                || ' Categoría FROM '
                || TABLA_HISTORICA
                || ' GROUP BY '
                || AGRUPA_TENDENCIA2,


                CASE

                    WHEN NVL(
                        ALCANCE_FUNCIONAL,
                        ''
                    ) = ''

                    THEN
                        'Pendiente Detalle'

                    ELSE
                        ALCANCE_FUNCIONAL

                END
                    AS ALCANCE_FUNCIONAL,


                CASE

                    WHEN NVL(
                        ALCANCE_TECNICO,
                        ''
                    ) = ''

                    THEN
                        'Pendiente Detalle'

                    ELSE
                        ALCANCE_TECNICO

                END
                    AS ALCANCE_TECNICO,


                LOG_NOMBRE_SP,

                RELACION,

                TABLA_HISTORICA


            FROM
                CONTROL_MAKO..T_CATA_REPORTES_NORMA


            WHERE
                NOMBRE_PROCESO_REPO = ?

        """


        cursor.execute(
            query_tabla,
            (
                nombre_reporte,
            )
        )


        row = cursor.fetchone()


        if not row:

            return (
                "Tabla histórica no encontrada",
                404
            )


        if not row[0] or not row[1]:

            return (
                "Tabla histórica no encontrada",
                404
            )


        nombre_tabla = row[0]

        nombre_tabla2 = row[1]


        reporte["funcional"] = row[2]

        reporte["tecnico"] = row[3]


        nombre_log = row[4]

        nombre_input = row[5]

        tabla_historica = row[6]


        # =================================================
        # VALIDACIÓN DE TABLAS
        # =================================================

        if (
            ";" in nombre_tabla
            or "--" in nombre_tabla
        ):

            return (
                "Nombre de tabla inválido",
                400
            )


        # =================================================
        # GRÁFICO 1
        # =================================================

        query_datos = (
            f"{nombre_tabla}"
        )


        cursor.execute(
            query_datos
        )


        data = cursor.fetchall()


        # =================================================
        # PROCESAR DATOS PARA GRÁFICOS
        # =================================================

        def procesar_datos_grafico(
            cursor,
            query,
            meses_texto
        ):

            cursor.execute(
                query
            )


            data = cursor.fetchall()


            columnas = [

                'Mes',

                'Categoría',

                'Cantidad'

            ]


            datos_normalizados = [

                dict(
                    zip(
                        columnas,

                        fila
                        if len(fila) == 3

                        else [
                            fila[0],
                            '',
                            fila[1]
                        ]
                    )
                )

                for fila in data

            ]


            df = pd.DataFrame(
                datos_normalizados
            )


            df['Mes_dt'] = pd.to_datetime(
                df['Mes'],
                format="%Y%m",
                errors='coerce'
            )


            df = df.dropna(
                subset=[
                    'Cantidad',
                    'Mes_dt'
                ]
            )


            hoy = datetime.today()


            un_anio_atras = (
                hoy -
                timedelta(days=365)
            )


            df = df[
                df['Mes_dt']
                >= un_anio_atras
            ]


            df['Mes_num'] = (
                df['Mes_dt']
                .dt.month
            )


            df['Mes_nombre'] = (
                df['Mes_num']
                .apply(
                    lambda x:
                    meses_texto[x - 1]
                )
            )


            df['Año'] = (
                df['Mes_dt']
                .dt.year
            )


            df = df.sort_values(
                'Mes_dt'
            )


            if df.empty:

                return (
                    "<p>"
                    "No hay datos para graficar."
                    "</p>"
                )


            columnas_json = [

                'Mes_num',

                'Mes_nombre',

                'Cantidad',

                'Año'

            ]


            if (
                'Categoría' in df.columns
                and
                not df['Categoría']
                .isna()
                .all()
            ):

                columnas_json.append(
                    'Categoría'
                )


            data_json = (
                df[columnas_json]
                .to_dict(
                    orient='records'
                )
            )


            return json.dumps(
                data_json
            )


        # =================================================
        # MESES
        # =================================================

        meses_texto = [

            'Ene',
            'Feb',
            'Mar',
            'Abr',
            'May',
            'Jun',
            'Jul',
            'Ago',
            'Sep',
            'Oct',
            'Nov',
            'Dic'

        ]


        data_actual_json = (
            procesar_datos_grafico(
                cursor,
                nombre_tabla,
                meses_texto
            )
        )


        data_tabla2_json = (
            procesar_datos_grafico(
                cursor,
                nombre_tabla2,
                meses_texto
            )
        )


        # =================================================
        # CERRAR PRIMERA CONEXIÓN
        # =================================================

        conn.close()

        conn = None

        cursor = None


        # =================================================
        # TABLA DE ÚLTIMAS EJECUCIONES
        # =================================================

        conn = conectar_netezza()

        cursor = conn.cursor()


        query_metricas = """

            SELECT *

            FROM (

                SELECT

                    LOG_NOMBRE_SP,

                    LOG_PARAMETRO_SP
                        AS PERIODO,

                    TO_CHAR(
                        LOG_FECHA_INICIO,
                        'YYYY-MM-DD HH24:MI:SS'
                    )
                        AS LOG_FECHA_INICIO,

                    TO_CHAR(
                        LOG_FECHA_FIN,
                        'YYYY-MM-DD HH24:MI:SS'
                    )
                        AS LOG_FECHA_FIN,

                    LOG_ESTADO,

                    ROW_NUMBER()
                    OVER (
                        PARTITION BY 1
                        ORDER BY
                            LOG_FECHA_INICIO DESC
                    )
                        AS row_num2


                FROM (

                    SELECT

                        L.*,

                        ROW_NUMBER()
                        OVER (

                            PARTITION BY
                                L.LOG_NOMBRE_SP,
                                LOG_PARAMETRO_SP

                            ORDER BY
                                L.LOG_FECHA_INICIO DESC

                        )
                            AS row_num


                    FROM
                        PROD_REGU_NORMA_DATA..T_NRM_LOG L


                    WHERE
                        LOG_NOMBRE_SP = ?

                ) AS X


                WHERE
                    row_num = 1

            ) AS Y


            WHERE
                row_num2 <= 5


            ORDER BY
                PERIODO DESC

        """


        cursor.execute(
            query_metricas,
            (
                nombre_log,
            )
        )


        metricas = cursor.fetchall()


        metricas_relevantes = [

            {

                "nombre_sp":
                    row[0],

                "periodo":
                    row[1],

                "fecha_inicio":
                    row[2],

                "fecha_fin":
                    row[3],

                "estado":
                    row[4]

            }

            for row in metricas

        ]


        # =================================================
        # PROCESO DEL REPORTE
        # =================================================

        conn.close()

        conn = None

        cursor = None


        conn = conectar_netezza()

        cursor = conn.cursor()


        query_proceso = """

            SELECT

                A.SECUENCIA_INPUT,

                B.PERIODO,

                A.SCHEMA_INPUT,

                A.NOMBRE_INPUT,

                A.FRECUENCIA_INPUT,

                A.DIA_EJECUCION_INPUT,

                TO_CHAR(
                    FECHA_EJECUCION,
                    'YYYY-MM-DD HH24:MI:SS'
                ),

                B.ESTADO


            FROM
                CONTROL_MAKO..T_CATA_INPUTS_NORMA A


            LEFT JOIN
                CONTROL_MAKO..T_AGR_INPUT_CONTROL B


            ON
                A.NOMBRE_INPUT =
                B.NOMBRE_INPUT


            WHERE
                '|' || ? || '|'
                LIKE
                '%|' || SECUENCIA_INPUT || '|%'


            AND B.PERIODO =
                CAST(
                    '?' || '01'
                    AS INT
                )

        """


        cursor.execute(
            query_proceso,
            (
                nombre_input,
                reporte_periodo
            )
        )


        metricas = cursor.fetchall()


        # =================================================
        # MERMAID
        # =================================================

        proceso_mermaid = (
            "graph LR;\n"
        )


        proceso_mermaid += (
            "subgraph Inputs\n"
        )


        for row in metricas:

            input_id = row[0]

            input_name = row[3]


            proceso_mermaid += (
                f'input_{input_id}'
                f'[" {input_name}"]\n'
            )


        proceso_mermaid += (
            "end\n"
        )


        proceso_mermaid += (
            "subgraph Proceso\n"
        )


        proceso_mermaid += (
            f'proc_{nombre_log}'
            f'["{nombre_log}"]\n'
        )


        proceso_mermaid += (
            "end\n"
        )


        proceso_mermaid += (
            "subgraph Output\n"
        )


        proceso_mermaid += (
            f'tabla_{tabla_historica}'
            f'[" {tabla_historica}"]\n'
        )


        proceso_mermaid += (
            "end\n"
        )


        for row in metricas:

            input_id = row[0]


            proceso_mermaid += (
                f'input_{input_id}'
                f' --> '
                f'proc_{nombre_log}\n'
            )


        proceso_mermaid += (
            f'proc_{nombre_log}'
            f' --> '
            f'tabla_{tabla_historica}\n'
        )


        # =================================================
        # DATOS DE INPUT
        # =================================================

        metricas_input = [

            {

                "periodo":
                    reporte_periodo,

                "Schema":
                    row[2].lower(),

                "Input":
                    row[3].lower(),

                "Frecuencia":
                    row[4].lower(),

                "fecha":
                    row[5],

                "fecha_ejecucion":
                    row[6],

                "Estado":
                    row[7]

            }

            for row in metricas

        ]


        print(
            proceso_mermaid
        )


        # =================================================
        # RESPUESTA
        # =================================================

        if modo_panel:

            """
            ==================================================
            MODO PANEL
            ==================================================

            Esta respuesta será utilizada posteriormente
            por monitoreo_norma.html mediante fetch().

            IMPORTANTE:
            Vamos a crear la plantilla
            detalle_reporte_panel.html en el siguiente paso.
            """

            return render_template(

                "detalle_reporte_panel.html",

                reporte=reporte,

                data_actual=data_actual_json,

                data_tabla2=data_tabla2_json,

                metricas_relevantes=
                    metricas_relevantes,

                proceso_mermaid=
                    proceso_mermaid,

                metricas_input=
                    metricas_input

            )


        # =================================================
        # MODO NORMAL
        # =================================================

        return render_template(

            "detalle_reporte.html",

            reporte=reporte,

            data_actual=
                data_actual_json,

            data_tabla2=
                data_tabla2_json,

            metricas_relevantes=
                metricas_relevantes,

            proceso_mermaid=
                proceso_mermaid,

            metricas_input=
                metricas_input

        )


    except Exception as e:

        print(
            "=========================================="
        )

        print(
            "[ERROR DETALLE REPORTE]"
        )

        print(
            str(e)
        )

        print(
            "=========================================="
        )


        return (
            f"Error al obtener el detalle: {str(e)}",
            500
        )


    finally:

        if cursor:

            cursor.close()


        if conn:

            conn.close()


# =========================================================
# ACTUALIZAR DATOS
# =========================================================

@monitoreo_norma_bp.route(
    '/actualizar_datos'
)
def actualizar_datos():

    """
    Devuelve los reportes actualizados
    en formato JSON.
    """

    reportes = obtener_reportes()


    return jsonify(
        reportes
    )