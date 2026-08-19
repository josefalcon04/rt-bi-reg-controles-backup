# ============================================================
# AGENTE DASHBOARD
# ============================================================
#
# RESPONSABILIDAD
# ------------------------------------------------------------
# 1. Detectar motor, esquema y objeto.
# 2. Detectar si el usuario indicó columnas explícitamente.
# 3. Detectar agregación solicitada.
# 4. Analizar la fuente REAL mediante DashboardService.
# 5. Validar columnas contra metadata REAL.
# 6. Si no hay columnas:
#       -> dejar que Planner analice la fuente completa.
# 7. Si hay columnas:
#       -> restringir estrictamente a esas columnas.
# 8. Generar plan mediante DashboardPlanner.
# 9. Construir dashboard mediante DashboardBuilder.
#
# REGLAS IMPORTANTES
# ------------------------------------------------------------
# - NO existen columnas hardcodeadas.
# - NO se crean columnas virtuales.
# - NO se aceptan aliases como columnas físicas.
# - NO se inventan columnas.
# - Si una columna solicitada no existe -> ERROR.
# - Si no se indican columnas -> análisis automático.
#
# Motores:
#   NETEZZA  -> ESQUEMA..TABLA
#   TERADATA -> ESQUEMA.TABLA
#
# ============================================================

import re
import time


from app.servicios.dashboard_service import DashboardService
from app.servicios.dashboard_planner import DashboardPlanner
from app.servicios.dashboard_builder import DashboardBuilder


class AgenteDashboard:
        # ========================================================
    # INTERFAZ ESTÁNDAR DEL ROUTER
    # ========================================================

    def execute(
        self,
        pregunta=None,
        memoria=None,
        consulta=None
    ):
        """
        Punto de entrada estándar utilizado por Router.
        
        AgenteDashboard mantiene su lógica interna en
        procesar(), por lo que execute() funciona como
        adaptador para mantener compatibilidad con todos
        los agentes del sistema.
        """

        # El Router normalmente enviará pregunta=
        texto = pregunta

        # Compatibilidad si algún flujo utiliza consulta=
        if texto is None:
            texto = consulta

        if texto is None:
            texto = ""

        return self.procesar(
            texto
        )
    
    # ========================================================
    # INIT
    # ========================================================

    def __init__(self):

        self.nombre = "dashboard"

        self.dashboard_service = DashboardService()

        self.dashboard_planner = DashboardPlanner()

        self.dashboard_builder = DashboardBuilder()

        # --------------------------------------------------------
        # CONTEXTO DE CONVERSACION PENDIENTE
        # --------------------------------------------------------
        # Cuando el usuario solicita un dashboard sin indicar una
        # opcion, el agente genera propuestas y espera una segunda
        # interaccion: 1, 2 o 3.
        #
        # Este contexto evita interpretar "2" como una nueva
        # consulta y permite continuar el flujo iniciado por el
        # usuario. En una integracion multiusuario este contexto
        # debe vivir en la sesion/conversacion, no como estado global.
        self._contexto_pendiente = None

        print(
            "[AGENTE DASHBOARD] Inicializado correctamente"
        )

    # ========================================================
    # PROCESAR
    # ========================================================

    def procesar(
        self,
        consulta,
        opcion=None
    ):

        inicio = time.time()

        print("\n" + "=" * 70)
        print("[AGENTE DASHBOARD] PROCESANDO CONSULTA")
        print("=" * 70)

        print(
            "[AGENTE DASHBOARD] Consulta:",
            consulta
        )

        # ----------------------------------------------------
        # 0. CONTINUAR PROPUESTA PENDIENTE
        # ----------------------------------------------------
        # Si la ultima respuesta del agente fue "opciones" y el
        # siguiente mensaje del usuario es simplemente 1, 2 o 3,
        # ese numero corresponde a la propuesta anterior.
        #
        # Importante: no intentamos detectar esquema/tabla en "2".
        # Restauramos la consulta original y continuamos el flujo.
        # ----------------------------------------------------
        if opcion is None and self._contexto_pendiente:

            texto_opcion = str(consulta or "").strip()

            if re.fullmatch(r"[1-3]", texto_opcion):
                opcion = int(texto_opcion)

                contexto = self._contexto_pendiente

                print(
                    "[AGENTE DASHBOARD] Opcion recibida desde la "
                    "segunda interaccion:",
                    opcion
                )

                print(
                    "[AGENTE DASHBOARD] Continuando plan pendiente "
                    "para:",
                    contexto.get("referencia")
                )

                # Restauramos la consulta original para que el resto
                # del metodo trabaje con la fuente real.
                consulta = contexto.get(
                    "consulta",
                    consulta
                )

                # El plan pendiente se limpia al intentar continuar.
                # Si la opcion no existe, el metodo devolvera el error
                # correspondiente sin dejar un contexto obsoleto.
                self._contexto_pendiente = None

        # ----------------------------------------------------
        # 1. DETECTAR FUENTE
        # ----------------------------------------------------

        fuente = self._detectar_fuente(
            consulta
        )

        if not fuente:

            return self._error(
                inicio,
                "No pude identificar correctamente "
                "el esquema y la tabla o vista.\n\n"
                "Formatos soportados:\n"
                "- Teradata: `ESQUEMA.TABLA`\n"
                "- Netezza: `ESQUEMA..TABLA`"
            )

        motor = fuente["motor"]
        esquema = fuente["esquema"]
        objeto = fuente["objeto"]

        referencia = self._construir_referencia(
            motor,
            esquema,
            objeto
        )

        print(
            "[AGENTE DASHBOARD] Fuente detectada:",
            fuente
        )

        print(
            "[AGENTE DASHBOARD] Referencia:",
            referencia
        )

        # ----------------------------------------------------
        # 2. DETECTAR COLUMNAS EXPLICITAS
        # ----------------------------------------------------

        columnas_solicitadas = (
            self._detectar_columnas_solicitadas(
                consulta
            )
        )

        if columnas_solicitadas:

            print(
                "[AGENTE DASHBOARD] "
                "Columnas indicadas por usuario:",
                columnas_solicitadas
            )

        else:

            print(
                "[AGENTE DASHBOARD] "
                "No se indicaron columnas explícitas."
            )

            print(
                "[AGENTE DASHBOARD] "
                "Se realizará análisis automático."
            )

        # ----------------------------------------------------
        # 3. DETECTAR AGREGACION
        # ----------------------------------------------------

        agregacion = (
            self._detectar_agregacion(
                consulta
            )
        )

        if agregacion:

            print(
                "[AGENTE DASHBOARD] "
                "Agregación detectada:",
                agregacion
            )

        # ----------------------------------------------------
        # 4. ANALIZAR FUENTE REAL
        # ----------------------------------------------------

        try:

            analisis = (
                self.dashboard_service.analizar_fuente(
                    motor=motor,
                    database=esquema,
                    objeto=objeto
                )
            )

        except Exception as e:

            print(
                "[AGENTE DASHBOARD] "
                "Error analizando fuente:",
                str(e)
            )

            return self._error(
                inicio,
                "No pude analizar la fuente.\n\n"
                f"Detalle: {str(e)}",
                fuente=fuente,
                referencia=referencia
            )

        if not analisis:

            return self._error(
                inicio,
                "La fuente no devolvió metadata.",
                fuente=fuente,
                referencia=referencia
            )

        print(
            "[AGENTE DASHBOARD] "
            "Fuente analizada correctamente"
        )

        # ----------------------------------------------------
        # 5. OBTENER COLUMNAS REALES
        # ----------------------------------------------------

        columnas_reales = (
            self._obtener_nombres_columnas_reales(
                analisis
            )
        )

        print(
            "[AGENTE DASHBOARD] "
            "Columnas físicas detectadas:",
            columnas_reales
        )

        # ----------------------------------------------------
        # 6. VALIDAR COLUMNAS EXPLICITAS
        # ----------------------------------------------------
        #
        # Si el usuario indicó columnas:
        #
        #     TODAS deben existir físicamente.
        #
        # No se permite:
        #
        #     alias
        #     columnas virtuales
        #     constantes
        #     nombres inventados
        #
        # ----------------------------------------------------

        if columnas_solicitadas:

            validacion = (
                self._validar_columnas_solicitadas(
                    columnas_solicitadas,
                    columnas_reales
                )
            )

            if not validacion["ok"]:

                faltantes = validacion["faltantes"]

                print(
                    "[AGENTE DASHBOARD] "
                    "Columnas inexistentes:",
                    faltantes
                )

                return self._error(
                    inicio,
                    self._mensaje_columnas_inexistentes(
                        faltantes=faltantes,
                        fuente=fuente,
                        columnas_reales=columnas_reales
                    ),
                    fuente=fuente,
                    referencia=referencia,
                    analisis=analisis
                )

            # ------------------------------------------------
            # NORMALIZAR NOMBRES A LOS NOMBRES FISICOS
            # ------------------------------------------------

            columnas_solicitadas = (
                self._normalizar_nombres_reales(
                    columnas_solicitadas,
                    columnas_reales
                )
            )

            print(
                "[AGENTE DASHBOARD] "
                "Columnas validadas:",
                columnas_solicitadas
            )

            # ------------------------------------------------
            # RESTRINGIR ANALISIS
            # ------------------------------------------------

            analisis = (
                self._restringir_analisis(
                    analisis=analisis,
                    columnas_solicitadas=columnas_solicitadas,
                    agregacion=agregacion
                )
            )

            print(
                "[AGENTE DASHBOARD] "
                "Análisis restringido:"
            )

            print(
                "[AGENTE DASHBOARD] Dimensiones:",
                len(
                    analisis.get(
                        "dimensiones",
                        []
                    )
                )
            )

            print(
                "[AGENTE DASHBOARD] Métricas:",
                len(
                    analisis.get(
                        "metricas",
                        []
                    )
                )
            )

            print(
                "[AGENTE DASHBOARD] Fechas:",
                len(
                    analisis.get(
                        "fechas",
                        []
                    )
                )
            )

        else:

            # ------------------------------------------------
            # NO HAY COLUMNAS:
            #
            # NO RESTRINGIR EL ANALISIS.
            #
            # Planner recibe toda la metadata real.
            # ------------------------------------------------

            analisis = dict(
                analisis
            )

            if agregacion:

                analisis["agregacion"] = (
                    agregacion
                )

            print(
                "[AGENTE DASHBOARD] "
                "Planner recibirá metadata completa."
            )

        # ----------------------------------------------------
        # 7. GENERAR PLAN
        # ----------------------------------------------------

        try:

            plan = (
                self.dashboard_planner.generar_plan(
                    analisis
                )
            )

        except Exception as e:

            print(
                "[AGENTE DASHBOARD] "
                "Error generando plan:",
                str(e)
            )

            return self._error(
                inicio,
                "La fuente fue analizada correctamente, "
                "pero no pude generar el plan.\n\n"
                f"Detalle: {str(e)}",
                fuente=fuente,
                referencia=referencia,
                analisis=analisis
            )

        if not plan:

            return self._error(
                inicio,
                "El Planner no generó un plan válido.",
                fuente=fuente,
                referencia=referencia,
                analisis=analisis
            )

        print(
            "[AGENTE DASHBOARD] "
            "Plan generado correctamente"
        )

        # ----------------------------------------------------
        # 8. SI NO SE INDICA OPCION
        # ----------------------------------------------------
        #
        # Devuelve propuesta.
        #
        # Esto permite:
        #
        # "Hazme un dashboard de TABLA"
        #
        # -> analiza
        # -> propone
        #
        # ----------------------------------------------------

        if opcion is None:

            respuesta = (
                self._formatear_opciones(
                    fuente=fuente,
                    analisis=analisis,
                    plan=plan,
                    columnas_solicitadas=columnas_solicitadas
                )
            )

            # ------------------------------------------------
            # GUARDAR CONTEXTO PARA LA SIGUIENTE INTERACCION
            # ------------------------------------------------
            # Ejemplo:
            #   Usuario -> "Hazme un dashboard de TABLA"
            #   Agente  -> propone 1, 2 y 3
            #   Usuario -> "2"
            #
            # La segunda llamada a procesar() podra reconocer que
            # "2" pertenece a esta propuesta.
            self._contexto_pendiente = {
                "consulta": consulta,
                "motor": motor,
                "esquema": esquema,
                "objeto": objeto,
                "referencia": referencia,
                "fuente": fuente,
                "analisis": analisis,
                "plan": plan
            }

            print(
                "[AGENTE DASHBOARD] Contexto de propuesta guardado."
            )

            return {
                "estado": "opciones",
                "agente": self.nombre,
                "motor": motor,
                "esquema": esquema,
                "objeto": objeto,
                "referencia": referencia,
                "fuente": fuente,
                "analisis": analisis,
                "plan": plan,
                "respuesta": respuesta,
                "tiempo": round(
                    time.time() - inicio,
                    2
                )
            }

        # ----------------------------------------------------
        # 9. VALIDAR OPCION
        # ----------------------------------------------------

        try:

            opcion = int(
                opcion
            )

        except Exception:

            return self._error(
                inicio,
                "La opción del dashboard "
                "debe ser un número válido.",
                fuente=fuente,
                referencia=referencia,
                plan=plan
            )

        opciones = plan.get(
            "opciones",
            []
        )

        opcion_plan = None

        for item in opciones:

            try:

                item_id = int(
                    item.get(
                        "id",
                        0
                    )
                )

            except Exception:

                continue

            if item_id == opcion:

                opcion_plan = item

                break

        if opcion_plan is None:

            disponibles = [
                x.get("id")
                for x in opciones
            ]

            return self._error(
                inicio,
                "La opción seleccionada no existe.\n\n"
                "Opciones disponibles: "
                + ", ".join(
                    str(x)
                    for x in disponibles
                ),
                fuente=fuente,
                referencia=referencia,
                plan=plan
            )

        print(
            "[AGENTE DASHBOARD] "
            "Opción seleccionada:",
            opcion
        )

        print(
            "[AGENTE DASHBOARD] "
            "Continuando con construcción de opción:",
            opcion_plan.get("nombre", "Sin nombre")
        )

        # ----------------------------------------------------
        # 10. OBTENER DATOS
        # ----------------------------------------------------

        try:

            df = (
                self.dashboard_service.obtener_muestra(
                    motor=motor,
                    database=esquema,
                    objeto=objeto,
                    limite=5000
                )
            )

        except Exception as e:

            print(
                "[AGENTE DASHBOARD] "
                "Error obteniendo datos:",
                str(e)
            )

            return self._error(
                inicio,
                "No pude obtener los datos "
                "para construir el dashboard.\n\n"
                f"Detalle: {str(e)}",
                fuente=fuente,
                referencia=referencia,
                plan=plan
            )

        print(
            "[AGENTE DASHBOARD] Datos obtenidos:",
            len(df),
            "filas"
        )

        # ----------------------------------------------------
        # 11. VALIDACION FINAL DEL DATAFRAME
        # ----------------------------------------------------
        #
        # Si el usuario indicó columnas:
        #
        # SOLO esas columnas.
        #
        # Si NO indicó columnas:
        #
        # Se usan las columnas definidas por el Planner.
        #
        # ----------------------------------------------------

        if columnas_solicitadas:

            df = self._restringir_dataframe(
                df=df,
                columnas_solicitadas=columnas_solicitadas
            )

            print(
                "[AGENTE DASHBOARD] "
                "DataFrame restringido:"
            )

            print(
                "[AGENTE DASHBOARD] Columnas:",
                list(df.columns)
            )

        else:

            # ----------------------------------------------
            # SIN COLUMNAS EXPLICITAS
            #
            # El Planner define qué campos utilizar.
            # ----------------------------------------------

            columnas_plan = (
                self._obtener_columnas_plan(
                    plan
                )
            )

            if columnas_plan:

                df = self._restringir_dataframe(
                    df=df,
                    columnas_solicitadas=columnas_plan
                )

                print(
                    "[AGENTE DASHBOARD] "
                    "DataFrame definido por Planner:"
                )

                print(
                    "[AGENTE DASHBOARD] Columnas:",
                    list(df.columns)
                )

            else:

                print(
                    "[AGENTE DASHBOARD] "
                    "Planner no restringió columnas; "
                    "se conserva metadata completa."
                )

        # ----------------------------------------------------
        # 12. VALIDACION DE SEGURIDAD
        # ----------------------------------------------------

        if columnas_solicitadas:

            columnas_finales = {
                str(x).upper()
                for x in df.columns
            }

            columnas_autorizadas = {
                str(x).upper()
                for x in columnas_solicitadas
            }

            extras = (
                columnas_finales
                - columnas_autorizadas
            )

            if extras:

                print(
                    "[AGENTE DASHBOARD] "
                    "ERROR: columnas no autorizadas:",
                    extras
                )

                return self._error(
                    inicio,
                    "El DataFrame contiene columnas "
                    "que no fueron solicitadas por el usuario.",
                    fuente=fuente,
                    referencia=referencia,
                    plan=plan
                )

        # ----------------------------------------------------
        # 13. CONSTRUIR DASHBOARD
        # ----------------------------------------------------

        try:

            titulo = (
                "Dashboard - "
                + objeto
            )

            resultado = (
                self.dashboard_builder.construir(
                    df=df,
                    plan=plan,
                    titulo=titulo,
                    esquema=esquema,
                    objeto=objeto,
                    motor=motor
                )
            )

        except Exception as e:

            print(
                "[AGENTE DASHBOARD] "
                "Error construyendo dashboard:",
                str(e)
            )

            return self._error(
                inicio,
                "Los datos fueron obtenidos, "
                "pero no pude construir el dashboard.\n\n"
                f"Detalle: {str(e)}",
                fuente=fuente,
                referencia=referencia,
                plan=plan
            )

        print(
            "[AGENTE DASHBOARD] "
            "Dashboard construido correctamente"
        )

        # ----------------------------------------------------
        # 14. URL
        # ----------------------------------------------------

        url = resultado.get(
            "url"
        )

        if not url:

            nombre_archivo = resultado.get(
                "nombre_archivo"
            )

            if nombre_archivo:

                url = (
                    "/static/dashboards/"
                    + nombre_archivo
                )

        print(
            "[AGENTE DASHBOARD] URL:",
            url
        )

        # ----------------------------------------------------
        # 15. RESPUESTA
        # ----------------------------------------------------

        respuesta = (
            self._formatear_resultado(
                fuente=fuente,
                opcion=opcion_plan,
                resultado=resultado,
                url=url
            )
        )

        return {
            "estado": "ok",
            "agente": self.nombre,
            "motor": motor,
            "esquema": esquema,
            "objeto": objeto,
            "referencia": referencia,
            "opcion": opcion,
            "analisis": analisis,
            "plan": plan,
            "resultado": resultado,
            "url": url,
            "respuesta": respuesta,
            "tiempo": round(
                time.time() - inicio,
                2
            )
        }

    # ========================================================
    # DETECTAR COLUMNAS SOLICITADAS
    # ========================================================

    def _detectar_columnas_solicitadas(
        self,
        consulta
    ):

        texto = str(
            consulta or ""
        ).strip()

        if not texto:

            return []

        candidatos = []

        # ----------------------------------------------------
        # CASO:
        #
        # información de A, B y C
        # datos de A, B y C
        # columnas A, B y C
        # campos A, B y C
        # ----------------------------------------------------

        patrones = [

            r"(?:información|informacion|datos|"
            r"campos|columnas)"
            r"\s+(?:de|sobre|con)?\s*"
            r"([A-Za-z_][A-Za-z0-9_$#]*"
            r"(?:\s*,\s*[A-Za-z_][A-Za-z0-9_$#]*)*"
            r"(?:\s+y\s+[A-Za-z_][A-Za-z0-9_$#]*)?)",

            r"(?:columnas|campos)"
            r"\s*:\s*"
            r"([A-Za-z_][A-Za-z0-9_$#]*"
            r"(?:\s*,\s*[A-Za-z_][A-Za-z0-9_$#]*)*"
            r"(?:\s+y\s+[A-Za-z_][A-Za-z0-9_$#]*)?)"
        ]

        for patron in patrones:

            encontrados = re.findall(
                patron,
                texto,
                flags=re.IGNORECASE
            )

            for encontrado in encontrados:

                if isinstance(
                    encontrado,
                    tuple
                ):

                    encontrado = encontrado[0]

                candidatos.append(
                    encontrado
                )

        # ----------------------------------------------------
        # LIMPIAR
        # ----------------------------------------------------

        resultado = []

        for bloque in candidatos:

            bloque = str(
                bloque
            )

            bloque = (
                bloque
                .replace("\n", " ")
            )

            bloque = re.sub(
                r"\s+y\s+",
                ",",
                bloque,
                flags=re.IGNORECASE
            )

            for parte in bloque.split(","):

                columna = (
                    parte
                    .strip()
                    .strip("`")
                    .strip("'")
                    .strip('"')
                    .strip()
                )

                if not columna:

                    continue

                if not re.match(
                    r"^[A-Za-z_][A-Za-z0-9_$#]*$",
                    columna
                ):

                    continue

                # Palabras claramente narrativas.
                #
                # IMPORTANTE:
                # NO tenemos una lista de columnas BI.
                # Solo palabras de lenguaje natural.
                #

                if columna.upper() in {
                    "TENGO",
                    "TABLA",
                    "QUIERO",
                    "HACER",
                    "HAZME",
                    "GENERAME",
                    "GENERA",
                    "DASHBOARD",
                    "INFORMACION",
                    "INFORMACIÓN",
                    "DATOS",
                    "CANTIDAD",
                    "REGISTROS",
                    "CONTANDO",
                    "CONTAR",
                    "COUNT",
                    "DE",
                    "SOBRE",
                    "CON"
                }:

                    continue

                if columna.upper() not in {
                    x.upper()
                    for x in resultado
                }:

                    resultado.append(
                        columna
                    )

        # ----------------------------------------------------
        # ORDENAR SEGUN APARICION
        # ----------------------------------------------------

        texto_upper = texto.upper()

        resultado.sort(
            key=lambda x:
            (
                texto_upper.find(
                    x.upper()
                )
                if texto_upper.find(
                    x.upper()
                ) >= 0
                else 999999
            )
        )

        return resultado

    # ========================================================
    # DETECTAR AGREGACION
    # ========================================================

    def _detectar_agregacion(
        self,
        consulta
    ):

        texto = str(
            consulta or ""
        ).lower()

        patrones_count = [

            "cantidad de registros",
            "contando la cantidad",
            "contar registros",
            "conteo de registros",
            "conteo registros",
            "número de registros",
            "numero de registros",
            "total de registros",
            "cantidad registros",
            "count(*)",
            "count *",
            "count de registros",
            "contar la cantidad"

        ]

        for patron in patrones_count:

            if patron in texto:

                return "count"

        return None

    # ========================================================
    # OBTENER NOMBRES REALES
    # ========================================================

    def _obtener_nombres_columnas_reales(
        self,
        analisis
    ):

        resultado = []

        columnas = (
            analisis.get(
                "columnas",
                []
            )
        )

        for columna in columnas:

            if isinstance(
                columna,
                dict
            ):

                nombre = columna.get(
                    "nombre"
                )

            else:

                nombre = columna

            if not nombre:

                continue

            nombre = str(
                nombre
            ).strip()

            if nombre.upper() not in {
                x.upper()
                for x in resultado
            }:

                resultado.append(
                    nombre
                )

        return resultado

    # ========================================================
    # VALIDAR COLUMNAS
    # ========================================================

    def _validar_columnas_solicitadas(
        self,
        solicitadas,
        reales
    ):

        mapa = {
            str(x).upper(): x
            for x in reales
        }

        faltantes = []

        for solicitada in solicitadas:

            if (
                str(solicitada).upper()
                not in mapa
            ):

                faltantes.append(
                    solicitada
                )

        return {
            "ok": len(faltantes) == 0,
            "faltantes": faltantes
        }

    # ========================================================
    # NORMALIZAR NOMBRES
    # ========================================================

    def _normalizar_nombres_reales(
        self,
        solicitadas,
        reales
    ):

        mapa = {
            str(x).upper(): x
            for x in reales
        }

        resultado = []

        for solicitada in solicitadas:

            real = mapa.get(
                str(solicitada).upper()
            )

            if real:

                if real not in resultado:

                    resultado.append(
                        real
                    )

        return resultado

    # ========================================================
    # RESTRINGIR ANALISIS
    # ========================================================

    def _restringir_analisis(
        self,
        analisis,
        columnas_solicitadas,
        agregacion=None
    ):

        analisis = dict(
            analisis or {}
        )

        permitidas = {
            str(x).upper()
            for x in columnas_solicitadas
        }

        # ----------------------------------------------------
        # COLUMNAS
        # ----------------------------------------------------

        columnas_finales = []

        for columna in analisis.get(
            "columnas",
            []
        ):

            nombre = (
                columna.get("nombre")
                if isinstance(
                    columna,
                    dict
                )
                else columna
            )

            if not nombre:

                continue

            if (
                str(nombre).upper()
                in permitidas
            ):

                columnas_finales.append(
                    columna
                )

        # ----------------------------------------------------
        # DIMENSIONES
        # ----------------------------------------------------

        dimensiones_finales = []

        for dimension in analisis.get(
            "dimensiones",
            []
        ):

            nombre = (
                dimension.get("nombre")
                if isinstance(
                    dimension,
                    dict
                )
                else dimension
            )

            if not nombre:

                continue

            if (
                str(nombre).upper()
                in permitidas
            ):

                dimensiones_finales.append(
                    dimension
                )

        # ----------------------------------------------------
        # FECHAS
        # ----------------------------------------------------

        fechas_finales = []

        for fecha in analisis.get(
            "fechas",
            []
        ):

            nombre = (
                fecha.get("nombre")
                if isinstance(
                    fecha,
                    dict
                )
                else fecha
            )

            if not nombre:

                continue

            if (
                str(nombre).upper()
                in permitidas
            ):

                fechas_finales.append(
                    fecha
                )

        # ----------------------------------------------------
        # METRICAS
        #
        # COUNT es una métrica virtual válida,
        # pero NO es una columna física.
        # ----------------------------------------------------

        metricas_finales = []

        if agregacion == "count":

            metricas_finales.append(
                {
                    "nombre": "COUNT_REGISTROS",
                    "tipo": "count",
                    "operacion": "count",
                    "virtual": True
                }
            )

        else:

            for metrica in analisis.get(
                "metricas",
                []
            ):

                nombre = (
                    metrica.get("nombre")
                    if isinstance(
                        metrica,
                        dict
                    )
                    else metrica
                )

                if not nombre:

                    continue

                if (
                    str(nombre).upper()
                    in permitidas
                ):

                    metricas_finales.append(
                        metrica
                    )

        analisis["columnas"] = (
            columnas_finales
        )

        analisis["dimensiones"] = (
            dimensiones_finales
        )

        analisis["metricas"] = (
            metricas_finales
        )

        analisis["fechas"] = (
            fechas_finales
        )

        analisis["columnas_solicitadas"] = (
            list(columnas_solicitadas)
        )

        if agregacion:

            analisis["agregacion"] = (
                agregacion
            )

        if agregacion == "count":

            analisis["metrica_virtual"] = {

                "nombre":
                    "COUNT_REGISTROS",

                "operacion":
                    "count",

                "expresion":
                    "COUNT(*)",

                "titulo":
                    "Cantidad de registros"
            }

        print(
            "[AGENTE DASHBOARD] "
            "Columnas finales para Planner:",
            [
                x.get("nombre")
                if isinstance(
                    x,
                    dict
                )
                else x
                for x in columnas_finales
            ]
        )

        print(
            "[AGENTE DASHBOARD] "
            "Dimensiones finales:",
            [
                x.get("nombre")
                if isinstance(
                    x,
                    dict
                )
                else x
                for x in dimensiones_finales
            ]
        )

        print(
            "[AGENTE DASHBOARD] "
            "Métricas finales:",
            [
                x.get("nombre")
                if isinstance(
                    x,
                    dict
                )
                else x
                for x in metricas_finales
            ]
        )

        return analisis

    # ========================================================
    # RESTRINGIR DATAFRAME
    # ========================================================

    def _restringir_dataframe(
        self,
        df,
        columnas_solicitadas
    ):

        if df is None:

            return df

        if not columnas_solicitadas:

            return df

        mapa = {
            str(columna).upper():
                columna
            for columna in df.columns
        }

        seleccionadas = []

        faltantes = []

        for solicitada in columnas_solicitadas:

            original = mapa.get(
                str(solicitada).upper()
            )

            if original:

                if original not in seleccionadas:

                    seleccionadas.append(
                        original
                    )

            else:

                faltantes.append(
                    solicitada
                )

        # ----------------------------------------------------
        # SEGURIDAD
        # ----------------------------------------------------

        if faltantes:

            raise ValueError(
                "Las siguientes columnas no "
                "existen en el DataFrame: "
                + ", ".join(
                    faltantes
                )
            )

        return df[
            seleccionadas
        ].copy()

    # ========================================================
    # OBTENER COLUMNAS DEL PLAN
    # ========================================================

    def _obtener_columnas_plan(
        self,
        plan
    ):

        resultado = []

        # ----------------------------------------------------
        # DIMENSIONES
        # ----------------------------------------------------

        for nombre in plan.get(
            "dimensiones",
            []
        ):

            if nombre:

                if nombre not in resultado:

                    resultado.append(
                        nombre
                    )

        # ----------------------------------------------------
        # FECHAS
        # ----------------------------------------------------

        for nombre in plan.get(
            "fechas",
            []
        ):

            if nombre:

                if nombre not in resultado:

                    resultado.append(
                        nombre
                    )

        # ----------------------------------------------------
        # METRICAS
        #
        # COUNT virtual no es columna física.
        # ----------------------------------------------------

        for nombre in plan.get(
            "metricas",
            []
        ):

            if not nombre:

                continue

            if str(nombre).upper() in {
                "COUNT",
                "COUNT_REGISTROS",
                "CANTIDAD"
            }:

                continue

            if nombre not in resultado:

                resultado.append(
                    nombre
                )

        return resultado

    # ========================================================
    # DETECTAR FUENTE
    # ========================================================

    def _detectar_fuente(
        self,
        consulta
    ):

        texto = str(
            consulta or ""
        ).strip()

        if not texto:

            return None

        texto_upper = texto.upper()

        # ----------------------------------------------------
        # MOTOR
        # ----------------------------------------------------

        if "NETEZZA" in texto_upper:

            motor = "NETEZZA"

        elif "TERADATA" in texto_upper:

            motor = "TERADATA"

        else:

            motor = None

        # ----------------------------------------------------
        # REFERENCIAS
        # ----------------------------------------------------

        referencias = re.findall(
            r"`([^`]+)`",
            texto
        )

        referencia = None

        for item in referencias:

            item = item.strip()

            if ".." in item:

                referencia = item

                break

            if "." in item:

                referencia = item

                break

        # ----------------------------------------------------
        # SIN BACKTICKS
        # ----------------------------------------------------

        if not referencia:

            patron_netezza = (
                r"\b[A-Za-z_][A-Za-z0-9_$#]*"
                r"\.\."
                r"[A-Za-z_][A-Za-z0-9_$#]*\b"
            )

            patron_teradata = (
                r"\b[A-Za-z_][A-Za-z0-9_$#]*"
                r"\."
                r"[A-Za-z_][A-Za-z0-9_$#]*\b"
            )

            encontrados = re.findall(
                patron_netezza,
                texto
            )

            if encontrados:

                referencia = encontrados[0]

                motor = (
                    motor
                    or "NETEZZA"
                )

            else:

                encontrados = re.findall(
                    patron_teradata,
                    texto
                )

                if encontrados:

                    referencia = (
                        encontrados[0]
                    )

                    motor = (
                        motor
                        or "TERADATA"
                    )

        if not referencia:

            return None

        referencia = (
            referencia
            .strip()
            .replace("`", "")
        )

        # ----------------------------------------------------
        # NETEZZA
        # ----------------------------------------------------

        if ".." in referencia:

            partes = referencia.split(
                "..",
                1
            )

            if len(partes) != 2:

                return None

            esquema = (
                partes[0].strip()
            )

            objeto = (
                partes[1].strip()
            )

            motor_referencia = (
                "NETEZZA"
            )

        # ----------------------------------------------------
        # TERADATA
        # ----------------------------------------------------

        else:

            partes = referencia.split(
                ".",
                1
            )

            if len(partes) != 2:

                return None

            esquema = (
                partes[0].strip()
            )

            objeto = (
                partes[1].strip()
            )

            motor_referencia = (
                "TERADATA"
            )

        if not esquema or not objeto:

            return None

        # ----------------------------------------------------
        # FORMATO DE REFERENCIA TIENE PRIORIDAD
        # ----------------------------------------------------

        if motor is None:

            motor = motor_referencia

        return {

            "motor":
                motor,

            "esquema":
                esquema,

            "objeto":
                objeto
        }

    # ========================================================
    # CONSTRUIR REFERENCIA
    # ========================================================

    def _construir_referencia(
        self,
        motor,
        esquema,
        objeto
    ):

        motor = str(
            motor or ""
        ).upper()

        if motor == "NETEZZA":

            return (
                f"{esquema}..{objeto}"
            )

        return (
            f"{esquema}.{objeto}"
        )

    # ========================================================
    # MENSAJE COLUMNAS INEXISTENTES
    # ========================================================

    def _mensaje_columnas_inexistentes(
        self,
        faltantes,
        fuente,
        columnas_reales
    ):

        mensaje = []

        mensaje.append(
            "❌ **COLUMNAS NO ENCONTRADAS**"
        )

        mensaje.append("")

        mensaje.append(
            f"La fuente `{fuente.get('objeto')}` "
            "no contiene físicamente las siguientes "
            "columnas solicitadas:"
        )

        mensaje.append("")

        for columna in faltantes:

            mensaje.append(
                f"- `{columna}`"
            )

        mensaje.append("")

        mensaje.append(
            "El dashboard no fue generado."
        )

        mensaje.append("")

        mensaje.append(
            "No se crearán columnas virtuales, "
            "aliases ni campos ficticios."
        )

        return "\n".join(
            mensaje
        )

    # ========================================================
    # FORMATEAR OPCIONES
    # ========================================================

    def _formatear_opciones(
        self,
        fuente,
        analisis,
        plan,
        columnas_solicitadas
    ):

        motor = fuente.get(
            "motor",
            "N/D"
        )

        esquema = fuente.get(
            "esquema",
            "N/D"
        )

        objeto = fuente.get(
            "objeto",
            "N/D"
        )

        opciones = plan.get(
            "opciones",
            []
        )

        recomendacion = plan.get(
            "recomendacion"
        )

        lineas = []

        lineas.append(
            "📊 **ANÁLISIS DE FUENTE**"
        )

        lineas.append("")

        lineas.append(
            f"**Motor:** {motor}"
        )

        lineas.append(
            f"**Esquema:** {esquema}"
        )

        lineas.append(
            f"**Objeto:** `{objeto}`"
        )

        lineas.append("")

        if columnas_solicitadas:

            lineas.append(
                "**Columnas solicitadas:** "
                + ", ".join(
                    columnas_solicitadas
                )
            )

        else:

            lineas.append(
                "**Modo:** análisis automático"
            )

        lineas.append("")

        lineas.append(
            "### 📊 Propuesta de dashboard"
        )

        lineas.append("")

        # ----------------------------------------------------
        # MOSTRAR CAMPOS QUE ANALIZO
        # ----------------------------------------------------

        dimensiones = [
            x.get("nombre")
            if isinstance(x, dict)
            else x
            for x in analisis.get(
                "dimensiones",
                []
            )
        ]

        metricas = [
            x.get("nombre")
            if isinstance(x, dict)
            else x
            for x in analisis.get(
                "metricas",
                []
            )
        ]

        if dimensiones:

            lineas.append(
                "**Dimensiones consideradas:** "
                + ", ".join(
                    str(x)
                    for x in dimensiones
                )
            )

        if metricas:

            lineas.append(
                "**Métricas consideradas:** "
                + ", ".join(
                    str(x)
                    for x in metricas
                )
            )

        lineas.append("")

        for item in opciones:

            numero = item.get(
                "id"
            )

            nombre = item.get(
                "nombre",
                "Dashboard"
            )

            descripcion = item.get(
                "descripcion",
                ""
            )

            if numero == recomendacion:

                lineas.append(
                    f"**{numero}. {nombre}** "
                    "⭐ Recomendada"
                )

            else:

                lineas.append(
                    f"**{numero}. {nombre}**"
                )

            if descripcion:

                lineas.append(
                    f"   {descripcion}"
                )

            lineas.append("")

        lineas.append(
            "Indícame el número de la opción "
            "que deseas construir."
        )

        return "\n".join(
            lineas
        )

    # ========================================================
    # FORMATEAR RESULTADO
    # ========================================================

    def _formatear_resultado(
        self,
        fuente,
        opcion,
        resultado,
        url
    ):

        objeto = fuente.get(
            "objeto",
            "N/D"
        )

        nombre = opcion.get(
            "nombre",
            "Dashboard"
        )

        filas = resultado.get(
            "filas",
            0
        )

        graficos = resultado.get(
            "graficos",
            0
        )

        lineas = []

        lineas.append(
            "📊 **DASHBOARD GENERADO**"
        )

        lineas.append("")

        lineas.append(
            f"**Fuente:** `{objeto}`"
        )

        lineas.append("")

        lineas.append(
            f"**Tipo:** {nombre}"
        )

        lineas.append(
            f"**Registros analizados:** {filas}"
        )

        lineas.append(
            f"**Visualizaciones:** {graficos}"
        )

        lineas.append("")

        lineas.append(
            "El dashboard interactivo está listo."
        )

        lineas.append("")

        if url:

            lineas.append(
                f"👉 [📊 **Abrir Dashboard**]({url})"
            )

        else:

            lineas.append(
                "⚠️ El dashboard fue generado, "
                "pero no se encontró su URL."
            )

        return "\n".join(
            lineas
        )

    # ========================================================
    # ERROR
    # ========================================================

    def _error(
        self,
        inicio,
        mensaje,
        fuente=None,
        referencia=None,
        analisis=None,
        plan=None
    ):

        resultado = {

            "estado":
                "error",

            "agente":
                self.nombre,

            "respuesta":
                mensaje,

            "tiempo":
                round(
                    time.time() - inicio,
                    2
                )
        }

        if fuente:

            resultado["motor"] = (
                fuente.get("motor")
            )

            resultado["esquema"] = (
                fuente.get("esquema")
            )

            resultado["objeto"] = (
                fuente.get("objeto")
            )

        if referencia:

            resultado["referencia"] = (
                referencia
            )

        if analisis is not None:

            resultado["analisis"] = (
                analisis
            )

        if plan is not None:

            resultado["plan"] = (
                plan
            )

        return resultado


# ============================================================
# FIN
# ============================================================