/* ============================================================
   NRIPO 035 - GRÁFICOS PLOTLY
   ============================================================ */

(function () {

    "use strict";


    /* ========================================================
       CONFIGURACIÓN PLOTLY
       ======================================================== */

    const PLOTLY_CONFIG = {

        responsive: true,

        displaylogo: false,

        modeBarButtonsToRemove: [
            "lasso2d",
            "select2d"
        ]
    };


    /* ========================================================
       LAYOUT BASE
       ======================================================== */

    const LAYOUT_BASE = {

        paper_bgcolor: "transparent",

        plot_bgcolor: "#ffffff",

        margin: {
            l: 60,
            r: 25,
            t: 30,
            b: 55
        },

        font: {
            family: "Arial, sans-serif",
            size: 11
        },

        xaxis: {

            title: "Período",

            type: "category",

            showgrid: true,

            zeroline: false

        },

        yaxis: {

            title: "Líneas en servicio",

            showgrid: true,

            zeroline: false

        },

        hovermode: "x unified",

        legend: {

            orientation: "h",

            y: 1.08,

            x: 0

        }
    };


    /* ========================================================
       LEER DATOS JSON
       ======================================================== */

    function obtenerDatos(id) {

        const elemento =
            document.getElementById(id);


        if (!elemento) {

            console.warn(
                "No se encontró:",
                id
            );

            return null;
        }


        try {

            const contenido =
                elemento.textContent.trim();


            if (!contenido) {

                console.warn(
                    "El elemento está vacío:",
                    id
                );

                return null;
            }


            return JSON.parse(
                contenido
            );

        } catch (error) {

            console.error(
                "Error leyendo JSON:",
                id,
                error
            );

            return null;
        }
    }


    /* ========================================================
       VALIDAR DATOS
       ======================================================== */

    function tieneDatos(datos) {

        return (

            datos &&

            Array.isArray(
                datos.periodos
            ) &&

            datos.periodos.length > 0

        );
    }


    /* ========================================================
       MENSAJE SIN DATOS
       ======================================================== */

    function mostrarSinDatos(id) {

        const contenedor =
            document.getElementById(id);


        if (!contenedor) {

            return;
        }


        contenedor.innerHTML = `

            <div class="nripo035-empty">

                <div class="nripo035-empty-icon">

                    <i class="fa-solid fa-chart-line"></i>

                </div>

                <strong>
                    Sin datos disponibles
                </strong>

                <span>
                    No existen datos para mostrar.
                </span>

            </div>

        `;
    }


    /* ========================================================
       FORMATEAR PERÍODO
       ======================================================== */

    function formatearPeriodo(periodo) {

        if (!periodo) {

            return "--";
        }


        const partes =
            String(periodo).split("-");


        if (partes.length !== 2) {

            return periodo;
        }


        const anio =
            partes[0];


        const mes =
            Number(partes[1]);


        const meses = [

            "ENE",
            "FEB",
            "MAR",
            "ABR",
            "MAY",
            "JUN",
            "JUL",
            "AGO",
            "SEP",
            "OCT",
            "NOV",
            "DIC"

        ];


        if (
            mes < 1 ||
            mes > 12
        ) {

            return periodo;
        }


        return (
            meses[mes - 1] +
            " " +
            anio
        );
    }


    /* ========================================================
       ACTUALIZAR KPIs
       ======================================================== */

    function actualizarKPIs(datos) {

        if (!tieneDatos(datos)) {

            return;
        }


        /*
         * IMPORTANTE:
         *
         * El backend entrega:
         *
         * lineas_servicio
         *
         * NO lineas_035
         */

        const periodos =
            datos.periodos || [];


        const valores =
            (datos.lineas_servicio || [])
            .map(Number);


        if (
            !periodos.length ||
            !valores.length
        ) {

            return;
        }


        /* ----------------------------------------------------
           ÚLTIMO PERÍODO
           ---------------------------------------------------- */

        const ultimoPeriodo =
            periodos[
                periodos.length - 1
            ];


        /* ----------------------------------------------------
           ÚLTIMO VALOR
           ---------------------------------------------------- */

        const ultimoValor =
            valores[
                valores.length - 1
            ];


        /* ----------------------------------------------------
           VALOR ANTERIOR
           ---------------------------------------------------- */

        const valorAnterior =
            valores.length > 1
                ? valores[
                    valores.length - 2
                ]
                : null;


        /* ----------------------------------------------------
           VARIACIÓN
           ---------------------------------------------------- */

        let variacion = null;


        if (
            valorAnterior !== null &&
            valorAnterior !== 0
        ) {

            variacion =

                (
                    (
                        ultimoValor -
                        valorAnterior
                    )
                    /
                    valorAnterior
                )
                *
                100;
        }


        /* ----------------------------------------------------
           TENDENCIA
           ---------------------------------------------------- */

        let tendencia =
            "Estable";


        let claseTendencia =
            "estable";


        let iconoTendencia =
            "fa-minus";


        if (
            valorAnterior !== null
        ) {

            if (
                ultimoValor >
                valorAnterior
            ) {

                tendencia =
                    "Ascendente";


                claseTendencia =
                    "ascendente";


                iconoTendencia =
                    "fa-arrow-trend-up";

            }

            else if (
                ultimoValor <
                valorAnterior
            ) {

                tendencia =
                    "Descendente";


                claseTendencia =
                    "descendente";


                iconoTendencia =
                    "fa-arrow-trend-down";
            }
        }


        /* ----------------------------------------------------
           ELEMENTOS
           ---------------------------------------------------- */

        const kpiPeriodo =
            document.getElementById(
                "kpi-periodo"
            );


        const kpiServicio =
            document.getElementById(
                "kpi-servicio"
            );


        const kpiVariacion =
            document.getElementById(
                "kpi-variacion"
            );


        const kpiTendencia =
            document.getElementById(
                "kpi-tendencia"
            );


        /* ----------------------------------------------------
           PERÍODO
           ---------------------------------------------------- */

        if (kpiPeriodo) {

            kpiPeriodo.textContent =
                formatearPeriodo(
                    ultimoPeriodo
                );
        }


        /* ----------------------------------------------------
           LÍNEAS EN SERVICIO
           ---------------------------------------------------- */

        if (kpiServicio) {

            kpiServicio.textContent =

                ultimoValor.toFixed(3) +
                " M";
        }


        /* ----------------------------------------------------
           VARIACIÓN
           ---------------------------------------------------- */

        if (kpiVariacion) {

            if (
                variacion !== null
            ) {

                const signo =
                    variacion > 0
                        ? "+"
                        : "";


                kpiVariacion.textContent =

                    signo +
                    variacion.toFixed(2) +
                    "%";

            }

            else {

                kpiVariacion.textContent =
                    "--";
            }
        }


        /* ----------------------------------------------------
           TENDENCIA
           ---------------------------------------------------- */

        if (kpiTendencia) {

            kpiTendencia.innerHTML = `

                <span
                    class="nripo035-tendencia ${claseTendencia}"
                >

                    <i
                        class="fa-solid ${iconoTendencia}"
                    ></i>

                    ${tendencia}

                </span>

            `;
        }


        console.log(
            "KPIs NRIPO 035 actualizados:",
            {

                periodo:
                    ultimoPeriodo,

                valor:
                    ultimoValor,

                variacion:
                    variacion,

                tendencia:
                    tendencia

            }
        );
    }


    /* ========================================================
       GRÁFICO PRINCIPAL NRIPO 035
       ======================================================== */

    function crearGrafico035(datos) {

        const id =
            "grafico-nripo-035";


        if (!tieneDatos(datos)) {

            mostrarSinDatos(id);

            return;
        }


        /*
         * CAMPOS REALES DEL BACKEND:
         *
         * periodos
         * lineas_servicio
         * lineas_3_meses
         * diferencia
         * porcentaje_diferencia
         */

        const periodos =
            datos.periodos || [];


        const lineasServicio =
            (datos.lineas_servicio || [])
            .map(Number);


        const lineas3Meses =
            (datos.lineas_3_meses || [])
            .map(Number);


        if (
            !lineasServicio.length
        ) {

            mostrarSinDatos(id);

            return;
        }


        /* ----------------------------------------------------
           TRAZA PRINCIPAL
           ---------------------------------------------------- */

        const traceServicio = {

            x:
                periodos,

            y:
                lineasServicio,

            type:
                "scatter",

            mode:
                "lines+markers",

            name:
                "Líneas en servicio",

            line: {

                width: 3,

                shape: "spline"
            },

            marker: {

                size: 6
            },

            hovertemplate:

                "<b>%{x}</b><br>" +

                "Líneas en servicio: " +

                "%{y:.3f} M" +

                "<extra></extra>"
        };


        /* ----------------------------------------------------
           TRAZA 3 MESES
           ---------------------------------------------------- */

        const traces = [

            traceServicio

        ];


        /*
         * Si existe la serie de 3 meses,
         * la mostramos como segunda línea.
         */

        if (
            lineas3Meses.length ===
            periodos.length
        ) {

            traces.push({

                x:
                    periodos,

                y:
                    lineas3Meses,

                type:
                    "scatter",

                mode:
                    "lines",

                name:
                    "Promedio 3 meses",

                line: {

                    width: 2,

                    dash: "dash"
                },

                hovertemplate:

                    "<b>%{x}</b><br>" +

                    "Promedio 3 meses: " +

                    "%{y:.3f} M" +

                    "<extra></extra>"
            });
        }


        /* ----------------------------------------------------
           ESCALA Y
           ---------------------------------------------------- */

        const todosLosValores =

            lineasServicio.concat(
                lineas3Meses
            )
            .filter(
                valor =>
                    Number.isFinite(valor)
            );


        const minimo =
            Math.min(
                ...todosLosValores
            );


        const maximo =
            Math.max(
                ...todosLosValores
            );


        let margen =

            (maximo - minimo) *
            0.15;


        if (
            margen === 0 ||
            !Number.isFinite(margen)
        ) {

            margen =
                Math.abs(maximo) *
                0.05;
        }


        /* ----------------------------------------------------
           LAYOUT
           ---------------------------------------------------- */

        const layout = {

            ...LAYOUT_BASE,

            height:
                320,

            title: {

                text: ""

            },

            yaxis: {

                ...LAYOUT_BASE.yaxis,

                title:
                    "Líneas en servicio (millones)",

                range: [

                    Math.max(
                        0,
                        minimo - margen
                    ),

                    maximo + margen
                ],

                tickformat:
                    ".1f"
            },

            xaxis: {

                ...LAYOUT_BASE.xaxis,

                title:
                    "Período"
            },

            legend: {

                orientation:
                    "h",

                y:
                    1.08,

                x:
                    0
            }
        };


        Plotly.newPlot(

            id,

            traces,

            layout,

            PLOTLY_CONFIG
        );
    }


    /* ========================================================
       NRIPO 033 VS NRIPO 035
       ======================================================== */

    function crearGrafico033035(datos) {

        const id =
            "grafico-033-035";


        if (!tieneDatos(datos)) {

            mostrarSinDatos(id);

            return;
        }


        const trace033 = {

            x:
                datos.periodos,

            y:
                datos.nripo_033
                .map(Number),

            type:
                "scatter",

            mode:
                "lines+markers",

            name:
                "NRIPO 033",

            line: {

                width: 2
            },

            marker: {

                size: 5
            },

            hovertemplate:

                "<b>%{x}</b><br>" +

                "NRIPO 033: " +

                "%{y:.3f}" +

                "<extra></extra>"
        };


        const trace035 = {

            x:
                datos.periodos,

            y:
                datos.lineas_035
                .map(Number),

            type:
                "scatter",

            mode:
                "lines+markers",

            name:
                "NRIPO 035",

            line: {

                width: 2
            },

            marker: {

                size: 5
            },

            hovertemplate:

                "<b>%{x}</b><br>" +

                "NRIPO 035: " +

                "%{y:.3f}" +

                "<extra></extra>"
        };


        const layout = {

            ...LAYOUT_BASE,

            height:
                280,

            title: {

                text:
                    ""
            }
        };


        Plotly.newPlot(

            id,

            [
                trace033,
                trace035
            ],

            layout,

            PLOTLY_CONFIG
        );
    }


    /* ========================================================
       NRIPO 034 VS NRIPO 035
       ======================================================== */

    function crearGrafico034035(datos) {

        const id =
            "grafico-034-035";


        if (!tieneDatos(datos)) {

            mostrarSinDatos(id);

            return;
        }


        const trace034 = {

            x:
                datos.periodos,

            y:
                datos.nripo_034
                .map(Number),

            type:
                "scatter",

            mode:
                "lines+markers",

            name:
                "NRIPO 034",

            line: {

                width: 2
            },

            marker: {

                size: 5
            },

            hovertemplate:

                "<b>%{x}</b><br>" +

                "NRIPO 034: " +

                "%{y:.3f}" +

                "<extra></extra>"
        };


        const trace035 = {

            x:
                datos.periodos,

            y:
                datos.lineas_3_meses
                .map(Number),

            type:
                "scatter",

            mode:
                "lines+markers",

            name:
                "NRIPO 035",

            line: {

                width: 2
            },

            marker: {

                size: 5
            },

            hovertemplate:

                "<b>%{x}</b><br>" +

                "NRIPO 035: " +

                "%{y:.3f}" +

                "<extra></extra>"
        };


        const layout = {

            ...LAYOUT_BASE,

            height:
                280,

            title: {

                text:
                    ""
            }
        };


        Plotly.newPlot(

            id,

            [
                trace034,
                trace035
            ],

            layout,

            PLOTLY_CONFIG
        );
    }


    /* ========================================================
       REDIMENSIONAR
       ======================================================== */

    function redimensionarGraficos() {

        const ids = [

            "grafico-nripo-035",

            "grafico-033-035",

            "grafico-034-035"

        ];


        ids.forEach(

            function (id) {

                const elemento =
                    document.getElementById(id);


                if (
                    elemento &&
                    elemento.classList.contains(
                        "js-plotly-plot"
                    )
                ) {

                    try {

                        Plotly.Plots.resize(
                            elemento
                        );

                    }

                    catch (error) {

                        console.warn(

                            "No se pudo redimensionar:",

                            id,

                            error
                        );
                    }
                }
            }
        );
    }


    /* ========================================================
       INICIALIZACIÓN
       ======================================================== */

    function inicializarNRIPO035() {

        console.log(
            "Inicializando gráficos NRIPO 035..."
        );


        const datos035 =
            obtenerDatos(
                "datos-nripo-035"
            );


        const datos033035 =
            obtenerDatos(
                "datos-nripo-033-035"
            );


        const datos034035 =
            obtenerDatos(
                "datos-nripo-034-035"
            );


        console.log(
            "Datos NRIPO 035:",
            datos035
        );


        console.log(
            "Datos NRIPO 033 vs 035:",
            datos033035
        );


        console.log(
            "Datos NRIPO 034 vs 035:",
            datos034035
        );


        /* ----------------------------------------------------
           KPIs
           ---------------------------------------------------- */

        actualizarKPIs(
            datos035
        );


        /* ----------------------------------------------------
           GRÁFICO PRINCIPAL
           ---------------------------------------------------- */

        crearGrafico035(
            datos035
        );


        /* ----------------------------------------------------
           COMPARATIVO 033 / 035
           ---------------------------------------------------- */

        crearGrafico033035(
            datos033035
        );


        /* ----------------------------------------------------
           COMPARATIVO 034 / 035
           ---------------------------------------------------- */

        crearGrafico034035(
            datos034035
        );


        /* ----------------------------------------------------
           REDIMENSIONAR
           ---------------------------------------------------- */

        setTimeout(
            redimensionarGraficos,
            150
        );
    }


    /* ========================================================
       EXPONER FUNCIÓN GLOBAL
       ======================================================== */

    window.inicializarNRIPO035 =
        inicializarNRIPO035;


})();