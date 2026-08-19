# ============================================================
# DASHBOARD BUILDER
# ============================================================
# Generador de dashboards dinámicos y profesionales.
#
# Características:
# - CSS embebido
# - JavaScript embebido
# - Plotly CDN
# - KPIs automáticos
# - Filtros dinámicos
# - Gráficos interactivos
# - Tabla de detalle
# - Responsive
# - Interacción entre filtros y gráficos
# - No depende de archivos .css ni .js externos
# ============================================================

import os
import re
import json
import time
import uuid
import html

import pandas as pd


class DashboardBuilder:

    def __init__(self, output_dir="static/dashboards"):

        self.output_dir = output_dir

        os.makedirs(
            self.output_dir,
            exist_ok=True
        )

        print(
            "[DASHBOARD BUILDER] "
            "Inicializado correctamente"
        )

    # ========================================================
    # UTILIDADES
    # ========================================================

    def _safe_filename(self, texto):

        texto = str(texto)

        texto = texto.lower()

        texto = re.sub(
            r"[^a-z0-9_]+",
            "_",
            texto
        )

        texto = re.sub(
            r"_+",
            "_",
            texto
        )

        return texto.strip("_")

    # ========================================================
    # NORMALIZAR / EXTRAER PLAN DEL PLANNER
    # ========================================================

    def _extraer_plan(self, plan):
        """
        Normaliza las distintas formas en que AgenteDashboard puede
        entregar el plan al Builder.

        Formas soportadas:
          1. {"dimensiones": [...], "metricas": [...], "fechas": [...]}
          2. {"plan": { ... }}
          3. {"resultado": {"plan": { ... }}}
          4. {"plan": {"plan": { ... }}}

        Nunca modifica el objeto original.
        """

        if not isinstance(plan, dict):
            return {}

        # Caso 1: ya es el plan.
        if any(
            clave in plan
            for clave in (
                "dimensiones",
                "metricas",
                "fechas",
                "opciones",
            )
        ):
            return plan

        # Buscar wrappers habituales sin entrar en estructuras
        # arbitrariamente profundas.
        for clave in ("plan", "resultado", "analisis"):
            valor = plan.get(clave)

            if isinstance(valor, dict):

                if any(
                    k in valor
                    for k in (
                        "dimensiones",
                        "metricas",
                        "fechas",
                        "opciones",
                    )
                ):
                    return valor

                anidado = self._extraer_plan(valor)

                if anidado:
                    return anidado

        return {}

    def _obtener_dimensiones(
        self,
        plan,
        df
    ):

        dimensiones = []

        if isinstance(plan, dict):

            dimensiones = plan.get(
                "dimensiones",
                []
            )

        dimensiones = [
            d for d in dimensiones
            if d in df.columns
        ]

        return dimensiones

    def _obtener_metricas(
        self,
        plan,
        df
    ):

        metricas = []

        if isinstance(plan, dict):

            metricas = plan.get(
                "metricas",
                []
            )

        metricas = [
            m for m in metricas
            if m in df.columns
        ]

        return metricas

    def _obtener_fechas(
        self,
        plan,
        df
    ):

        fechas = []

        if isinstance(plan, dict):

            fechas = plan.get(
                "fechas",
                []
            )

        fechas = [
            f for f in fechas
            if f in df.columns
        ]

        return fechas

    # ========================================================
    # INFERIR METADATA CUANDO EL AGENTE NO LA ENVÍA
    # ========================================================

    def _inferir_metadata(self, df):
        """
        Infere dimensiones, métricas y campos temporales directamente
        desde el DataFrame.

        Esto permite que  funcione aunque AgenteDashboard entregue
        solamente una opción del planner en lugar del plan completo.
        """

        dimensiones = []
        metricas = []
        fechas = []

        # Campos temporales habituales en BI.
        patrones_fecha = (
            "FECHA",
            "DATE",
            "DATETIME",
            "TIMESTAMP",
            "ANIO",
            "AÑO",
            "YEAR",
            "MES",
            "MONTH",
            "TRIMESTRE",
            "TRIM",
            "PERIODO",
            "PERIOD",
        )

        for columna in df.columns:

            nombre = str(columna).strip()
            nombre_upper = nombre.upper()
            serie = df[columna]

            es_fecha = any(
                patron in nombre_upper
                for patron in patrones_fecha
            )

            if es_fecha:
                fechas.append(nombre)
                continue

            if pd.api.types.is_numeric_dtype(serie):
                metricas.append(nombre)
                continue

            # Categóricas razonables para filtros/gráficos.
            cardinalidad = serie.nunique(dropna=True)

            if cardinalidad <= 100:
                dimensiones.append(nombre)

        # Evitar métricas que sean en realidad campos de fecha.
        metricas = [
            m for m in metricas
            if m not in fechas
        ]

        return {
            "dimensiones": dimensiones,
            "metricas": metricas,
            "fechas": fechas,
        }

    def _resolver_metadata(self, plan, df):
        """Resuelve metadata respetando estrictamente el Planner."""
        plan_real = self._extraer_plan(plan)

        tiene_metadata = any(
            key in plan_real
            for key in ("dimensiones", "metricas", "fechas")
        )

        def nombre(item):
            if isinstance(item, dict):
                return str(item.get("nombre", ""))
            return str(item)

        dimensiones = [
            nombre(x) for x in plan_real.get("dimensiones", [])
            if nombre(x) in df.columns
        ]
        metricas = [
            nombre(x) for x in plan_real.get("metricas", [])
            if nombre(x) in df.columns
        ]
        fechas = [
            nombre(x) for x in plan_real.get("fechas", [])
            if nombre(x) in df.columns
        ]

        if tiene_metadata:
            return dimensiones, metricas, fechas

        # Solo inferir cuando el Planner realmente no entregó metadata.
        inferido = self._inferir_metadata(df)
        return (
            inferido["dimensiones"],
            inferido["metricas"],
            inferido["fechas"]
        )

    # ========================================================
    # ELEGIR MÉTRICA PRINCIPAL
    # ========================================================

    def _seleccionar_metrica(
        self,
        df,
        metricas
    ):

        for columna in metricas:

            if columna not in df.columns:
                continue

            serie = pd.to_numeric(
                df[columna],
                errors="coerce"
            )

            if serie.notna().any():

                return columna

        # No seleccionar una columna arbitraria: el Planner manda.
        return None

    # ========================================================
    # NORMALIZAR DATOS
    # ========================================================

    def _normalizar_dataframe(
        self,
        df
    ):

        df = df.copy()

        for columna in df.columns:

            if pd.api.types.is_object_dtype(
                df[columna]
            ):

                # Intentamos convertir únicamente
                # cuando la mayoría de valores
                # parecen numéricos.

                convertido = pd.to_numeric(
                    df[columna],
                    errors="coerce"
                )

                porcentaje = (
                    convertido.notna().mean()
                    if len(df) > 0
                    else 0
                )

                if porcentaje >= 0.90:

                    df[columna] = convertido

        return df

    # ========================================================
    # SERIALIZAR DATAFRAME
    # ========================================================

    def _dataframe_json(
        self,
        df
    ):

        registros = []

        for _, fila in df.iterrows():

            registro = {}

            for columna in df.columns:

                valor = fila[columna]

                if pd.isna(valor):

                    valor = None

                elif hasattr(valor, "item"):

                    try:

                        valor = valor.item()

                    except Exception:

                        valor = str(valor)

                elif not isinstance(
                    valor,
                    (
                        str,
                        int,
                        float,
                        bool,
                        type(None)
                    )
                ):

                    valor = str(valor)

                registro[str(columna)] = valor

            registros.append(
                registro
            )

        return registros

    # ========================================================
    # FORMATO DE NÚMEROS
    # ========================================================

    def _numero_js(self):

        return """
function formatoNumero(valor) {

    if (
        valor === null ||
        valor === undefined ||
        isNaN(valor)
    ) {
        return "0";
    }

    const numero = Number(valor);

    if (Math.abs(numero) >= 1000000000) {

        return (
            (numero / 1000000000)
            .toFixed(1)
            .replace(/\\.0$/, "")
            + "B"
        );
    }

    if (Math.abs(numero) >= 1000000) {

        return (
            (numero / 1000000)
            .toFixed(1)
            .replace(/\\.0$/, "")
            + "M"
        );
    }

    if (Math.abs(numero) >= 1000) {

        return (
            (numero / 1000)
            .toFixed(1)
            .replace(/\\.0$/, "")
            + "K"
        );
    }

    return numero.toLocaleString(
        "es-PE",
        {
            maximumFractionDigits: 2
        }
    );
}
"""

    # ========================================================
    # GENERAR CSS
    # ========================================================

    def _generar_css(self):

        return r"""
/* ==========================================================
   DASHBOARD 
   ========================================================== */

* {
    box-sizing: border-box;
}

body {

    margin: 0;

    padding: 0;

    font-family:
        "Segoe UI",
        Arial,
        sans-serif;

    background:
        #f4f7fb;

    color:
        #172033;
}

.dashboard {

    width: 100%;

    min-height: 100vh;

    padding: 24px 30px 40px;
}

/* ==========================================================
   HEADER
   ========================================================== */

.dashboard-header {

    display: flex;

    justify-content: space-between;

    align-items: center;

    gap: 20px;

    margin-bottom: 22px;

    padding: 22px 26px;

    background:
        linear-gradient(
            135deg,
            #172b4d,
            #244b78
        );

    border-radius: 16px;

    color: white;

    box-shadow:
        0 8px 24px
        rgba(23, 43, 77, 0.14);
}

.header-title {

    margin: 0;

    font-size: 25px;

    font-weight: 700;

    letter-spacing: 0.2px;
}

.header-subtitle {

    margin-top: 6px;

    font-size: 13px;

    opacity: 0.82;
}

.header-badge {

    padding: 8px 13px;

    border-radius: 20px;

    background:
        rgba(255,255,255,0.14);

    border:
        1px solid
        rgba(255,255,255,0.20);

    font-size: 12px;

    white-space: nowrap;
}

/* ==========================================================
   KPI
   ========================================================== */

.kpi-grid {

    display: grid;

    grid-template-columns:
        repeat(
            4,
            minmax(0, 1fr)
        );

    gap: 16px;

    margin-bottom: 20px;
}

.kpi-card {

    position: relative;

    background: white;

    border-radius: 14px;

    padding: 20px;

    min-height: 118px;

    border:
        1px solid
        #e5eaf1;

    box-shadow:
        0 5px 18px
        rgba(30, 55, 90, 0.06);

    overflow: hidden;
}

.kpi-card::before {

    content: "";

    position: absolute;

    left: 0;

    top: 0;

    bottom: 0;

    width: 4px;

    background:
        #2f6fed;
}

.kpi-label {

    color:
        #718096;

    font-size: 13px;

    font-weight: 600;

    margin-bottom: 10px;
}

.kpi-value {

    font-size: 28px;

    font-weight: 700;

    color:
        #172b4d;
}

.kpi-detail {

    margin-top: 7px;

    color:
        #9aa5b5;

    font-size: 11px;
}

/* ==========================================================
   FILTROS
   ========================================================== */

.filters-card {

    background: white;

    border:
        1px solid
        #e5eaf1;

    border-radius: 14px;

    padding: 18px;

    margin-bottom: 20px;

    box-shadow:
        0 5px 18px
        rgba(30, 55, 90, 0.05);
}

.filters-header {

    display: flex;

    justify-content: space-between;

    align-items: center;

    margin-bottom: 14px;
}

.filters-title {

    font-size: 14px;

    font-weight: 700;

    color:
        #253858;
}

.btn-reset {

    border: none;

    background:
        #eef3fb;

    color:
        #2f5f9f;

    padding:
        7px 12px;

    border-radius:
        8px;

    cursor: pointer;

    font-size: 12px;

    font-weight: 600;
}

.btn-reset:hover {

    background:
        #dfe9f8;
}

.filters-grid {

    display: grid;

    grid-template-columns:
        repeat(
            4,
            minmax(0, 1fr)
        );

    gap: 12px;
}

.filter-group label {

    display: block;

    font-size: 11px;

    font-weight: 600;

    color:
        #718096;

    margin-bottom: 6px;
}

.filter-group select {

    width: 100%;

    height: 38px;

    padding:
        0 10px;

    border:
        1px solid
        #dce3ed;

    border-radius:
        8px;

    background:
        #fff;

    color:
        #253858;

    outline: none;
}

.filter-group select:focus {

    border-color:
        #5d8ed8;

    box-shadow:
        0 0 0 3px
        rgba(93, 142, 216, 0.12);
}

/* ==========================================================
   GRID DE GRÁFICOS
   ========================================================== */

.charts-grid {

    display: grid;

    grid-template-columns:
        repeat(
            2,
            minmax(0, 1fr)
        );

    gap: 18px;

    margin-bottom: 20px;
}

.chart-card {

    background: white;

    border:
        1px solid
        #e5eaf1;

    border-radius:
        14px;

    padding:
        14px 16px 8px;

    box-shadow:
        0 5px 18px
        rgba(30, 55, 90, 0.05);

    min-height: 390px;
}

.chart-card.full {

    grid-column:
        1 / -1;
}

.chart-title {

    font-size: 14px;

    font-weight: 700;

    color:
        #253858;

    padding:
        6px 4px 2px;
}

.chart-subtitle {

    font-size: 11px;

    color:
        #8b96a8;

    padding:
        3px 4px 0;
}

.chart {

    width: 100%;

    height: 330px;
}

/* ==========================================================
   TABLA
   ========================================================== */

.table-card {

    background: white;

    border:
        1px solid
        #e5eaf1;

    border-radius:
        14px;

    padding:
        18px;

    box-shadow:
        0 5px 18px
        rgba(30, 55, 90, 0.05);
}

.table-header {

    display: flex;

    justify-content: space-between;

    align-items: center;

    margin-bottom: 14px;
}

.table-title {

    font-size: 14px;

    font-weight: 700;

    color:
        #253858;
}

.table-info {

    color:
        #8b96a8;

    font-size: 11px;
}

.table-wrapper {

    overflow-x: auto;

    max-height: 420px;

    overflow-y: auto;
}

table {

    width: 100%;

    border-collapse:
        collapse;

    font-size: 12px;
}

thead {

    position: sticky;

    top: 0;

    z-index: 2;
}

th {

    background:
        #f4f7fb;

    color:
        #56657a;

    text-align: left;

    padding:
        11px 10px;

    font-weight: 700;

    border-bottom:
        1px solid
        #dfe5ee;
}

td {

    padding:
        10px;

    border-bottom:
        1px solid
        #edf0f5;

    color:
        #39475a;
}

tbody tr:hover {

    background:
        #f8fbff;
}

/* ==========================================================
   FOOTER
   ========================================================== */

.dashboard-footer {

    margin-top: 18px;

    text-align: right;

    color:
        #98a2b3;

    font-size: 11px;
}

/* ==========================================================
   RESPONSIVE
   ========================================================== */

@media (max-width: 1100px) {

    .kpi-grid {

        grid-template-columns:
            repeat(2, 1fr);
    }

    .filters-grid {

        grid-template-columns:
            repeat(2, 1fr);
    }
}

@media (max-width: 760px) {

    .dashboard {

        padding:
            14px;
    }

    .dashboard-header {

        flex-direction:
            column;

        align-items:
            flex-start;
    }

    .kpi-grid {

        grid-template-columns:
            1fr;
    }

    .filters-grid {

        grid-template-columns:
            1fr;
    }

    .charts-grid {

        grid-template-columns:
            1fr;
    }

    .chart-card.full {

        grid-column:
            auto;
    }
}
"""

    # ========================================================
    # GENERAR HTML
    # ========================================================

    def construir(
        self,
        df,
        plan=None,
        titulo=None,
        esquema=None,
        objeto=None,
        motor=None
    ):

        inicio = time.time()

        print()
        print(
            "======================================================================"
        )

        print(
            "[DASHBOARD BUILDER] INICIO"
        )

        # ----------------------------------------------------
        # VALIDACIÓN
        # ----------------------------------------------------

        if df is None:

            raise ValueError(
                "El DataFrame no puede ser None."
            )

        if not isinstance(df, pd.DataFrame):

            raise TypeError(
                "df debe ser un pandas.DataFrame."
            )

        if df.empty:

            raise ValueError(
                "No existen datos para construir el dashboard."
            )

        # ----------------------------------------------------
        # NORMALIZAR
        # ----------------------------------------------------

        df = self._normalizar_dataframe(
            df
        )

        # ----------------------------------------------------
        # SEGURIDAD COUNT(*)
        # ----------------------------------------------------
        # Si el Planner indicó COUNT y por cualquier motivo el
        # Agente no agregó CANTIDAD, la creamos aquí como 1 por
        # fila. Así el Builder puede sumar correctamente bajo
        # filtros sin volver a seleccionar otra columna numérica.
        # ----------------------------------------------------
        plan_real_previo = self._extraer_plan(plan)
        if (
            isinstance(plan_real_previo, dict)
            and str(plan_real_previo.get("agregacion", "")).lower() == "count"
            and "CANTIDAD" not in df.columns
        ):
            df = df.copy()
            df["CANTIDAD"] = 1
            print(
                "[DASHBOARD BUILDER] "
                "Métrica virtual COUNT(*) creada: CANTIDAD = 1 por fila"
            )

        # ----------------------------------------------------
        # INFORMACIÓN
        # ----------------------------------------------------

        dimensiones, metricas, fechas = self._resolver_metadata(
            plan,
            df
        )

        print(
            "[DASHBOARD BUILDER] "
            "Metadata resuelto: "
            f"{len(dimensiones)} dimensiones, "
            f"{len(metricas)} métricas, "
            f"{len(fechas)} fechas"
        )

        if not self._extraer_plan(plan):
            print(
                "[DASHBOARD BUILDER] "
                "Planner sin metadata completo; "
                "se utilizó inferencia automática desde el DataFrame."
            )

        metrica = self._seleccionar_metrica(
            df,
            metricas
        )

        if titulo is None:

            titulo = (
                "Dashboard - "
                + str(objeto or "Fuente")
            )

        print(
            "[DASHBOARD BUILDER] "
            f"Título: {titulo}"
        )

        print(
            "[DASHBOARD BUILDER] "
            f"Filas: {len(df)}"
        )

        print(
            "[DASHBOARD BUILDER] "
            f"Columnas: {len(df.columns)}"
        )

        print(
            "[DASHBOARD BUILDER] "
            f"Dimensiones: {len(dimensiones)}"
        )

        print(
            "[DASHBOARD BUILDER] "
            f"Métricas: {len(metricas)}"
        )

        print(
            "[DASHBOARD BUILDER] "
            f"Fechas: {len(fechas)}"
        )

        print(
            "[DASHBOARD BUILDER] "
            f"Métrica principal: {metrica}"
        )

        # ----------------------------------------------------
        # DATOS
        # ----------------------------------------------------

        datos = self._dataframe_json(
            df
        )

        datos_json = json.dumps(
            datos,
            ensure_ascii=False
        )

        columnas = [
            str(c)
            for c in df.columns
        ]

        columnas_json = json.dumps(
            columnas,
            ensure_ascii=False
        )

        dimensiones_json = json.dumps(
            dimensiones,
            ensure_ascii=False
        )

        fechas_json = json.dumps(
            fechas,
            ensure_ascii=False
        )

        metrica_json = json.dumps(
            metrica,
            ensure_ascii=False
        )

        # ----------------------------------------------------
        # ELEMENTOS PROPUESTOS POR EL PLANNER
        # ----------------------------------------------------
        plan_real = self._extraer_plan(plan)
        elementos = []

        if isinstance(plan_real, dict):
            elementos = plan_real.get("elementos", []) or []

            if not elementos:
                opcion_id = plan_real.get("opcion")
                opciones = plan_real.get("opciones", []) or []

                if opcion_id is not None:
                    for opcion in opciones:
                        if (
                            isinstance(opcion, dict)
                            and opcion.get("id") == opcion_id
                        ):
                            elementos = opcion.get(
                                "elementos", []
                            ) or []
                            break

            if (
                not elementos
                and isinstance(
                    plan_real.get("opcion"),
                    dict
                )
            ):
                elementos = (
                    plan_real["opcion"]
                    .get("elementos", [])
                    or []
                )

        elementos_json = json.dumps(
            elementos,
            ensure_ascii=False
        )

        # ----------------------------------------------------
        # FILTROS
        # ----------------------------------------------------

        filtros = []

        for columna in dimensiones + fechas:

            if columna not in df.columns:
                continue

            cardinalidad = (
                df[columna]
                .nunique(dropna=True)
            )

            # Evitamos combos con demasiados valores.
            if cardinalidad <= 50:

                valores = (
                    df[columna]
                    .dropna()
                    .astype(str)
                    .drop_duplicates()
                    .sort_values()
                    .tolist()
                )

                filtros.append(
                    {
                        "campo": columna,
                        "valores": valores
                    }
                )

        filtros_json = json.dumps(
            filtros,
            ensure_ascii=False
        )

        # ----------------------------------------------------
        # METADATOS
        # ----------------------------------------------------

        nombre_archivo = (
            "dashboard_"
            + self._safe_filename(
                objeto or "fuente"
            )
            + "_"
            + uuid.uuid4().hex[:8]
            + ".html"
        )

        ruta_archivo = os.path.join(
            self.output_dir,
            nombre_archivo
        )

        # ----------------------------------------------------
        # HTML
        # ----------------------------------------------------

        html_documento = """
<!DOCTYPE html>

<html lang="es">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<title>
    __DASH_TITLE__
</title>

<script
    src="https://cdn.plot.ly/plotly-2.35.2.min.js">
</script>

<style>

__DASH_CSS__

</style>

</head>

<body>

<div class="dashboard">

    <!-- ==================================================
         HEADER
         ================================================== -->

    <header class="dashboard-header">

        <div>

            <h1 class="header-title">
                __DASH_TITLE__
            </h1>

            <div class="header-subtitle">

                __DASH_MOTOR__
                &nbsp;•&nbsp;
                __DASH_SCHEMA__
                &nbsp;•&nbsp;
                __DASH_OBJECT__

            </div>

        </div>

        <div class="header-badge">
            Dashboard Ejecutivo
        </div>

    </header>


    <!-- ==================================================
         KPIs
         ================================================== -->

    <section
        id="kpiGrid"
        class="kpi-grid">
    </section>


    <!-- ==================================================
         FILTROS
         ================================================== -->

    <section class="filters-card">

        <div class="filters-header">

            <div class="filters-title">
                Filtros
            </div>

            <button
                id="btnReset"
                class="btn-reset"
                type="button"
            >
                Limpiar filtros
            </button>

        </div>

        <div
            id="filtersGrid"
            class="filters-grid">
        </div>

    </section>


    <!-- ==================================================
         GRÁFICOS
         ================================================== -->

    <section
        id="chartsGrid"
        class="charts-grid">
    </section>


    <!-- ==================================================
         TABLA
         ================================================== -->

    <section class="table-card">

        <div class="table-header">

            <div class="table-title">
                Detalle de datos
            </div>

            <div
                id="tableInfo"
                class="table-info">
            </div>

        </div>

        <div class="table-wrapper">

            <table>

                <thead id="tableHead">
                </thead>

                <tbody id="tableBody">
                </tbody>

            </table>

        </div>

    </section>


    <div class="dashboard-footer">

        Generado automáticamente por Dashboard Builder

    </div>

</div>


<script>

__DASH_NUMBER_JS__


/* ==========================================================
   DATOS
   ========================================================== */

const DATOS = __DASH_DATA__;

const COLUMNAS = __DASH_COLUMNS__;

const DIMENSIONES = __DASH_DIMENSIONS__;

const FECHAS = __DASH_DATES__;

const METRICA = __DASH_METRIC__;

const FILTROS = __DASH_FILTERS__;\nconst ELEMENTOS = __DASH_ELEMENTS__;\nconst METRICAS = __DASH_METRICS__;


/* ==========================================================
   ESTADO
   ========================================================== */

let datosFiltrados = [...DATOS];


/* ==========================================================
   CONFIGURACIÓN PLOTLY
   ========================================================== */

const CONFIG_PLOTLY = {

    responsive: true,

    displaylogo: false,

    modeBarButtonsToRemove: [
        "lasso2d",
        "select2d"
    ]
};


const LAYOUT_BASE = {

    paper_bgcolor: "#ffffff",

    plot_bgcolor: "#ffffff",

    font: {

        family:
            "Segoe UI, Arial, sans-serif",

        color:
            "#536174"
    },

    margin: {

        l: 55,

        r: 20,

        t: 15,

        b: 55
    },

    hovermode:
        "x unified",

    xaxis: {

        gridcolor:
            "#edf1f6",

        zerolinecolor:
            "#edf1f6"
    },

    yaxis: {

        gridcolor:
            "#edf1f6",

        zerolinecolor:
            "#edf1f6"
    }
};


/* ==========================================================
   CONVERTIR VALOR
   ========================================================== */

function numero(valor) {

    if (
        valor === null ||
        valor === undefined
    ) {

        return 0;
    }

    const n = Number(valor);

    return isNaN(n)
        ? 0
        : n;
}


/* ==========================================================
   AGRUPAR
   ========================================================== */

function agrupar(
    datos,
    campo,
    metrica
) {

    const mapa = {};

    datos.forEach(
        function (fila) {

            const clave =
                String(
                    fila[campo] ?? "Sin dato"
                );

            const valor =
                numero(
                    fila[metrica]
                );

            if (
                !mapa[clave]
            ) {

                mapa[clave] = 0;
            }

            mapa[clave] += valor;

        }
    );

    return Object.entries(
        mapa
    );
}


/* ==========================================================
   CREAR FILTROS
   ========================================================== */

function crearFiltros() {

    const contenedor =
        document.getElementById(
            "filtersGrid"
        );

    contenedor.innerHTML = "";

    FILTROS.forEach(
        function (filtro) {

            const grupo =
                document.createElement(
                    "div"
                );

            grupo.className =
                "filter-group";

            const label =
                document.createElement(
                    "label"
                );

            label.textContent =
                filtro.campo;

            const select =
                document.createElement(
                    "select"
                );

            select.dataset.campo =
                filtro.campo;

            const todos =
                document.createElement(
                    "option"
                );

            todos.value = "";

            todos.textContent =
                "Todos";

            select.appendChild(
                todos
            );

            filtro.valores.forEach(
                function (valor) {

                    const option =
                        document.createElement(
                            "option"
                        );

                    option.value =
                        valor;

                    option.textContent =
                        valor;

                    select.appendChild(
                        option
                    );
                }
            );

            select.addEventListener(
                "change",
                aplicarFiltros
            );

            grupo.appendChild(
                label
            );

            grupo.appendChild(
                select
            );

            contenedor.appendChild(
                grupo
            );

        }
    );
}


/* ==========================================================
   APLICAR FILTROS
   ========================================================== */

function aplicarFiltros() {

    const selects =
        document.querySelectorAll(
            "#filtersGrid select"
        );

    const activos = {};

    selects.forEach(
        function (select) {

            if (select.value) {

                activos[
                    select.dataset.campo
                ] = select.value;

            }

        }
    );

    datosFiltrados =
        DATOS.filter(
            function (fila) {

                return Object.entries(
                    activos
                ).every(
                    function ([campo, valor]) {

                        return String(
                            fila[campo]
                        ) === valor;

                    }
                );

            }
        );

    actualizarDashboard();
}


/* ==========================================================
   RESET
   ========================================================== */

document
    .getElementById(
        "btnReset"
    )
    .addEventListener(
        "click",
        function () {

            document
                .querySelectorAll(
                    "#filtersGrid select"
                )
                .forEach(
                    function (select) {

                        select.value = "";

                    }
                );

            datosFiltrados =
                [...DATOS];

            actualizarDashboard();

        }
    );


/* ==========================================================
   KPIs
   ========================================================== */

function generarKPIs() {
    const contenedor =
        document.getElementById("kpiGrid");

    contenedor.innerHTML = "";

    const metricasDisponibles =
        METRICAS.length
            ? METRICAS
            : (METRICA ? [METRICA] : []);

    metricasDisponibles
        .slice(0, 4)
        .forEach(function(campo) {
            const total =
                datosFiltrados.reduce(
                    function(suma, fila) {
                        return suma +
                            numero(
                                fila[campo]
                            );
                    },
                    0
                );

            const card =
                document.createElement("div");

            card.className =
                "kpi-card";

            card.innerHTML = `
                <div class="kpi-label">
                    ${tituloCampo(campo)}
                </div>
                <div class="kpi-value">
                    ${formatoNumero(total)}
                </div>
                <div class="kpi-detail">
                    Total calculado sobre los datos filtrados
                </div>
            `;

            contenedor.appendChild(card);
        });
}

/* ==========================================================
   GRÁFICOS DINÁMICOS SEGÚN PLANNER
   ========================================================== */

function tituloCampo(campo) {
    if (!campo) return "";
    return String(campo)
        .replace(/_/g, " ")
        .replace(/\s+/g, " ")
        .trim();
}

function crearTarjetaGrafico(indice, elemento) {
    const grid = document.getElementById("chartsGrid");

    const card = document.createElement("div");
    card.className = "chart-card";

    const titulo = document.createElement("div");
    titulo.className = "chart-title";
    titulo.textContent =
        elemento.titulo ||
        (
            tituloCampo(
                elemento.eje_y ||
                elemento.valor ||
                elemento.metrica ||
                METRICA
            ) +
            (
                elemento.eje_x
                    ? " por " + tituloCampo(elemento.eje_x)
                    : ""
            )
        ) ||
        "Visualización";

    const subtitulo = document.createElement("div");
    subtitulo.className = "chart-subtitle";
    subtitulo.textContent =
        elemento.tipo
            ? "Tipo: " + elemento.tipo
            : "Visualización generada automáticamente";

    const chart = document.createElement("div");
    chart.className = "chart";
    chart.id = "chartDynamic_" + indice;

    card.appendChild(titulo);
    card.appendChild(subtitulo);
    card.appendChild(chart);
    grid.appendChild(card);

    return chart;
}

function agruparTriple(datos, campoX, campoY, metrica) {
    const mapa = {};

    datos.forEach(function(fila) {
        const x = String(fila[campoX] ?? "Sin dato");
        const y = String(fila[campoY] ?? "Sin dato");
        const clave = x + "|||" + y;

        if (!mapa[clave]) {
            mapa[clave] = 0;
        }

        mapa[clave] += numero(fila[metrica]);
    });

    return Object.entries(mapa).map(function(par) {
        const partes = par[0].split("|||");
        return {
            x: partes[0],
            y: partes[1],
            valor: par[1]
        };
    });
}

function renderBarAgrupado(
    contenedor,
    campoX,
    agrupacion,
    metrica
) {
    const mapa = {};

    datosFiltrados.forEach(function(fila) {
        const x = String(fila[campoX] ?? "Sin dato");
        const grupo = String(fila[agrupacion] ?? "Sin dato");

        if (!mapa[grupo]) {
            mapa[grupo] = {};
        }

        if (!mapa[grupo][x]) {
            mapa[grupo][x] = 0;
        }

        mapa[grupo][x] += numero(fila[metrica]);
    });

    const categorias = [
        ...new Set(
            Object.values(mapa)
                .flatMap(function(obj) {
                    return Object.keys(obj);
                })
        )
    ].slice(0, 20);

    const traces = Object.keys(mapa).map(function(grupo) {
        return {
            x: categorias,
            y: categorias.map(function(categoria) {
                return mapa[grupo][categoria] || 0;
            }),
            type: "bar",
            name: grupo
        };
    });

    Plotly.react(
        contenedor,
        traces,
        {
            ...LAYOUT_BASE,
            barmode: "group",
            xaxis: {
                automargin: true,
                tickangle: -30
            },
            yaxis: {
                title: metrica,
                tickformat: ",.2s"
            }
        },
        CONFIG_PLOTLY
    );
}

function renderGrafico(elemento, contenedor) {
    if (!elemento || !contenedor) return;

    const tipo = String(
        elemento.tipo || "bar"
    ).toLowerCase();

    const campoX =
        elemento.eje_x ||
        elemento.dimension ||
        elemento.campo;

    const campoY =
        elemento.eje_y ||
        elemento.metrica ||
        elemento.valor ||
        METRICA;

    const agrupacion =
        elemento.agrupacion;

    if (
        tipo === "kpi" ||
        tipo === "table"
    ) {
        return;
    }

    if (
        tipo === "heatmap"
    ) {
        const ejeX = elemento.eje_x;
        const ejeY = elemento.eje_y;
        const valor = elemento.valor || METRICA;

        if (!ejeX || !ejeY || !valor) {
            contenedor.innerHTML =
                "<p style='padding:20px'>No hay campos suficientes para el mapa.</p>";
            return;
        }

        const filas = agruparTriple(
            datosFiltrados,
            ejeX,
            ejeY,
            valor
        );

        const xValues = [
            ...new Set(
                filas.map(function(item) {
                    return item.x;
                })
            )
        ];

        const yValues = [
            ...new Set(
                filas.map(function(item) {
                    return item.y;
                })
            )
        ];

        const z = yValues.map(function(y) {
            return xValues.map(function(x) {
                const encontrado = filas.find(function(item) {
                    return (
                        item.x === x &&
                        item.y === y
                    );
                });

                return encontrado
                    ? encontrado.valor
                    : 0;
            });
        });

        Plotly.react(
            contenedor,
            [{
                x: xValues,
                y: yValues,
                z: z,
                type: "heatmap",
                hovertemplate:
                    ejeX + ": %{x}<br>" +
                    ejeY + ": %{y}<br>" +
                    valor + ": %{z:,.0f}" +
                    "<extra></extra>"
            }],
            {
                ...LAYOUT_BASE,
                xaxis: {
                    automargin: true
                },
                yaxis: {
                    automargin: true
                }
            },
            CONFIG_PLOTLY
        );

        return;
    }

    if (!campoX) {
        contenedor.innerHTML =
            "<p style='padding:20px'>No existe una dimensión para esta visualización.</p>";
        return;
    }

    if (
        tipo === "line" &&
        (!FECHAS.length ||
         FECHAS.indexOf(campoX) === -1)
    ) {
        contenedor.innerHTML =
            "<p style='padding:20px'>No se generó tendencia porque no existe un campo temporal válido.</p>";
        return;
    }

    const agrupado = agrupar(
        datosFiltrados,
        campoX,
        campoY
    );

    agrupado.sort(function(a, b) {
        return b[1] - a[1];
    });

    const top = agrupado.slice(0, 20);

    if (
        tipo === "donut" ||
        tipo === "pie"
    ) {
        Plotly.react(
            contenedor,
            [{
                labels: top.map(function(item) {
                    return item[0];
                }),
                values: top.map(function(item) {
                    return item[1];
                }),
                type: "pie",
                hole:
                    tipo === "donut"
                        ? 0.58
                        : 0,
                textinfo: "label+percent",
                hovertemplate:
                    "%{label}<br>" +
                    campoY +
                    ": %{value:,.0f}<br>" +
                    "%{percent}<extra></extra>"
            }],
            {
                ...LAYOUT_BASE,
                showlegend: true,
                legend: {
                    orientation: "h",
                    y: -0.08
                }
            },
            CONFIG_PLOTLY
        );

        return;
    }

    if (tipo === "line") {
        top.sort(function(a, b) {
            return String(a[0]).localeCompare(
                String(b[0]),
                undefined,
                { numeric: true }
            );
        });

        Plotly.react(
            contenedor,
            [{
                x: top.map(function(item) {
                    return item[0];
                }),
                y: top.map(function(item) {
                    return item[1];
                }),
                type: "scatter",
                mode: "lines+markers",
                line: {
                    width: 3,
                    shape: "spline"
                },
                marker: {
                    size: 7
                },
                hovertemplate:
                    "%{x}<br>" +
                    campoY +
                    ": %{y:,.0f}<extra></extra>"
            }],
            {
                ...LAYOUT_BASE,
                showlegend: false
            },
            CONFIG_PLOTLY
        );

        return;
    }

    if (
        agrupacion &&
        agrupacion !== campoX
    ) {
        renderBarAgrupado(
            contenedor,
            campoX,
            agrupacion,
            campoY
        );
        return;
    }

    Plotly.react(
        contenedor,
        [{
            x: top.map(function(item) {
                return item[0];
            }),
            y: top.map(function(item) {
                return item[1];
            }),
            type: "bar",
            hovertemplate:
                "%{x}<br>" +
                campoY +
                ": %{y:,.0f}<extra></extra>"
        }],
        {
            ...LAYOUT_BASE,
            showlegend: false,
            xaxis: {
                automargin: true,
                tickangle: -30
            },
            yaxis: {
                title: campoY,
                tickformat: ",.2s"
            }
        },
        CONFIG_PLOTLY
    );
}

function generarGraficos() {
    const grid =
        document.getElementById("chartsGrid");

    grid.innerHTML = "";

    const elementosGraficos =
        ELEMENTOS.filter(function(elemento) {
            const tipo =
                String(
                    elemento.tipo || ""
                ).toLowerCase();

            return (
                tipo !== "kpi" &&
                tipo !== "table"
            );
        });

    if (elementosGraficos.length) {
        elementosGraficos.forEach(
            function(elemento, indice) {
                const contenedor =
                    crearTarjetaGrafico(
                        indice,
                        elemento
                    );

                renderGrafico(
                    elemento,
                    contenedor
                );
            }
        );

        return;
    }

    // Fallback mínimo: solamente si el Planner no entregó
    // elementos visuales. Nunca crea una tendencia sin fechas.
    if (
        DIMENSIONES.length &&
        METRICA
    ) {
        const elemento = {
            tipo: "bar",
            eje_x: DIMENSIONES[0],
            eje_y: METRICA,
            titulo:
                tituloCampo(METRICA) +
                " por " +
                tituloCampo(DIMENSIONES[0])
        };

        const contenedor =
            crearTarjetaGrafico(
                0,
                elemento
            );

        renderGrafico(
            elemento,
            contenedor
        );
    }
}

/* ==========================================================
   TABLA
   ========================================================== */

function generarTabla() {

    const head =
        document.getElementById(
            "tableHead"
        );

    const body =
        document.getElementById(
            "tableBody"
        );

    const info =
        document.getElementById(
            "tableInfo"
        );

    head.innerHTML = "";

    body.innerHTML = "";

    const filaHead =
        document.createElement(
            "tr"
        );

    const columnasTabla =
        [...DIMENSIONES, ...METRICAS]
            .filter(function(valor, indice, arreglo) {
                return (
                    valor &&
                    arreglo.indexOf(valor) === indice
                );
            });

    const columnasMostrar =
        columnasTabla.length
            ? columnasTabla
            : COLUMNAS;

    columnasMostrar.forEach(
        function (columna) {

            const th =
                document.createElement(
                    "th"
                );

            th.textContent =
                columna;

            filaHead.appendChild(
                th
            );

        }
    );

    head.appendChild(
        filaHead
    );


    /*
     * Mostramos máximo 100 registros
     * en la vista inicial.
     */

    const filas =
        datosFiltrados.slice(
            0,
            100
        );

    filas.forEach(
        function (fila) {

            const tr =
                document.createElement(
                    "tr"
                );

            const columnasTabla =
        [...DIMENSIONES, ...METRICAS]
            .filter(function(valor, indice, arreglo) {
                return (
                    valor &&
                    arreglo.indexOf(valor) === indice
                );
            });

    const columnasMostrar =
        columnasTabla.length
            ? columnasTabla
            : COLUMNAS;

    columnasMostrar.forEach(
                function (columna) {

                    const td =
                        document.createElement(
                            "td"
                        );

                    const valor =
                        fila[columna];

                    if (
                        typeof valor ===
                        "number"
                    ) {

                        td.textContent =
                            valor.toLocaleString(
                                "es-PE",
                                {
                                    maximumFractionDigits: 2
                                }
                            );

                    }
                    else {

                        td.textContent =
                            valor ?? "";

                    }

                    tr.appendChild(
                        td
                    );

                }
            );

            body.appendChild(
                tr
            );

        }
    );

    info.textContent =
        "Mostrando " +
        filas.length +
        " de " +
        datosFiltrados.length +
        " registros";
}


/* ==========================================================
   ACTUALIZAR TODO
   ========================================================== */

function actualizarDashboard() {

    generarKPIs();

    generarGraficos();

    generarTabla();
}


/* ==========================================================
   INICIO
   ========================================================== */

document.addEventListener(
    "DOMContentLoaded",
    function () {

        crearFiltros();

        actualizarDashboard();

    }
);

</script>

</body>

</html>
"""

        # ----------------------------------------------------
        # RESOLVER PLACEHOLDERS DEL HTML
        # ----------------------------------------------------
        # Se usa replace() en lugar de un f-string para que las llaves
        # del JavaScript/CSS no sean interpretadas por Python.
        html_documento = (
            html_documento
            .replace("__DASH_TITLE__", html.escape(str(titulo)))
            .replace("__DASH_CSS__", self._generar_css())
            .replace("__DASH_MOTOR__", html.escape(str(motor or "")))
            .replace("__DASH_SCHEMA__", html.escape(str(esquema or "")))
            .replace("__DASH_OBJECT__", html.escape(str(objeto or "")))
            .replace("__DASH_NUMBER_JS__", self._numero_js())
            .replace("__DASH_DATA__", datos_json)
            .replace("__DASH_COLUMNS__", columnas_json)
            .replace("__DASH_DIMENSIONS__", dimensiones_json)
            .replace("__DASH_DATES__", fechas_json)
            .replace(
                "__DASH_METRIC__",
                metrica_json
            )
            .replace(
                "__DASH_METRICS__",
                json.dumps(
                    metricas,
                    ensure_ascii=False
                )
            )
            .replace(
                "__DASH_ELEMENTS__",
                elementos_json
            )
            .replace("__DASH_FILTERS__", filtros_json)
        )

        # ----------------------------------------------------
        # ESCRIBIR
        # ----------------------------------------------------

        with open(
            ruta_archivo,
            "w",
            encoding="utf-8"
        ) as archivo:

            archivo.write(
                html_documento
            )

        tiempo = round(
            time.time() - inicio,
            2
        )

        print(
            "[DASHBOARD BUILDER] "
            f"Archivo: {ruta_archivo}"
        )

        print(
            "[DASHBOARD BUILDER] "
            f"Tiempo: {tiempo}s"
        )

        print(
            "======================================================================"
        )

        print(
            "[DASHBOARD BUILDER] FIN"
        )

        print(
            "======================================================================"
        )

        return {

            "estado":
                "ok",

            "titulo":
                titulo,

            "archivo":
                ruta_archivo,

            "nombre_archivo":
                nombre_archivo,

            "graficos":
                len(
                    [
                        e for e in elementos
                        if isinstance(e, dict)
                        and str(
                            e.get("tipo", "")
                        ).lower()
                        not in ("kpi", "table")
                    ]
                ),

            "kpis":
                min(
                    4,
                    1 + len(dimensiones[:3])
                ),

            "filtros":
                len(filtros),

            "filas":
                len(df),

            "columnas":
                len(df.columns),

            "tiempo":
                tiempo
        }


# ============================================================
# COMPATIBILIDAD
# ============================================================

DashboardBuilder = DashboardBuilder