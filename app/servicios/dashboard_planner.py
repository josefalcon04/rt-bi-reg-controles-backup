# ============================================================
# dashboard_planner.py
# ============================================================
#
# Planner dinámico para generación de dashboards.
#
# RESPONSABILIDAD:
#   1. Recibir metadata REAL de dashboard_service.
#   2. Analizar dimensiones, métricas y fechas.
#   3. Seleccionar automáticamente los mejores campos.
#   4. Crear propuestas de dashboard.
#   5. NO generar HTML.
#
# El HTML corresponde exclusivamente a dashboard_builder.py
# ============================================================

from typing import Any, Dict, List, Optional
import math
import re


class DashboardPlanner:

    def __init__(self):
        print("[DASHBOARD PLANNER] Inicializado correctamente")

    # ========================================================
    # MÉTODO PRINCIPAL
    # ========================================================

    def planificar(
        self,
        metadata: Dict[str, Any],
        fuente: Optional[Dict[str, Any]] = None,
        columnas_solicitadas: Optional[List[str]] = None,
        agregacion: Optional[str] = None,
    ) -> Dict[str, Any]:

        print("\n" + "=" * 70)
        print("[DASHBOARD PLANNER] INICIO")
        print("=" * 70)

        fuente = fuente or {}

        motor = (
            metadata.get("motor")
            or fuente.get("motor")
            or metadata.get("database_engine")
            or "DESCONOCIDO"
        )

        esquema = (
            metadata.get("database")
            or metadata.get("esquema")
            or fuente.get("esquema")
            or ""
        )

        objeto = (
            metadata.get("objeto")
            or fuente.get("objeto")
            or ""
        )

        referencia = (
            metadata.get("referencia")
            or fuente.get("referencia")
            or self._crear_referencia(esquema, objeto)
        )

        columnas_solicitadas = columnas_solicitadas or []

        print(f"[DASHBOARD PLANNER] Motor: {motor}")
        print(f"[DASHBOARD PLANNER] Esquema: {esquema}")
        print(f"[DASHBOARD PLANNER] Objeto: {objeto}")
        print(f"[DASHBOARD PLANNER] Referencia: {referencia}")

        # ----------------------------------------------------
        # EXTRAER METADATA
        # ----------------------------------------------------

        dimensiones = self._normalizar_campos(
            metadata.get("dimensiones", [])
        )

        metricas = self._normalizar_campos(
            metadata.get("metricas", [])
        )

        fechas = self._normalizar_campos(
            metadata.get("fechas", [])
        )

        columnas = self._normalizar_campos(
            metadata.get("columnas", [])
        )

        print(
            f"[DASHBOARD PLANNER] Dimensiones detectadas: "
            f"{len(dimensiones)}"
        )

        print(
            f"[DASHBOARD PLANNER] Métricas detectadas: "
            f"{len(metricas)}"
        )

        print(
            f"[DASHBOARD PLANNER] Fechas detectadas: "
            f"{len(fechas)}"
        )

        # ----------------------------------------------------
        # SI EL SERVICE NO SEPARÓ CORRECTAMENTE LOS CAMPOS,
        # RECONSTRUIR DESDE columnas
        # ----------------------------------------------------

        if not dimensiones and not metricas and columnas:

            dimensiones = []
            metricas = []
            fechas = []

            for campo in columnas:

                if self._es_fecha(campo):
                    fechas.append(campo)

                elif self._es_numerico(campo):
                    metricas.append(campo)

                else:
                    dimensiones.append(campo)

        # ----------------------------------------------------
        # SI HAY COLUMNAS EXPLÍCITAS
        # ----------------------------------------------------

        campos_explicitos = self._resolver_columnas_solicitadas(
            columnas_solicitadas,
            columnas,
            dimensiones,
            metricas,
            fechas,
        )

        if campos_explicitos:

            print(
                "[DASHBOARD PLANNER] Columnas explícitamente "
                f"solicitadas: {campos_explicitos}"
            )

            dimensiones, metricas, fechas = (
                self._restringir_a_columnas_solicitadas(
                    campos_explicitos,
                    dimensiones,
                    metricas,
                    fechas,
                )
            )

        # ----------------------------------------------------
        # SELECCIÓN INTELIGENTE
        # ----------------------------------------------------

        dimensiones_seleccionadas = self._seleccionar_dimensiones(
            dimensiones
        )

        metricas_seleccionadas = self._seleccionar_metricas(
            metricas
        )

        fechas_seleccionadas = self._seleccionar_fechas(
            fechas
        )

        # ----------------------------------------------------
        # COUNT VIRTUAL
        # ----------------------------------------------------

        requiere_count = (
            agregacion
            and str(agregacion).lower() in {
                "count",
                "conteo",
                "cantidad"
            }
        )

        if requiere_count:

            metricas_seleccionadas = [
                self._crear_count_virtual()
            ]

        elif not metricas_seleccionadas:

            # Si no encontramos una métrica numérica útil,
            # usamos COUNT(*) como métrica universal.
            metricas_seleccionadas = [
                self._crear_count_virtual()
            ]

        # ----------------------------------------------------
        # LOG
        # ----------------------------------------------------

        print(
            "[DASHBOARD PLANNER] Dimensiones seleccionadas: "
            f"{[self._nombre(x) for x in dimensiones_seleccionadas]}"
        )

        print(
            "[DASHBOARD PLANNER] Métricas seleccionadas: "
            f"{[self._nombre(x) for x in metricas_seleccionadas]}"
        )

        print(
            "[DASHBOARD PLANNER] Fechas seleccionadas: "
            f"{[self._nombre(x) for x in fechas_seleccionadas]}"
        )

        # ----------------------------------------------------
        # GENERAR OPCIONES
        # ----------------------------------------------------

        opciones = self._generar_opciones(
            dimensiones_seleccionadas,
            metricas_seleccionadas,
            fechas_seleccionadas,
        )

        recomendacion = self._calcular_recomendacion(
            dimensiones_seleccionadas,
            metricas_seleccionadas,
            fechas_seleccionadas,
        )

        print(
            f"[DASHBOARD PLANNER] Opciones generadas: "
            f"{len(opciones)}"
        )

        print(
            f"[DASHBOARD PLANNER] Recomendación: "
            f"{recomendacion}"
        )

        print("=" * 70)
        print("[DASHBOARD PLANNER] FIN")
        print("=" * 70)

        plan = {
            "estado": "ok",
            "motor": motor,
            "esquema": esquema,
            "objeto": objeto,
            "referencia": referencia,

            "columnas_solicitadas": columnas_solicitadas,

            "dimensiones": [
                self._nombre(x)
                for x in dimensiones_seleccionadas
            ],

            "metricas": [
                self._nombre(x)
                for x in metricas_seleccionadas
            ],

            "fechas": [
                self._nombre(x)
                for x in fechas_seleccionadas
            ],

            "metadata": {
                "dimensiones": dimensiones_seleccionadas,
                "metricas": metricas_seleccionadas,
                "fechas": fechas_seleccionadas,
            },

            "opciones": opciones,

            "recomendacion": recomendacion,

            "construccion_automatica": False,
        }

        return plan
        # ========================================================
    # COMPATIBILIDAD CON AGENTE DASHBOARD
    # ========================================================

    def generar_plan(
        self,
        metadata: Dict[str, Any],
        fuente: Optional[Dict[str, Any]] = None,
        columnas_solicitadas: Optional[List[str]] = None,
        agregacion: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:

        """
        Método compatible con agente_dashboard.py.

        Mantiene la interfaz anterior del agente y delega
        la generación real del plan al método planificar().
        """

        return self.planificar(
            metadata=metadata,
            fuente=fuente,
            columnas_solicitadas=columnas_solicitadas,
            agregacion=agregacion,
        )
    
    # ========================================================
    # NORMALIZACIÓN
    # ========================================================

    def _normalizar_campos(
        self,
        campos: Any
    ) -> List[Dict[str, Any]]:

        if not campos:
            return []

        resultado = []

        for campo in campos:

            if isinstance(campo, str):

                resultado.append({
                    "nombre": campo,
                    "tipo": "",
                    "nulos": 0,
                    "cardinalidad": None,
                })

            elif isinstance(campo, dict):

                copia = dict(campo)

                if "nombre" not in copia:
                    continue

                resultado.append(copia)

        return resultado

    # ========================================================
    # NOMBRE
    # ========================================================

    def _nombre(self, campo: Dict[str, Any]) -> str:
        return str(
            campo.get("nombre")
            or campo.get("name")
            or ""
        )

    # ========================================================
    # REFERENCIA
    # ========================================================

    def _crear_referencia(
        self,
        esquema: str,
        objeto: str
    ) -> str:

        if esquema and objeto:
            return f"{esquema}.{objeto}"

        return objeto or esquema or ""

    # ========================================================
    # TIPOS
    # ========================================================

    def _tipo(self, campo: Dict[str, Any]) -> str:

        return str(
            campo.get("tipo")
            or campo.get("type")
            or ""
        ).lower()

    def _es_numerico(
        self,
        campo: Dict[str, Any]
    ) -> bool:

        tipo = self._tipo(campo)

        return any(
            x in tipo
            for x in [
                "int",
                "float",
                "double",
                "decimal",
                "numeric",
                "number",
                "real"
            ]
        )

    def _es_fecha(
        self,
        campo: Dict[str, Any]
    ) -> bool:

        tipo = self._tipo(campo)
        nombre = self._nombre(campo).lower()

        if any(
            x in tipo
            for x in [
                "date",
                "timestamp",
                "datetime"
            ]
        ):
            return True

        patrones = [
            "fecha",
            "fec",
            "date",
            "periodo",
            "period",
            "month",
            "mes",
            "year",
            "anio"
        ]

        return any(
            patron in nombre
            for patron in patrones
        )

    # ========================================================
    # COLUMNAS SOLICITADAS
    # ========================================================

    def _resolver_columnas_solicitadas(
        self,
        solicitadas: List[str],
        columnas: List[Dict[str, Any]],
        dimensiones: List[Dict[str, Any]],
        metricas: List[Dict[str, Any]],
        fechas: List[Dict[str, Any]],
    ) -> List[str]:

        if not solicitadas:
            return []

        disponibles = {}

        for campo in (
            columnas +
            dimensiones +
            metricas +
            fechas
        ):

            nombre = self._nombre(campo)

            if nombre:
                disponibles[nombre.upper()] = nombre

        resultado = []

        for solicitada in solicitadas:

            encontrada = disponibles.get(
                str(solicitada).upper()
            )

            if encontrada:
                resultado.append(encontrada)

        return resultado

    # ========================================================
    # RESTRINGIR
    # ========================================================

    def _restringir_a_columnas_solicitadas(
        self,
        solicitadas: List[str],
        dimensiones: List[Dict[str, Any]],
        metricas: List[Dict[str, Any]],
        fechas: List[Dict[str, Any]],
    ):

        permitidas = {
            x.upper()
            for x in solicitadas
        }

        nuevas_dimensiones = [
            x for x in dimensiones
            if self._nombre(x).upper() in permitidas
        ]

        nuevas_metricas = [
            x for x in metricas
            if self._nombre(x).upper() in permitidas
        ]

        nuevas_fechas = [
            x for x in fechas
            if self._nombre(x).upper() in permitidas
        ]

        return (
            nuevas_dimensiones,
            nuevas_metricas,
            nuevas_fechas
        )

    # ========================================================
    # DIMENSIONES
    # ========================================================

    def _seleccionar_dimensiones(
        self,
        dimensiones: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:

        candidatos = []

        for campo in dimensiones:

            nombre = self._nombre(campo)

            if not nombre:
                continue

            cardinalidad = self._cardinalidad(campo)

            nulos = self._nulos(campo)

            # ----------------------------------------------
            # DESCARTAR CONSTANTES
            # ----------------------------------------------

            if cardinalidad is not None:

                if cardinalidad <= 1:
                    continue

            # ----------------------------------------------
            # DESCARTAR CARDINALIDAD DEMASIADO ALTA
            # ----------------------------------------------

            if cardinalidad is not None:

                if cardinalidad > 500:
                    continue

            # ----------------------------------------------
            # PENALIZAR MUCHO NULO
            # ----------------------------------------------

            score = 0.0

            if cardinalidad is not None:

                if cardinalidad <= 5:
                    score += 5

                elif cardinalidad <= 10:
                    score += 4

                elif cardinalidad <= 20:
                    score += 3

                elif cardinalidad <= 50:
                    score += 2

                else:
                    score += 1

            # Menos nulos = mejor
            if nulos == 0:
                score += 2

            elif nulos < 0.10:
                score += 1

            # ----------------------------------------------
            # NOMBRES DESCRIPTIVOS
            # ----------------------------------------------

            nombre_lower = nombre.lower()

            indicadores = [
                "estado",
                "tipo",
                "categoria",
                "producto",
                "plan",
                "fuente",
                "departamento",
                "region",
                "zona",
                "segmento",
                "cliente"
            ]

            if any(
                x in nombre_lower
                for x in indicadores
            ):
                score += 2

            candidatos.append(
                (score, campo)
            )

        candidatos.sort(
            key=lambda x: x[0],
            reverse=True
        )

        # Máximo 4 dimensiones visualmente útiles.
        return [campo for _, campo in candidatos[:4]]

    # ========================================================
    # MÉTRICAS
    # ========================================================

    def _seleccionar_metricas(
        self,
        metricas: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:

        candidatos = []

        for campo in metricas:

            nombre = self._nombre(campo)

            if not nombre:
                continue

            cardinalidad = self._cardinalidad(campo)

            nulos = self._nulos(campo)

            # ----------------------------------------------
            # IDENTIFICADORES
            # ----------------------------------------------

            if self._parece_identificador(
                campo
            ):
                continue

            score = 0.0

            # ----------------------------------------------
            # CARDINALIDAD
            # ----------------------------------------------

            if cardinalidad is not None:

                if cardinalidad <= 1:
                    continue

                if cardinalidad <= 10:
                    score += 1

                elif cardinalidad <= 100:
                    score += 4

                elif cardinalidad <= 1000:
                    score += 3

                else:
                    score += 1

            # ----------------------------------------------
            # NULOS
            # ----------------------------------------------

            if nulos == 0:
                score += 2

            elif nulos < 0.10:
                score += 1

            elif nulos > 0.80:
                score -= 4

            # ----------------------------------------------
            # NOMBRE
            # ----------------------------------------------

            nombre_lower = nombre.lower()

            indicadores = [
                "monto",
                "importe",
                "precio",
                "saldo",
                "cantidad",
                "total",
                "venta",
                "ingreso",
                "costo",
                "volumen"
            ]

            if any(
                x in nombre_lower
                for x in indicadores
            ):
                score += 3

            candidatos.append(
                (score, campo)
            )

        candidatos.sort(
            key=lambda x: x[0],
            reverse=True
        )

        return [campo for _, campo in candidatos[:4]]

    # ========================================================
    # IDENTIFICADOR
    # ========================================================

    def _parece_identificador(
        self,
        campo: Dict[str, Any]
    ) -> bool:

        nombre = self._nombre(campo).lower()

        cardinalidad = self._cardinalidad(campo)

        if cardinalidad is None:
            return False

        # ----------------------------------------------
        # Nombres típicos de identificador
        # ----------------------------------------------

        patrones = [
            "id",
            "key",
            "codigo",
            "cod",
            "customer",
            "cliente",
            "telefono",
            "tel",
            "folio",
            "nro",
            "numero",
            "num"
        ]

        if any(
            re.search(
                rf"(^|_){re.escape(p)}($|_)",
                nombre
            )
            for p in patrones
        ):
            return True

        # ----------------------------------------------
        # Cardinalidad casi única
        # ----------------------------------------------

        filas = campo.get(
            "filas"
            or campo.get("rows")
            or campo.get("total_filas")
        )

        if filas:

            try:

                ratio = (
                    float(cardinalidad)
                    /
                    float(filas)
                )

                if ratio >= 0.95:
                    return True

            except Exception:
                pass

        return False

    # ========================================================
    # FECHAS
    # ========================================================

    def _seleccionar_fechas(
        self,
        fechas: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:

        resultado = []

        for campo in fechas:

            cardinalidad = self._cardinalidad(campo)

            if cardinalidad is None:
                resultado.append(campo)
                continue

            if cardinalidad > 0:
                resultado.append(campo)

        return resultado[:3]

    # ========================================================
    # COUNT VIRTUAL
    # ========================================================

    def _crear_count_virtual(self):

        return {
            "nombre": "COUNT_REGISTROS",
            "tipo": "count",
            "operacion": "count",
            "expresion": "COUNT(*)",
            "titulo": "Cantidad de registros",
            "virtual": True
        }

    # ========================================================
    # OPCIONES
    # ========================================================

    def _generar_opciones(
        self,
        dimensiones: List[Dict[str, Any]],
        metricas: List[Dict[str, Any]],
        fechas: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:

        dim_names = [self._nombre(x) for x in dimensiones]
        metric_names = [self._nombre(x) for x in metricas]
        fecha_names = [self._nombre(x) for x in fechas]

        principal = metric_names[0] if metric_names else None

        # KPIs dinámicos: máximo 4 y únicamente métricas reales o COUNT virtual.
        kpis = []
        for campo in metricas[:4]:
            nombre = self._nombre(campo)
            if nombre:
                kpis.append({
                    "tipo": "kpi",
                    "campo": nombre,
                    "titulo": self._titulo(nombre)
                })

        # Gráficos categóricos según cardinalidad real.
        graficos_categoricos = []
        for dimension in dimensiones[:3]:
            nombre = self._nombre(dimension)
            if principal and nombre:
                cardinalidad = self._cardinalidad(dimension)
                tipo = "donut" if cardinalidad is not None and cardinalidad <= 8 else "bar"

                graficos_categoricos.append({
                    "tipo": tipo,
                    "titulo": (
                        f"{self._titulo(principal)} por "
                        f"{self._titulo(nombre)}"
                    ),
                    "eje_x": nombre,
                    "eje_y": principal
                })

        # Solo se crea tendencia si realmente existen fechas.
        graficos_fecha = []
        if fecha_names and principal:
            graficos_fecha.append({
                "tipo": "line",
                "titulo": (
                    f"{self._titulo(principal)} por "
                    f"{self._titulo(fecha_names[0])}"
                ),
                "eje_x": fecha_names[0],
                "eje_y": principal
            })

        opciones = []

        # ----------------------------------------------------
        # OPCIÓN 1 - EJECUTIVO
        # ----------------------------------------------------
        elementos_1 = kpis[:3]

        if graficos_fecha:
            elementos_1.append(graficos_fecha[0])
        elif graficos_categoricos:
            elementos_1.append(graficos_categoricos[0])

        opciones.append({
            "id": 1,
            "tipo": "ejecutivo",
            "nombre": "Dashboard Ejecutivo",
            "descripcion": (
                "Resumen ejecutivo construido a partir de las "
                "métricas y dimensiones más relevantes detectadas."
            ),
            "elementos": elementos_1
        })

        # ----------------------------------------------------
        # OPCIÓN 2 - OPERATIVO
        # ----------------------------------------------------
        elementos_2 = []
        elementos_2.extend(kpis[:4])
        elementos_2.extend(graficos_categoricos[:3])

        if graficos_fecha:
            elementos_2.append(graficos_fecha[0])

        campos_tabla = dim_names[:4] + metric_names[:3]
        if campos_tabla:
            elementos_2.append({
                "tipo": "table",
                "titulo": "Detalle de información",
                "campos": campos_tabla
            })

        opciones.append({
            "id": 2,
            "tipo": "operativo",
            "nombre": "Dashboard Operativo",
            "descripcion": (
                "Vista orientada al seguimiento, comparación y "
                "distribución de los principales campos detectados."
            ),
            "elementos": elementos_2
        })

        # ----------------------------------------------------
        # OPCIÓN 3 - ANALÍTICO
        # ----------------------------------------------------
        elementos_3 = kpis[:2]

        if len(dim_names) >= 2 and principal:
            elementos_3.append({
                "tipo": "heatmap",
                "titulo": (
                    f"Relación entre {self._titulo(dim_names[0])} "
                    f"y {self._titulo(dim_names[1])}"
                ),
                "eje_x": dim_names[0],
                "eje_y": dim_names[1],
                "valor": principal
            })

            elementos_3.append({
                "tipo": "bar",
                "titulo": (
                    f"{self._titulo(principal)} por "
                    f"{self._titulo(dim_names[0])} y "
                    f"{self._titulo(dim_names[1])}"
                ),
                "eje_x": dim_names[0],
                "eje_y": principal,
                "agrupacion": dim_names[1]
            })
        elif graficos_categoricos:
            elementos_3.extend(graficos_categoricos[:2])

        if graficos_fecha:
            elementos_3.append(graficos_fecha[0])

        opciones.append({
            "id": 3,
            "tipo": "analitico",
            "nombre": "Dashboard Analítico",
            "descripcion": (
                "Vista orientada a descubrir relaciones y patrones "
                "entre las dimensiones, fechas y métricas disponibles."
            ),
            "elementos": elementos_3
        })

        return opciones

    # ========================================================
    # RECOMENDACIÓN
    # ========================================================

    def _calcular_recomendacion(
        self,
        dimensiones: List[Dict[str, Any]],
        metricas: List[Dict[str, Any]],
        fechas: List[Dict[str, Any]],
    ) -> int:

        # Con fecha + métrica, la tendencia aporta valor.
        if fechas and metricas:
            return 3

        # Con varias dimensiones y métricas, la vista operativa
        # permite comparar y revisar el detalle.
        if len(dimensiones) >= 2 and len(metricas) >= 1:
            return 2

        return 1

    # ========================================================
    # CARDINALIDAD
    # ========================================================

    def _cardinalidad(
        self,
        campo: Dict[str, Any]
    ):

        valor = (
            campo.get("cardinalidad")
            if "cardinalidad" in campo
            else campo.get("cardinality")
        )

        try:

            if valor is None:
                return None

            return int(valor)

        except Exception:

            return None

    # ========================================================
    # NULOS
    # ========================================================

    def _nulos(
        self,
        campo: Dict[str, Any]
    ) -> float:

        valor = (
            campo.get("nulos")
            if "nulos" in campo
            else campo.get("nulls", 0)
        )

        try:

            valor = float(valor)

            # Si viene como cantidad absoluta,
            # la dejamos como señal simple.
            if valor > 1:
                return valor

            return valor

        except Exception:

            return 0.0

    # ========================================================
    # TÍTULO
    # ========================================================

    def _titulo(
        self,
        nombre: str
    ) -> str:

        if not nombre:
            return ""

        texto = str(nombre)

        texto = texto.replace("_", " ")

        return texto[:1].upper() + texto[1:].lower()