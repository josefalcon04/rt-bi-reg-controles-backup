# app/servicios/regulatorio_service.py

from app.servicios.netezza_service import ejecutar_query
import re



class RegulatorioService:


    def consultar_logs_norma(self, pregunta):


        p = pregunta.upper()


        match = re.search(
            r'(NRI[A-Z]*[_ ]?\d+)',
            p
        )


        if not match:

            return {
                "estado": "ERROR",
                "mensaje":
                "Indica el reporte (ej. NRIPO_035)"
            }



        reporte = (
            match.group(1)
            .replace(" ", "_")
        )


        reporte = re.sub(
            r"[^A-Z0-9_]",
            "",
            reporte
        )


        sp = f"SP_NRM_{reporte}"



        sql = f"""

        SELECT
            A.LOG_NOMBRE_SP,
            A.LOG_FECHA_INICIO,
            A.LOG_FECHA_FIN,
            A.LOG_ESTADO,
            B.LOG_NRO_PASO,
            B.LOG_DETAIL

        FROM PROD_REGU_NORMA_DATA..T_NRM_LOG A

        LEFT JOIN PROD_REGU_NORMA_DATA..T_NRM_LOG_DETAIL B

        ON A.LOG_NRO_EJECUCION =
           B.LOG_NRO_EJECUCION

        WHERE A.LOG_NOMBRE_SP = '{sp}'

        AND A.LOG_FECHA_INICIO =
        (
            SELECT MAX(LOG_FECHA_INICIO)
            FROM PROD_REGU_NORMA_DATA..T_NRM_LOG
            WHERE LOG_NOMBRE_SP = '{sp}'
        )

        ORDER BY B.LOG_NRO_PASO

        """



        try:

            datos = ejecutar_query(sql)


            if not datos:

                return {
                    "estado": "OK",
                    "mensaje":
                    f"No encontré logs para {reporte}"
                }



            cab = datos[0]


            return {

                "reporte": reporte,

                "estado": cab.get(
                    "LOG_ESTADO"
                ),

                "inicio": cab.get(
                    "LOG_FECHA_INICIO"
                ),

                "detalle": datos

            }



        except Exception as e:


            return {

                "estado": "ERROR",

                "mensaje": str(e)

            }




    def consultar_alertas_norma(self, pregunta):

        return {
            "estado": "PENDIENTE",
            "mensaje":
            "Lógica de alertas en desarrollo."
        }