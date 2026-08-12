/* ============================================================
   TENDENCIAS DE PLANTAS
   Planta Comercial vs Planta Control BI
   Planta MTC
   ============================================================ */

(function () {

    "use strict";

    console.log("📊 tendencias_plantas.js cargado");


    /* =========================================================
       CONFIGURACIÓN
       ========================================================= */

    const COLORES = {

        ADSL: "#F59E0B",

        FTTH: "#2563EB",

        HFC: "#16A34A"

    };


    const ORDEN_TECNOLOGIAS = [

        "ADSL",

        "FTTH",

        "HFC"

    ];


    let opcionesPlanta = null;


    /* =========================================================
       INICIALIZACIÓN
       ========================================================= */

    window.inicializarTendenciasPlantas = function () {

        console.log(
            "🚀 Inicializando Tendencias de Plantas"
        );


        configurarTabs();


        if (window.Plotly) {

            console.log(
                "✅ Plotly disponible"
            );

            cargarOpcionesPlanta();

        }

        else {

            console.warn(
                "⚠️ Plotly todavía no está disponible"
            );


            cargarPlotly(
                function () {

                    cargarOpcionesPlanta();

                }
            );

        }

    };


    /* =========================================================
       CARGAR PLOTLY
       ========================================================= */

    function cargarPlotly(callback) {

        if (window.Plotly) {

            callback();

            return;

        }


        const script =
            document.createElement("script");


        script.src =
            "https://cdn.plot.ly/plotly-2.35.2.min.js";


        script.onload = function () {

            console.log(
                "✅ Plotly cargado"
            );


            callback();

        };


        script.onerror = function () {

            console.error(
                "❌ No se pudo cargar Plotly"
            );

        };


        document.head.appendChild(script);

    }


    /* =========================================================
       PESTAÑAS
       ========================================================= */

    function configurarTabs() {

        const tabs =
            document.querySelectorAll(
                ".tendencia-tab"
            );


        if (!tabs.length) {

            return;

        }


        tabs.forEach(
            tab => {

                tab.addEventListener(
                    "click",
                    function () {

                        const panelId =
                            this.getAttribute(
                                "data-panel"
                            );


                        /*
                         * Si el botón tiene data-panel,
                         * usamos ese valor.
                         *
                         * Si no lo tiene, obtenemos
                         * el panel desde onclick o texto.
                         */

                        if (panelId) {

                            activarPanel(
                                this,
                                panelId
                            );

                        }

                    }
                );

            }
        );

    }


    /* =========================================================
       CAMBIAR TENDENCIA
       
       Esta función es utilizada directamente
       por el onclick del HTML:
       
       onclick="cambiarTendencia(this, 'planta-mtc')"
       ========================================================= */

    window.cambiarTendencia = function (
        boton,
        panelId
    ) {

        console.log(
            "📌 Cambiando tendencia:",
            panelId
        );


        activarPanel(
            boton,
            panelId
        );

    };


    /* =========================================================
       ACTIVAR PANEL
       ========================================================= */

    function activarPanel(
        boton,
        panelId
    ) {

        /*
         * ACTIVAR BOTÓN
         */

        const tabs =
            document.querySelectorAll(
                ".tendencia-tab"
            );


        tabs.forEach(
            tab => {

                tab.classList.remove(
                    "active"
                );

            }
        );


        if (boton) {

            boton.classList.add(
                "active"
            );

        }


        /*
         * OCULTAR PANELES
         */

        const paneles =
            document.querySelectorAll(
                ".tendencia-panel"
            );


        paneles.forEach(
            panel => {

                panel.classList.remove(
                    "active"
                );

            }
        );


        /*
         * MOSTRAR PANEL SELECCIONADO
         */

        const panel =
            document.getElementById(
                panelId
            );


        if (!panel) {

            console.warn(
                "⚠️ No existe el panel:",
                panelId
            );

            return;

        }


        panel.classList.add(
            "active"
        );


        /*
         * PLANTA CONTROL
         */

        if (
            panelId === "planta-control"
        ) {

            console.log(
                "🏢 Panel Planta Control"
            );


            /*
             * Si todavía no existen
             * los gráficos, cargarlos.
             */

            const grafico1 =
                document.getElementById(
                    "grafico1"
                );


            if (
                grafico1 &&
                !grafico1.children.length
            ) {

                actualizarGraficos();

            }

        }


        /*
         * PLANTA MTC
         */

        if (
            panelId === "planta-mtc"
        ) {

            console.log(
                "🏛️ Panel Planta MTC"
            );


            cargarPlantaMTC();

        }
        /*
 * TRÁFICO ACUMULADO
 */

if (
    panelId === "planta-trfacu"
) {

    console.log(
        "📈 Panel Tráfico Acumulado"
    );

    cargarPlantaTrfaCu();

}
/*
 * USUA MTC
 */

if (
    panelId === "planta-usua-mtc"
) {

    console.log(
        "👥 Panel USUA MTC"
    );

    cargarPlantaUsuaMTC();

}
/*
 * PLANTA TISA
 */

if (
    panelId === "planta-tisa"
) {

    console.log(
        "🌱 Panel Planta TISA"
    );

    cargarPlantaTisa();

}
    }


    /* =========================================================
       CARGAR PLANTA MTC
       ========================================================= */

    async function cargarPlantaMTC() {

        const contenedor =
            document.getElementById(
                "planta-mtc-contenido"
            );


        if (!contenedor) {

            console.warn(
                "⚠️ No existe #planta-mtc-contenido"
            );

            return;

        }


        /*
         * Evitar volver a cargar el HTML
         * cada vez que se presiona la pestaña.
         */

        if (
            contenedor.dataset.cargado === "true"
        ) {

            console.log(
                "ℹ️ Planta MTC ya fue cargada"
            );

            return;

        }


        /*
         * LOADING
         */

        contenedor.innerHTML = `

            <div class="planta-mtc-loading">

                <i class="fa-solid fa-spinner fa-spin"></i>

                <span>
                    Cargando Planta MTC...
                </span>

            </div>

        `;


        try {

            console.log(
                "📡 Solicitando /planta_mtc"
            );


            /*
             * IMPORTANTE:
             *
             * Esta es la ruta que debe devolver
             * el contenido de planta_mtc.html
             */

            const response =
                await fetch(
                    "/planta_mtc"
                );


            console.log(
                "📡 Planta MTC HTTP:",
                response.status
            );


            if (!response.ok) {

                throw new Error(
                    "HTTP " +
                    response.status
                );

            }


            const html =
                await response.text();


            /*
             * INSERTAR HTML
             */

            contenedor.innerHTML =
                html;


            contenedor.dataset.cargado =
                "true";


            console.log(
                "✅ Planta MTC cargada correctamente"
            );

        }

        catch (error) {

            console.error(
                "❌ Error cargando Planta MTC:",
                error
            );


            contenedor.innerHTML = `

                <div class="grafico-error">

                    <div class="grafico-error-icon">
                        ⚠️
                    </div>

                    <strong>
                        No se pudo cargar Planta MTC
                    </strong>

                    <span>
                        Verifique que exista la ruta
                        /planta_mtc.
                    </span>

                </div>

            `;

        }

    }
    /* =========================================================
   CARGAR TRÁFICO ACUMULADO
   ========================================================= */

async function cargarPlantaTrfaCu() {

    const contenedor =
        document.getElementById(
            "planta-trfacu-contenido"
        );


    if (!contenedor) {

        console.warn(
            "⚠️ No existe #planta-trfacu-contenido"
        );

        return;

    }


    /*
     * Evitar volver a cargar
     * cada vez que se presiona la pestaña.
     */

    if (
        contenedor.dataset.cargado === "true"
    ) {

        console.log(
            "ℹ️ Tráfico Acumulado ya fue cargado"
        );

        return;

    }


    /*
     * LOADING
     */

    contenedor.innerHTML = `

        <div class="planta-trfacu-loading">

            <i class="fa-solid fa-spinner fa-spin"></i>

            <span>
                Cargando Tráfico Acumulado...
            </span>

        </div>

    `;


    try {

        console.log(
            "📡 Solicitando /planta_trfacu"
        );


        /*
         * Ruta Flask que debe devolver
         * el contenido de planta_trfacu.html
         */

        const response =
            await fetch(
                "/planta_trfacu"
            );


        console.log(
            "📡 Tráfico Acumulado HTTP:",
            response.status
        );


        if (!response.ok) {

            throw new Error(
                "HTTP " +
                response.status
            );

        }


        const html =
            await response.text();


        /*
         * INSERTAR HTML
         */

        contenedor.innerHTML =
            html;


        contenedor.dataset.cargado =
            "true";


        console.log(
            "✅ Tráfico Acumulado cargado correctamente"
        );

    }

    catch (error) {

        console.error(
            "❌ Error cargando Tráfico Acumulado:",
            error
        );


        contenedor.innerHTML = `

            <div class="grafico-error">

                <div class="grafico-error-icon">
                    ⚠️
                </div>

                <strong>
                    No se pudo cargar Tráfico Acumulado
                </strong>

                <span>
                    Verifique que exista la ruta
                    /planta_trfacu.
                </span>

            </div>

        `;

    }

}
/* =========================================================
   CARGAR USUA MTC
   ========================================================= */

async function cargarPlantaUsuaMTC() {

    const contenedor =
        document.getElementById(
            "planta-usua-mtc-contenido"
        );


    if (!contenedor) {

        console.warn(
            "⚠️ No existe #planta-usua-mtc-contenido"
        );

        return;

    }


    /*
     * Evitar volver a cargar
     * cada vez que se presiona la pestaña.
     */

    if (
        contenedor.dataset.cargado === "true"
    ) {

        console.log(
            "ℹ️ USUA MTC ya fue cargado"
        );

        return;

    }


    /*
     * LOADING
     */

    contenedor.innerHTML = `

        <div class="planta-usua-mtc-loading">

            <i class="fa-solid fa-spinner fa-spin"></i>

            <span>
                Cargando USUA MTC...
            </span>

        </div>

    `;


    try {

        console.log(
            "📡 Solicitando /planta_usua_mtc"
        );


        /*
         * Ruta Flask
         */

        const response =
            await fetch(
                "/planta_usua_mtc"
            );


        console.log(
            "📡 USUA MTC HTTP:",
            response.status
        );


        if (!response.ok) {

            throw new Error(
                "HTTP " +
                response.status
            );

        }


        const html =
            await response.text();


        /*
         * INSERTAR HTML
         */

        contenedor.innerHTML =
            html;


        contenedor.dataset.cargado =
            "true";


        console.log(
            "✅ USUA MTC cargado correctamente"
        );

    }

    catch (error) {

        console.error(
            "❌ Error cargando USUA MTC:",
            error
        );


        contenedor.innerHTML = `

            <div class="grafico-error">

                <div class="grafico-error-icon">
                    ⚠️
                </div>

                <strong>
                    No se pudo cargar USUA MTC
                </strong>

                <span>
                    Verifique que exista la ruta
                    /planta_usua_mtc.
                </span>

            </div>

        `;

    }

}
/* =========================================================
   CARGAR PLANTA TISA
   ========================================================= */

async function cargarPlantaTisa() {

    const contenedor =
        document.getElementById(
            "planta-tisa-contenido"
        );


    if (!contenedor) {

        console.warn(
            "⚠️ No existe #planta-tisa-contenido"
        );

        return;

    }


    /*
     * Evitar volver a cargar
     * cada vez que se presiona la pestaña.
     */

    if (
        contenedor.dataset.cargado === "true"
    ) {

        console.log(
            "ℹ️ Planta TISA ya fue cargada"
        );

        return;

    }


    /*
     * LOADING
     */

    contenedor.innerHTML = `

        <div class="planta-tisa-loading">

            <i class="fa-solid fa-spinner fa-spin"></i>

            <span>
                Cargando Planta TISA...
            </span>

        </div>

    `;


    try {

        console.log(
            "📡 Solicitando /planta_tisa"
        );


        const response =
            await fetch(
                "/planta_tisa"
            );


        console.log(
            "📡 Planta TISA HTTP:",
            response.status
        );


        if (!response.ok) {

            throw new Error(
                "HTTP " +
                response.status
            );

        }


        const html =
            await response.text();


        /*
         * INSERTAR HTML
         */

        contenedor.innerHTML =
            html;


        contenedor.dataset.cargado =
            "true";


        console.log(
            "✅ Planta TISA cargada correctamente"
        );

    }

    catch (error) {

        console.error(
            "❌ Error cargando Planta TISA:",
            error
        );


        contenedor.innerHTML = `

            <div class="grafico-error">

                <div class="grafico-error-icon">
                    ⚠️
                </div>

                <strong>
                    No se pudo cargar Planta TISA
                </strong>

                <span>
                    Verifique que exista la ruta
                    /planta_tisa.
                </span>

            </div>

        `;

    }

}
    /* =========================================================
       OPCIONES DE PLANTA
       ========================================================= */

    async function cargarOpcionesPlanta() {

        try {

            console.log(
                "🔄 Consultando /planta_opciones"
            );


            const response =
                await fetch(
                    "/planta_opciones"
                );


            if (!response.ok) {

                throw new Error(
                    "HTTP " +
                    response.status
                );

            }


            opcionesPlanta =
                await response.json();


            console.log(
                "✅ Opciones recibidas:",
                opcionesPlanta
            );


            configurarFiltros();

        }

        catch (error) {

            console.error(
                "❌ Error cargando opciones:",
                error
            );


            opcionesPlanta = {

                tecnologias: [

                    "TODAS",

                    "ADSL",

                    "FTTH",

                    "HFC"

                ],


                estados: [

                    "ACTIVO"

                ],


                anio_actual:

                    new Date()
                        .getFullYear()
                        .toString()

            };


            configurarFiltros();

        }

    }


    /* =========================================================
       CONFIGURAR FILTROS
       ========================================================= */

    function configurarFiltros() {

        const panel =
            document.getElementById(
                "planta-control"
            );


        if (!panel) {

            console.warn(
                "⚠️ No existe #planta-control"
            );

            return;

        }


        /* =====================================================
           TECNOLOGÍA
           ===================================================== */

        const selectTecnologia =
            panel.querySelector(
                ".filtro-tecnologia"
            );


        if (selectTecnologia) {

            selectTecnologia.innerHTML =
                "";


            const tecnologias =
                opcionesPlanta.tecnologias ||
                [

                    "TODAS",

                    "ADSL",

                    "FTTH",

                    "HFC"

                ];


            tecnologias.forEach(
                tecnologia => {

                    const option =
                        document.createElement(
                            "option"
                        );


                    option.value =
                        tecnologia;


                    option.textContent =
                        tecnologia;


                    if (
                        tecnologia === "TODAS"
                    ) {

                        option.selected =
                            true;

                    }


                    selectTecnologia.appendChild(
                        option
                    );

                }
            );

        }


        /* =====================================================
           ESTADO
           ===================================================== */

        const selectEstado =
            panel.querySelector(
                ".filtro-estado"
            );


        if (selectEstado) {

            selectEstado.innerHTML =
                "";


            const estados =
                opcionesPlanta.estados ||
                [

                    "ACTIVO"

                ];


            estados.forEach(
                estado => {

                    const option =
                        document.createElement(
                            "option"
                        );


                    option.value =
                        estado;


                    option.textContent =
                        estado;


                    if (
                        estado === "ACTIVO"
                    ) {

                        option.selected =
                            true;

                    }


                    selectEstado.appendChild(
                        option
                    );

                }
            );

        }


        /* =====================================================
           PERÍODO
           ===================================================== */

        const periodoActual =
            opcionesPlanta.anio_actual ||
            new Date()
                .getFullYear()
                .toString();


        const inputPeriodo =
            panel.querySelector(
                ".filtro-periodo"
            );


        if (inputPeriodo) {

            inputPeriodo.value =
                periodoActual;

        }


        /* =====================================================
           EVENTOS
           ===================================================== */

        if (selectTecnologia) {

            selectTecnologia.addEventListener(
                "change",
                actualizarGraficos
            );

        }


        if (selectEstado) {

            selectEstado.addEventListener(
                "change",
                actualizarGraficos
            );

        }


        if (inputPeriodo) {

            inputPeriodo.addEventListener(
                "change",
                actualizarGraficos
            );


            inputPeriodo.addEventListener(
                "keyup",
                function (event) {

                    if (
                        event.key === "Enter"
                    ) {

                        actualizarGraficos();

                    }

                }
            );

        }


        /* =====================================================
           BOTÓN APLICAR
           ===================================================== */

        const boton =
            panel.querySelector(
                ".btn-aplicar-filtros"
            );


        if (boton) {

            boton.addEventListener(
                "click",
                function (event) {

                    event.preventDefault();

                    actualizarGraficos();

                }
            );

        }


        /* =====================================================
           PRIMERA CARGA
           ===================================================== */

        actualizarGraficos();

    }


    /* =========================================================
       OBTENER FILTROS
       ========================================================= */

    function obtenerFiltros() {

        const panel =
            document.getElementById(
                "planta-control"
            );


        if (!panel) {

            return {

                tecnologia: "TODAS",

                estado: "ACTIVO",

                periodo:
                    new Date()
                        .getFullYear()
                        .toString()

            };

        }


        const tecnologia =
            panel.querySelector(
                ".filtro-tecnologia"
            )?.value ||
            "TODAS";


        const estado =
            panel.querySelector(
                ".filtro-estado"
            )?.value ||
            "ACTIVO";


        const periodo =
            panel.querySelector(
                ".filtro-periodo"
            )?.value ||
            new Date()
                .getFullYear()
                .toString();


        return {

            tecnologia,

            estado,

            periodo

        };

    }


    /* =========================================================
       ACTUALIZAR GRÁFICOS
       ========================================================= */

    async function actualizarGraficos() {

        const filtros =
            obtenerFiltros();


        console.log(
            "🔎 Filtros:",
            filtros
        );


        const query =
            new URLSearchParams({

                tecnologia:
                    filtros.tecnologia,

                estado:
                    filtros.estado,

                periodo:
                    filtros.periodo

            });


        try {

            mostrarCargando();


            /*
             * MANTENER ESTOS ENDPOINTS
             */

            const [

                respuestaComercial,

                respuestaControl

            ] =
                await Promise.all([

                    fetch(
                        "/planta_datos1?" +
                        query.toString()
                    ),

                    fetch(
                        "/planta_datos2?" +
                        query.toString()
                    )

                ]);


            console.log(
                "📡 Planta Comercial HTTP:",
                respuestaComercial.status
            );


            console.log(
                "📡 Planta Control BI HTTP:",
                respuestaControl.status
            );


            if (!respuestaComercial.ok) {

                throw new Error(
                    "Error Planta Comercial: " +
                    respuestaComercial.status
                );

            }


            if (!respuestaControl.ok) {

                throw new Error(
                    "Error Planta Control BI: " +
                    respuestaControl.status
                );

            }


            const datosComercial =
                await respuestaComercial.json();


            const datosControl =
                await respuestaControl.json();


            console.log(
                "📊 Planta Comercial:",
                datosComercial
            );


            console.log(
                "📊 Planta Control BI:",
                datosControl
            );


            dibujarComparativo(
                datosComercial,
                datosControl
            );

        }

        catch (error) {

            console.error(
                "❌ Error generando gráficos:",
                error
            );


            mostrarError();

        }

    }


    /* =========================================================
       CONTENEDOR DE GRÁFICOS
       ========================================================= */

    function obtenerContenedorComparativo() {

        const selectores = [

            "#comparacion-graficos",

            ".comparacion-graficos",

            "#graficos-comparativos",

            ".graficos-comparativos",

            "#grafico-comparativo",

            ".grafico-comparativo",

            "#grafico1"

        ];


        for (
            const selector of selectores
        ) {

            const elemento =
                document.querySelector(
                    selector
                );


            if (elemento) {

                return elemento;

            }

        }


        console.warn(
            "⚠️ No se encontró contenedor de gráficos"
        );


        return null;

    }


    /* =========================================================
       NORMALIZAR DATOS
       ========================================================= */

    function normalizarDatos(respuesta) {

        if (!respuesta) {

            return [];

        }


        if (
            Array.isArray(respuesta)
        ) {

            return respuesta;

        }


        if (
            Array.isArray(
                respuesta.datos
            )
        ) {

            return respuesta.datos;

        }


        return [];

    }


    /* =========================================================
       AGRUPAR POR TECNOLOGÍA
       ========================================================= */

    function agruparPorTecnologia(datos) {

        const resultado = {};


        datos.forEach(
            item => {

                const tecnologia =
                    String(

                        item.tecnologia ||

                        item.TECNOLOGIA ||

                        ""

                    ).toUpperCase();


                if (!tecnologia) {

                    return;

                }


                if (
                    !resultado[
                        tecnologia
                    ]
                ) {

                    resultado[
                        tecnologia
                    ] = [];

                }


                resultado[
                    tecnologia
                ].push(item);

            }
        );


        return resultado;

    }


    /* =========================================================
       DIBUJAR COMPARATIVO
       ========================================================= */

    function dibujarComparativo(

        respuestaComercial,

        respuestaControl

    ) {

        const contenedor =
            obtenerContenedorComparativo();


        if (!contenedor) {

            return;

        }


        const datosComercial =
            normalizarDatos(
                respuestaComercial
            );


        const datosControl =
            normalizarDatos(
                respuestaControl
            );


        console.log(
            "📊 Registros Comercial:",
            datosComercial.length
        );


        console.log(
            "📊 Registros Control BI:",
            datosControl.length
        );


        const comercialPorTecnologia =
            agruparPorTecnologia(
                datosComercial
            );


        const controlPorTecnologia =
            agruparPorTecnologia(
                datosControl
            );


        /* =====================================================
           TECNOLOGÍAS
           ===================================================== */

        let tecnologias = [];


        ORDEN_TECNOLOGIAS.forEach(
            tecnologia => {

                if (

                    comercialPorTecnologia[
                        tecnologia
                    ] ||

                    controlPorTecnologia[
                        tecnologia
                    ]

                ) {

                    tecnologias.push(
                        tecnologia
                    );

                }

            }
        );


        const adicionales = [

            ...Object.keys(
                comercialPorTecnologia
            ),

            ...Object.keys(
                controlPorTecnologia
            )

        ];


        adicionales.forEach(
            tecnologia => {

                if (
                    !tecnologias.includes(
                        tecnologia
                    )
                ) {

                    tecnologias.push(
                        tecnologia
                    );

                }

            }
        );


        if (!tecnologias.length) {

            contenedor.innerHTML = `

                <div class="grafico-sin-datos">

                    <strong>
                        Sin datos disponibles
                    </strong>

                    <span>
                        No existen datos para
                        los filtros seleccionados.
                    </span>

                </div>

            `;

            return;

        }


        /* =====================================================
           LIMPIAR
           ===================================================== */

        contenedor.innerHTML = "";


        /* =====================================================
           CREAR GRÁFICOS
           ===================================================== */

        tecnologias.forEach(
            tecnologia => {

                crearComparativoTecnologia(

                    contenedor,

                    tecnologia,

                    comercialPorTecnologia[
                        tecnologia
                    ] || [],

                    controlPorTecnologia[
                        tecnologia
                    ] || []

                );

            }
        );

    }


    /* =========================================================
       CREAR GRÁFICO POR TECNOLOGÍA
       ========================================================= */

    function crearComparativoTecnologia(

        contenedor,

        tecnologia,

        datosComercial,

        datosControl

    ) {

        /* =====================================================
           CARD
           ===================================================== */

        const card =
            document.createElement(
                "div"
            );


        card.className =
            "grafico-tecnologia-card";


        card.setAttribute(
            "data-tecnologia",
            tecnologia
        );


        /* =====================================================
           CABECERA
           ===================================================== */

        const header =
            document.createElement(
                "div"
            );


        header.className =
            "grafico-tecnologia-header";


        const color =
            COLORES[
                tecnologia
            ] ||
            "#64748B";


        header.innerHTML = `

            <div
                class="tecnologia-titulo"
                style="
                    display:flex;
                    align-items:center;
                    gap:8px;
                "
            >

                <span
                    class="tecnologia-indicador"
                    style="
                        background:${color};
                        width:8px;
                        height:8px;
                        border-radius:50%;
                        display:inline-block;
                    "
                ></span>

                <strong>
                    ${tecnologia}
                </strong>

            </div>

        `;


        card.appendChild(
            header
        );


        /* =====================================================
           CONTENEDOR PLOTLY
           ===================================================== */

        const grafico =
            document.createElement(
                "div"
            );


        grafico.className =
            "grafico-tecnologia";


        card.appendChild(
            grafico
        );


        contenedor.appendChild(
            card
        );


        /* =====================================================
           ORDENAR DATOS
           ===================================================== */

        const comercial =
            ordenarDatos(
                datosComercial
            );


        const control =
            ordenarDatos(
                datosControl
            );


        /* =====================================================
           PERIODOS
           ===================================================== */

        const periodos = [

            ...new Set([

                ...comercial.map(
                    item =>
                        obtenerPeriodo(item)
                ),

                ...control.map(
                    item =>
                        obtenerPeriodo(item)
                )

            ])

        ].filter(
            periodo =>
                periodo !== ""
        );


        periodos.sort(
            (a, b) => {

                return String(a)
                    .localeCompare(
                        String(b)
                    );

            }
        );


        /* =====================================================
           MAPA COMERCIAL
           ===================================================== */

        const mapaComercial =
            new Map();


        comercial.forEach(
            item => {

                mapaComercial.set(

                    obtenerPeriodo(item),

                    obtenerCantidad(item)

                );

            }
        );


        /* =====================================================
           MAPA CONTROL
           ===================================================== */

        const mapaControl =
            new Map();


        control.forEach(
            item => {

                mapaControl.set(

                    obtenerPeriodo(item),

                    obtenerCantidad(item)

                );

            }
        );


        /* =====================================================
           EJE X
           ===================================================== */

        const x =
            periodos.map(
                periodo => {

                    return obtenerPeriodoLabel(

                        periodo,

                        comercial,

                        control

                    );

                }
            );


        /* =====================================================
           VALORES
           ===================================================== */

        const yComercial =
            periodos.map(
                periodo => {

                    return mapaComercial.has(
                        periodo
                    )

                        ? mapaComercial.get(
                            periodo
                        )

                        : null;

                }
            );


        const yControl =
            periodos.map(
                periodo => {

                    return mapaControl.has(
                        periodo
                    )

                        ? mapaControl.get(
                            periodo
                        )

                        : null;

                }
            );


        if (!periodos.length) {

            grafico.innerHTML = `

                <div class="grafico-sin-datos">

                    <strong>
                        Sin datos
                    </strong>

                </div>

            `;

            return;

        }


        /* =====================================================
           ESCALA Y
           ===================================================== */

        const todosValores = [

            ...yComercial.filter(
                valor =>
                    valor !== null &&
                    Number.isFinite(valor)
            ),

            ...yControl.filter(
                valor =>
                    valor !== null &&
                    Number.isFinite(valor)
            )

        ];


        let yMin =
            Math.min(
                ...todosValores
            );


        let yMax =
            Math.max(
                ...todosValores
            );


        if (
            !Number.isFinite(yMin) ||
            !Number.isFinite(yMax)
        ) {

            yMin = 0;

            yMax = 1;

        }


        if (
            yMin === yMax
        ) {

            const margen =
                Math.max(
                    Math.abs(yMax) * 0.10,
                    0.01
                );


            yMin =
                Math.max(
                    0,
                    yMin - margen
                );


            yMax =
                yMax + margen;

        }

        else {

            const margen =
                (yMax - yMin) * 0.10;


            yMin =
                Math.max(
                    0,
                    yMin - margen
                );


            yMax =
                yMax + margen;

        }


        /* =====================================================
           PLANTA CONTROL BI
           ===================================================== */

        const traceControl = {

            x: x,

            y: yControl,

            type: "scatter",

            mode: "lines+markers",

            name: "Planta Control BI",

            connectgaps: false,

            line: {

                color: "#64748B",

                width: 3,

                dash: "dash"

            },

            marker: {

                color: "#64748B",

                size: 7,

                symbol: "circle",

                line: {

                    color: "#FFFFFF",

                    width: 1

                }

            },

            hovertemplate:

                "<b>" +
                tecnologia +
                "</b><br>" +

                "Planta Control BI<br>" +

                "Período: %{x}<br>" +

                "Cantidad: %{y:.3f} M" +

                "<extra></extra>"

        };


        /* =====================================================
           PLANTA COMERCIAL
           ===================================================== */

        const traceComercial = {

            x: x,

            y: yComercial,

            type: "scatter",

            mode: "lines+markers",

            name: "Planta Comercial",

            connectgaps: false,

            line: {

                color: color,

                width: 3,

                dash: "solid"

            },

            marker: {

                color: color,

                size: 7,

                symbol: "circle",

                line: {

                    color: "#FFFFFF",

                    width: 1

                }

            },

            hovertemplate:

                "<b>" +
                tecnologia +
                "</b><br>" +

                "Planta Comercial<br>" +

                "Período: %{x}<br>" +

                "Cantidad: %{y:.3f} M" +

                "<extra></extra>"

        };


        /* =====================================================
           LAYOUT
           ===================================================== */

        const layout = {

            height: 225,

            margin: {

                l: 68,

                r: 18,

                t: 48,

                b: 48

            },

            paper_bgcolor:
                "#FFFFFF",

            plot_bgcolor:
                "#FFFFFF",

            font: {

                family:
                    "Segoe UI, Arial, sans-serif",

                color:
                    "#334155",

                size: 11

            },

            title: {

                text: ""

            },

            xaxis: {

                title: {

                    text: "Período",

                    font: {

                        size: 10,

                        color: "#475569"

                    }

                },

                showgrid: true,

                gridcolor:
                    "#E2E8F0",

                gridwidth: 1,

                zeroline: false,

                tickangle: 0,

                tickfont: {

                    size: 10,

                    color: "#475569"

                },

                automargin: true,

                fixedrange: false,

                showline: false

            },

            yaxis: {

                title: {

                    text:
                        "Cantidad (Millones)",

                    font: {

                        size: 10,

                        color: "#475569"

                    }

                },

                range: [

                    yMin,

                    yMax

                ],

                showgrid: true,

                gridcolor:
                    "#E2E8F0",

                gridwidth: 1,

                zeroline: false,

                tickformat:
                    ".3f",

                tickfont: {

                    size: 10,

                    color: "#475569"

                },

                automargin: true

            },

            legend: {

                orientation:
                    "h",

                x: 0,

                y: 1.10,

                xanchor:
                    "left",

                yanchor:
                    "bottom",

                font: {

                    size: 10,

                    color: "#475569"

                },

                bgcolor:
                    "rgba(255,255,255,0.90)"

            },

            hovermode:
                "x unified"

        };


        /* =====================================================
           CONFIGURACIÓN PLOTLY
           ===================================================== */

        const config = {

            responsive: true,

            displaylogo: false,

            displayModeBar: false,

            scrollZoom: false

        };


        /* =====================================================
           PINTAR
           ===================================================== */

        try {

            Plotly.newPlot(

                grafico,

                [

                    traceControl,

                    traceComercial

                ],

                layout,

                config

            );


            console.log(

                "✅ Comparativo creado:",

                tecnologia

            );

        }

        catch (error) {

            console.error(
                "❌ Error Plotly:",
                error
            );


            mostrarErrorContenedor(
                grafico
            );

        }

    }


    /* =========================================================
       ORDENAR DATOS
       ========================================================= */

    function ordenarDatos(datos) {

        return [...datos].sort(
            (a, b) => {

                return String(

                    a.periodo ||

                    a.PERIODO ||

                    a.periodo_codigo ||

                    ""

                ).localeCompare(

                    String(

                        b.periodo ||

                        b.PERIODO ||

                        b.periodo_codigo ||

                        ""

                    )

                );

            }
        );

    }


    /* =========================================================
       OBTENER PERÍODO
       ========================================================= */

    function obtenerPeriodo(item) {

        return String(

            item.periodo ||

            item.PERIODO ||

            item.periodo_codigo ||

            ""

        );

    }


    /* =========================================================
       OBTENER LABEL
       ========================================================= */

    function obtenerPeriodoLabel(

        periodo,

        datos1,

        datos2

    ) {

        const todos = [

            ...datos1,

            ...datos2

        ];


        const encontrado =
            todos.find(
                item =>
                    obtenerPeriodo(item) ===
                    periodo
            );


        if (encontrado) {

            return (

                encontrado.periodo_label ||

                encontrado.PERIODO_LABEL ||

                encontrado.periodo ||

                encontrado.PERIODO ||

                periodo

            );

        }


        return periodo;

    }


    /* =========================================================
       OBTENER CANTIDAD
       ========================================================= */

    function obtenerCantidad(item) {

        const valor = Number(

            item.cantidad ??

            item.CANTIDAD ??

            item.valor ??

            item.VALOR

        );


        if (
            Number.isFinite(valor)
        ) {

            return valor;

        }


        return null;

    }


    /* =========================================================
       CARGANDO
       ========================================================= */

    function mostrarCargando() {

        console.log(
            "⏳ Cargando gráficos..."
        );

    }


    /* =========================================================
       ERROR
       ========================================================= */

    function mostrarError() {

        const contenedor =
            obtenerContenedorComparativo();


        if (!contenedor) {

            return;

        }


        mostrarErrorContenedor(
            contenedor
        );

    }


    /* =========================================================
       ERROR CONTENEDOR
       ========================================================= */

    function mostrarErrorContenedor(
        contenedor
    ) {

        contenedor.innerHTML = `

            <div class="grafico-error">

                <div
                    class="grafico-error-icon"
                >
                    ⚠️
                </div>

                <strong>
                    No se pudo generar el gráfico
                </strong>

                <span>
                    Verifique los filtros
                    seleccionados.
                </span>

            </div>

        `;

    }


    /* =========================================================
       INICIALIZACIÓN AUTOMÁTICA
       ========================================================= */

    setTimeout(
        function () {

            if (
                document.getElementById(
                    "planta-control"
                )
            ) {

                inicializarTendenciasPlantas();

            }

        },
        100
    );


})();