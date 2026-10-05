// ============================================================
// IA OBSERVABILIDAD - UNIVERSO 3D
// ============================================================

import ForceGraph3D from
    "https://cdn.jsdelivr.net/npm/3d-force-graph@1.79.0/+esm";

import * as THREE from
    "https://cdn.jsdelivr.net/npm/three@0.179.1/+esm";


// ============================================================
// VARIABLES GLOBALES
// ============================================================

let Graph = null;

let graphData = {
    nodes: [],
    links: []
};

let selectedNode = null;

let searchText = "";

let filtroProceso = "";

let periodoActual = "202606";

let posiciones = new Map();

let objetosAnimados = [];

let ultimoTimestamp = null;


// ============================================================
// COLORES
// ============================================================

const STATUS_COLORS = {

    OK: "#22e58a",

    ERROR: "#ff315f",

    WARNING: "#ffc857",

    RUNNING: "#28a9ff",

    UNKNOWN: "#8b98a8"

};


const TYPE_COLORS = {

    PROCESS: "#22e58a",

    INPUT: "#28a9ff",

    REPORT: "#ffc857"

};


// ============================================================
// ELEMENTOS HTML
// ============================================================

const container =
    document.getElementById("graph-container");

const searchInput =
    document.getElementById("search-input");

const procesoSelect =
    document.getElementById("proceso-filter");

const periodoInput =
    document.getElementById("periodo-filter");


// ============================================================
// UTILIDADES
// ============================================================

function safeText(value) {

    if (
        value === null ||
        value === undefined
    ) {
        return "";
    }

    return String(value);
}


// ============================================================
// NORMALIZAR ESTADO
// ============================================================

function normalizarStatus(status) {

    if (!status) {
        return "UNKNOWN";
    }

    const value =
        String(status)
            .trim()
            .toUpperCase();


    if (
        value === "OK" ||
        value === "EXITO" ||
        value === "SUCCESS" ||
        value === "COMPLETADO"
    ) {

        return "OK";

    }


    if (
        value === "ERROR" ||
        value === "CANCELADO" ||
        value === "CANCEL" ||
        value === "FAILED" ||
        value === "FAIL" ||
        value === "FALLA" ||
        value === "FALLIDO" ||
        value === "NOK"
    ) {

        return "ERROR";

    }


    if (
        value === "WARNING" ||
        value === "WARN" ||
        value === "PENDIENTE" ||
        value === "ATRASADO"
    ) {

        return "WARNING";

    }


    if (
        value === "RUNNING" ||
        value === "EJECUTANDO" ||
        value === "EN EJECUCION"
    ) {

        return "RUNNING";

    }


    return "UNKNOWN";
}


// ============================================================
// COLOR DEL ESTADO
// ============================================================

function getStatusColor(status) {

    return (
        STATUS_COLORS[
            normalizarStatus(status)
        ] ||
        STATUS_COLORS.UNKNOWN
    );

}


// ============================================================
// POSICIÓN DE PROCESOS
// ============================================================

function generarPosicionProceso(index, total) {

    const columnas = 7;

    const fila =
        Math.floor(
            index / columnas
        );

    const columna =
        index % columnas;

    const totalFilas =
        Math.ceil(
            total / columnas
        );


    const separacionX = 230;

    const separacionY = 180;


    const offsetX =
        (
            columna -
            (columnas - 1) / 2
        ) *
        separacionX;


    const offsetY =
        (
            fila -
            (totalFilas - 1) / 2
        ) *
        separacionY;


    const offsetZ =
        (
            (index % 5) - 2
        ) *
        75;


    return {

        x: offsetX,

        y: offsetY,

        z: offsetZ

    };

}


// ============================================================
// POSICIÓN INPUT
// ============================================================

function posicionInput(
    processPosition,
    index,
    total
) {

    const angle =
        (
            index /
            Math.max(total, 1)
        ) *
        Math.PI *
        2;


    const radio = 80;


    return {

        x:
            processPosition.x +
            Math.cos(angle) *
            radio,

        y:
            processPosition.y +
            Math.sin(angle) *
            radio,

        z:
            processPosition.z +
            Math.sin(angle * 2) *
            45

    };

}


// ============================================================
// POSICIÓN REPORT
// ============================================================

function posicionReport(processPosition) {

    return {

        x: processPosition.x,

        y: processPosition.y - 100,

        z: processPosition.z + 20

    };

}


// ============================================================
// PREPARAR POSICIONES
// ============================================================

function prepararPosiciones(nodes) {

    const procesos =
        nodes.filter(
            n => n.type === "PROCESS"
        );


    // --------------------------------------------------------
    // PROCESOS
    // --------------------------------------------------------

    procesos.forEach(
        (node, index) => {

            const anterior =
                posiciones.get(
                    node.id
                );


            if (anterior) {

                node.x = anterior.x;

                node.y = anterior.y;

                node.z = anterior.z;

                node.fx = anterior.x;

                node.fy = anterior.y;

                node.fz = anterior.z;

                return;

            }


            const posicion =
                generarPosicionProceso(
                    index,
                    procesos.length
                );


            node.x = posicion.x;

            node.y = posicion.y;

            node.z = posicion.z;

            node.fx = posicion.x;

            node.fy = posicion.y;

            node.fz = posicion.z;


            posiciones.set(
                node.id,
                posicion
            );

        }
    );


    // --------------------------------------------------------
    // INPUTS
    // --------------------------------------------------------

    const inputsPorProceso =
        new Map();


    graphData.links.forEach(
        link => {

            const source =
                typeof link.source === "object"
                    ? link.source
                    : nodes.find(
                        n =>
                            n.id ===
                            link.source
                    );


            const target =
                typeof link.target === "object"
                    ? link.target
                    : nodes.find(
                        n =>
                            n.id ===
                            link.target
                    );


            if (
                !source ||
                !target
            ) {
                return;
            }


            if (
                source.type === "INPUT" &&
                target.type === "PROCESS"
            ) {

                if (
                    !inputsPorProceso.has(
                        target.id
                    )
                ) {

                    inputsPorProceso.set(
                        target.id,
                        []
                    );

                }


                inputsPorProceso
                    .get(target.id)
                    .push(source);

            }

        }
    );


    inputsPorProceso.forEach(
        (inputs, processId) => {

            const process =
                nodes.find(
                    n =>
                        n.id ===
                        processId
                );


            if (!process) {
                return;
            }


            inputs.forEach(
                (input, index) => {

                    const anterior =
                        posiciones.get(
                            input.id
                        );


                    if (anterior) {

                        input.x =
                            anterior.x;

                        input.y =
                            anterior.y;

                        input.z =
                            anterior.z;

                        input.fx =
                            anterior.x;

                        input.fy =
                            anterior.y;

                        input.fz =
                            anterior.z;

                        return;

                    }


                    const pos =
                        posicionInput(
                            process,
                            index,
                            inputs.length
                        );


                    input.x = pos.x;

                    input.y = pos.y;

                    input.z = pos.z;

                    input.fx = pos.x;

                    input.fy = pos.y;

                    input.fz = pos.z;


                    posiciones.set(
                        input.id,
                        pos
                    );

                }
            );

        }
    );


    // --------------------------------------------------------
    // REPORTES
    // --------------------------------------------------------

    nodes
        .filter(
            n =>
                n.type === "REPORT"
        )
        .forEach(
            report => {

                const process =
                    nodes.find(
                        n =>
                            n.type ===
                            "PROCESS" &&

                            safeText(
                                n.name
                            ).toUpperCase() ===

                            safeText(
                                report.name
                            ).toUpperCase()
                    );


                if (!process) {
                    return;
                }


                const anterior =
                    posiciones.get(
                        report.id
                    );


                if (anterior) {

                    report.x =
                        anterior.x;

                    report.y =
                        anterior.y;

                    report.z =
                        anterior.z;

                    report.fx =
                        anterior.x;

                    report.fy =
                        anterior.y;

                    report.fz =
                        anterior.z;

                    return;

                }


                const pos =
                    posicionReport(
                        process
                    );


                report.x = pos.x;

                report.y = pos.y;

                report.z = pos.z;

                report.fx = pos.x;

                report.fy = pos.y;

                report.fz = pos.z;


                posiciones.set(
                    report.id,
                    pos
                );

            }
        );

}


// ============================================================
// CREAR OBJETO 3D DEL NODO
// ============================================================

function crearNodo3D(node) {

    const group =
        new THREE.Group();


    const status =
        normalizarStatus(
            node.status
        );


    const color =
        getStatusColor(
            status
        );


    // ========================================================
    // PROCESS
    // ========================================================

    if (
        node.type === "PROCESS"
    ) {

        const radius = 19;


        const geometry =
            new THREE.SphereGeometry(
                radius,
                32,
                32
            );


        const material =
            new THREE.MeshStandardMaterial({

                color: color,

                emissive: color,

                emissiveIntensity: 0.45,

                metalness: 0.45,

                roughness: 0.28

            });


        const sphere =
            new THREE.Mesh(
                geometry,
                material
            );


        group.add(
            sphere
        );


        // ----------------------------------------------------
        // GLOW
        // ----------------------------------------------------

        const glowGeometry =
            new THREE.SphereGeometry(
                radius * 1.45,
                24,
                24
            );


        const glowMaterial =
            new THREE.MeshBasicMaterial({

                color: color,

                transparent: true,

                opacity: 0.09,

                depthWrite: false

            });


        const glow =
            new THREE.Mesh(
                glowGeometry,
                glowMaterial
            );


        group.add(
            glow
        );


        // ----------------------------------------------------
        // RING
        // ----------------------------------------------------

        const ringGeometry =
            new THREE.TorusGeometry(
                radius * 1.35,
                1.5,
                10,
                64
            );


        const ringMaterial =
            new THREE.MeshBasicMaterial({

                color: color,

                transparent: true,

                opacity: 0.8

            });


        const ring =
            new THREE.Mesh(
                ringGeometry,
                ringMaterial
            );


        ring.rotation.x =
            Math.PI / 2;


        group.add(
            ring
        );


        // ----------------------------------------------------
        // SEGUNDO RING
        // ----------------------------------------------------

        const ring2Geometry =
            new THREE.TorusGeometry(
                radius * 1.65,
                0.7,
                8,
                64
            );


        const ring2Material =
            new THREE.MeshBasicMaterial({

                color: color,

                transparent: true,

                opacity: 0.35

            });


        const ring2 =
            new THREE.Mesh(
                ring2Geometry,
                ring2Material
            );


        ring2.rotation.y =
            Math.PI / 3;


        group.add(
            ring2
        );


        objetosAnimados.push({

            object: ring,

            speed: 0.004

        });


        objetosAnimados.push({

            object: ring2,

            speed: -0.0025

        });

    }


    // ========================================================
    // INPUT
    // ========================================================

    else if (
        node.type === "INPUT"
    ) {

        const size = 14;


        const geometry =
            new THREE.BoxGeometry(
                size,
                size,
                size
            );


        const material =
            new THREE.MeshStandardMaterial({

                color: color,

                emissive: color,

                emissiveIntensity: 0.25,

                metalness: 0.5,

                roughness: 0.35

            });


        const cube =
            new THREE.Mesh(
                geometry,
                material
            );


        cube.rotation.y =
            Math.PI / 4;


        group.add(
            cube
        );


        // ----------------------------------------------------
        // GLOW
        // ----------------------------------------------------

        const glowGeometry =
            new THREE.BoxGeometry(
                size * 1.35,
                size * 1.35,
                size * 1.35
            );


        const glowMaterial =
            new THREE.MeshBasicMaterial({

                color: color,

                transparent: true,

                opacity: 0.06,

                depthWrite: false

            });


        const glow =
            new THREE.Mesh(
                glowGeometry,
                glowMaterial
            );


        glow.rotation.y =
            Math.PI / 4;


        group.add(
            glow
        );

    }


    // ========================================================
    // REPORT
    // ========================================================

    else if (
        node.type === "REPORT"
    ) {

        const geometry =
            new THREE.CylinderGeometry(
                12,
                12,
                20,
                24
            );


        const material =
            new THREE.MeshStandardMaterial({

                color: color,

                emissive: color,

                emissiveIntensity: 0.25,

                metalness: 0.5,

                roughness: 0.35

            });


        const cylinder =
            new THREE.Mesh(
                geometry,
                material
            );


        group.add(
            cylinder
        );


        const ringGeometry =
            new THREE.TorusGeometry(
                15,
                1,
                8,
                32
            );


        const ringMaterial =
            new THREE.MeshBasicMaterial({

                color: color,

                transparent: true,

                opacity: 0.35

            });


        const ring =
            new THREE.Mesh(
                ringGeometry,
                ringMaterial
            );


        ring.rotation.x =
            Math.PI / 2;


        group.add(
            ring
        );

    }


    // ========================================================
    // SELECCIÓN
    // ========================================================

    if (
        selectedNode &&
        selectedNode.id === node.id
    ) {

        const selectionGeometry =
            new THREE.TorusGeometry(
                27,
                1.8,
                10,
                64
            );


        const selectionMaterial =
            new THREE.MeshBasicMaterial({

                color: "#ffffff",

                transparent: true,

                opacity: 0.9

            });


        const selection =
            new THREE.Mesh(
                selectionGeometry,
                selectionMaterial
            );


        selection.rotation.x =
            Math.PI / 2;


        group.add(
            selection
        );

    }


    return group;

}


// ============================================================
// LABEL DEL NODO
// ============================================================

function obtenerLabel(node) {

    const status =
        normalizarStatus(
            node.status
        );


    const color =
        getStatusColor(
            status
        );


    return `

        <div style="
            padding:8px 11px;
            border:1px solid ${color};
            background:rgba(3,10,18,.94);
            border-radius:7px;
            color:#fff;
            font-family:Arial,sans-serif;
            min-width:150px;
            box-shadow:0 0 15px ${color}33;
        ">

            <div style="
                font-size:10px;
                color:${color};
                font-weight:bold;
                letter-spacing:1px;
            ">

                ${safeText(node.type)}

            </div>


            <div style="
                font-size:13px;
                font-weight:bold;
                margin-top:3px;
            ">

                ${safeText(node.name)}

            </div>


            <div style="
                font-size:10px;
                margin-top:5px;
                color:${color};
            ">

                ● ${status}

            </div>

        </div>

    `;

}


// ============================================================
// BUSQUEDA
// ============================================================

function nodoCoincideBusqueda(node) {

    if (!searchText) {
        return true;
    }


    const texto = (

        safeText(node.name) +

        " " +

        safeText(node.type) +

        " " +

        safeText(node.status)

    ).toUpperCase();


    return texto.includes(
        searchText.toUpperCase()
    );

}


// ============================================================
// VISIBILIDAD NODO
// ============================================================

function nodoVisible(node) {

    if (
        !nodoCoincideBusqueda(node)
    ) {

        return false;

    }


    return true;

}


// ============================================================
// VISIBILIDAD LINKS
// ============================================================

function linkVisible(link) {

    const source =
        typeof link.source === "object"

            ? link.source

            : graphData.nodes.find(
                n =>
                    n.id ===
                    link.source
            );


    const target =
        typeof link.target === "object"

            ? link.target

            : graphData.nodes.find(
                n =>
                    n.id ===
                    link.target
            );


    if (
        !source ||
        !target
    ) {

        return false;

    }


    return (

        nodoVisible(source) &&

        nodoVisible(target)

    );

}


// ============================================================
// COLOR LINKS
// ============================================================

function colorLink(link) {

    const source =
        typeof link.source === "object"

            ? link.source

            : null;


    const target =
        typeof link.target === "object"

            ? link.target

            : null;


    // --------------------------------------------------------
    // LINK SELECCIONADO
    // --------------------------------------------------------

    if (

        selectedNode &&

        (

            (
                source &&
                source.id ===
                selectedNode.id
            )

            ||

            (
                target &&
                target.id ===
                selectedNode.id
            )

        )

    ) {

        return "#ffffff";

    }


    // --------------------------------------------------------
    // ERROR
    // --------------------------------------------------------

    if (

        source &&

        normalizarStatus(
            source.status
        ) === "ERROR"

    ) {

        return "#ff315f";

    }


    return "rgba(60,175,220,.30)";

}


// ============================================================
// ANCHO LINKS
// ============================================================

function anchoLink(link) {

    const source =
        typeof link.source === "object"

            ? link.source

            : null;


    const target =
        typeof link.target === "object"

            ? link.target

            : null;


    if (

        selectedNode &&

        (

            (
                source &&
                source.id ===
                selectedNode.id
            )

            ||

            (
                target &&
                target.id ===
                selectedNode.id
            )

        )

    ) {

        return 3;

    }


    if (

        source &&

        normalizarStatus(
            source.status
        ) === "ERROR"

    ) {

        return 2.5;

    }


    return 0.8;

}


// ============================================================
// CENTRAR TODO EL UNIVERSO
// ============================================================

function centrarUniverso(
    duracion = 900,
    padding = 35
) {

    if (
        !Graph ||
        !container ||
        !graphData.nodes ||
        !graphData.nodes.length
    ) {
        return;
    }

    const ejecutar = () => {

        if (
            !Graph ||
            !container ||
            !graphData.nodes.length
        ) {
            return;
        }

        const width = container.clientWidth;
        const height = container.clientHeight;

        // Evita hacer fit mientras el layout todavía
        // está calculando sus dimensiones.
        if (width < 300 || height < 250) {
            return;
        }

        Graph.width(width);
        Graph.height(height);

        /*
         * zoomToFit calcula el centro real del bounding box
         * visible. Un padding pequeño hace que el universo
         * quede más grande y aprovechable dentro del panel.
         */
        Graph.zoomToFit(
            duracion,
            padding,
            node => nodoVisible(node)
        );
    };

    /*
     * Esperamos a que CSS Grid + Three.js hayan terminado
     * de calcular el tamaño final del panel.
     */
    requestAnimationFrame(() => {
        requestAnimationFrame(() => {
            setTimeout(ejecutar, 120);
        });
    });
}


// ============================================================
// INICIALIZAR GRAPH
// ============================================================

function inicializarGraph() {

    Graph =
        ForceGraph3D({

            // ------------------------------------------------
            // TRACKBALL = MOVIMIENTO TIPO MANO
            // ------------------------------------------------

            controlType: "trackball",

            rendererConfig: {

                antialias: true,

                alpha: true

            }

        })(container);


    Graph

        .backgroundColor(
            "rgba(0,0,0,0)"
        )

        .showNavInfo(false)

        .nodeThreeObject(
            node =>
                crearNodo3D(node)
        )

        .nodeThreeObjectExtend(false)

        .nodeLabel(
            node =>
                obtenerLabel(node)
        )

        .nodeVisibility(
            node =>
                nodoVisible(node)
        )

        .linkVisibility(
            link =>
                linkVisible(link)
        )

        .linkColor(
            link =>
                colorLink(link)
        )

        .linkWidth(
            link =>
                anchoLink(link)
        )

        .linkOpacity(
            0.55
        )

        .linkDirectionalParticles(
            3
        )

        .linkDirectionalParticleWidth(
            1.5
        )

        .linkDirectionalParticleSpeed(
            0.003
        );


    // ========================================================
    // NAVEGACIÓN
    // ========================================================

    Graph.enableNodeDrag(false);

    Graph.enableNavigationControls(true);

    Graph.showPointerCursor(true);


    // ========================================================
    // FORCES
    // ========================================================

    const charge =
        Graph.d3Force(
            "charge"
        );


    if (charge) {

        charge.strength(
            -20
        );

    }


    const linkForce =
        Graph.d3Force(
            "link"
        );


    if (linkForce) {

        linkForce.distance(
            100
        );

    }


    // ========================================================
    // EVITAR MOVIMIENTO AUTOMÁTICO
    // ========================================================

    Graph

        .warmupTicks(1)

        .cooldownTicks(1)

        .cooldownTime(1);


    // ========================================================
    // CLICK NODO
    // ========================================================

    Graph.onNodeClick(
        node =>
            seleccionarNodo(node)
    );


    // ========================================================
    // CLICK FONDO
    // ========================================================

    Graph.onBackgroundClick(
        () =>
            limpiarSeleccion()
    );


    // ========================================================
    // HOVER
    // ========================================================

    Graph.onNodeHover(
        node => {

            container.style.cursor =
                node
                    ? "pointer"
                    : "grab";

        }
    );


    container.style.cursor =
        "grab";


    // ========================================================
    // DOBLE CLICK EN FONDO = CENTRAR
    // ========================================================

    container.addEventListener(
        "dblclick",
        event => {

            // Si el doble click fue sobre
            // el canvas pero no sobre un nodo,
            // centramos el universo.

            if (
                event.target.tagName ===
                "CANVAS"
            ) {

                centrarUniverso(
                    800,
                    100
                );

            }

        }
    );

}


// ============================================================
// SELECCIONAR NODO
// ============================================================

function seleccionarNodo(node) {

    selectedNode = node;


    mostrarDetalle(
        node
    );


    Graph.nodeThreeObject(
        n =>
            crearNodo3D(n)
    );


    Graph.linkColor(
        link =>
            colorLink(link)
    );


    Graph.linkWidth(
        link =>
            anchoLink(link)
    );

}


// ============================================================
// LIMPIAR SELECCIÓN
// ============================================================

function limpiarSeleccion() {

    selectedNode = null;


    ocultarDetalle();


    if (!Graph) {
        return;
    }


    Graph.nodeThreeObject(
        node =>
            crearNodo3D(node)
    );


    Graph.linkColor(
        link =>
            colorLink(link)
    );


    Graph.linkWidth(
        link =>
            anchoLink(link)
    );

}


// ============================================================
// DETALLE - DISEÑO MODERNO
// ============================================================

function inyectarEstilosDetalle() {

    if (document.getElementById("detail-modern-styles")) {
        return;
    }

    const style = document.createElement("style");
    style.id = "detail-modern-styles";

    style.textContent = `
        #node-detail .detail-modern {
            display:flex;
            flex-direction:column;
            gap:16px;
            height:100%;
            overflow-y:auto;
            padding:2px 1px 8px 1px;
            box-sizing:border-box;
        }

        #node-detail .detail-modern::-webkit-scrollbar {
            width:4px;
        }

        #node-detail .detail-modern::-webkit-scrollbar-thumb {
            background:rgba(40,169,255,.28);
            border-radius:10px;
        }

        #node-detail .detail-top {
            display:flex;
            align-items:center;
            justify-content:space-between;
            gap:12px;
        }

        #node-detail .detail-identity {
            min-width:0;
        }

        #node-detail .detail-kicker {
            font-size:9px;
            letter-spacing:1.6px;
            color:#6f9ab2;
            font-weight:700;
            margin-bottom:5px;
        }

        #node-detail .detail-name {
            font-size:22px;
            line-height:1.08;
            font-weight:800;
            color:#f3f8fc;
            letter-spacing:.2px;
            word-break:break-word;
        }

        #node-detail .detail-subtitle {
            margin-top:5px;
            color:#6f8798;
            font-size:10px;
            letter-spacing:.7px;
        }

        #node-detail .detail-status-modern {
            flex:none;
            display:inline-flex;
            align-items:center;
            gap:6px;
            padding:6px 10px;
            border:1px solid;
            border-radius:999px;
            font-size:9px;
            font-weight:800;
            letter-spacing:1px;
            background:rgba(3,12,21,.72);
            white-space:nowrap;
        }

        #node-detail .detail-section {
            border-top:1px solid rgba(50,137,177,.20);
            padding-top:13px;
        }

        #node-detail .detail-section-title {
            display:flex;
            align-items:center;
            gap:7px;
            margin-bottom:10px;
            color:#6f9ab2;
            font-size:9px;
            font-weight:800;
            letter-spacing:1.4px;
        }

        #node-detail .detail-section-title::before {
            content:"";
            width:3px;
            height:11px;
            border-radius:3px;
            background:#28a9ff;
            box-shadow:0 0 8px rgba(40,169,255,.45);
        }

        #node-detail .detail-grid-modern {
            display:grid;
            grid-template-columns:1fr 1fr;
            gap:8px;
        }

        #node-detail .detail-card {
            min-width:0;
            padding:11px 10px;
            border:1px solid rgba(39,117,154,.24);
            border-radius:9px;
            background:linear-gradient(
                135deg,
                rgba(7,25,38,.72),
                rgba(3,13,22,.82)
            );
        }

        #node-detail .detail-card-label {
            display:block;
            margin-bottom:6px;
            color:#587487;
            font-size:8px;
            font-weight:700;
            letter-spacing:1.2px;
        }

        #node-detail .detail-card-value {
            display:block;
            color:#e9f3f8;
            font-size:12px;
            line-height:1.25;
            font-weight:700;
            overflow-wrap:anywhere;
        }

        #node-detail .detail-card-value.muted {
            color:#778b99;
            font-weight:500;
        }

        #node-detail .detail-code {
            padding:12px;
            border:1px solid rgba(39,117,154,.25);
            border-radius:9px;
            background:rgba(2,11,19,.72);
            color:#bfe8ff;
            font-family:Consolas, "Courier New", monospace;
            font-size:11px;
            line-height:1.45;
            overflow-wrap:anywhere;
        }

        #node-detail .detail-state {
            display:flex;
            align-items:center;
            gap:10px;
            padding:11px 12px;
            border:1px solid rgba(39,117,154,.24);
            border-radius:9px;
            background:rgba(4,17,28,.72);
        }

        #node-detail .detail-state-dot {
            width:8px;
            height:8px;
            border-radius:50%;
            flex:none;
            box-shadow:0 0 10px currentColor;
        }

        #node-detail .detail-state-main {
            min-width:0;
        }

        #node-detail .detail-state-value {
            font-size:12px;
            font-weight:800;
            letter-spacing:.5px;
        }

        #node-detail .detail-state-caption {
            margin-top:3px;
            color:#617b8b;
            font-size:9px;
        }

        #node-detail .detail-insight {
            position:relative;
            padding:12px 12px 12px 14px;
            border:1px solid rgba(40,169,255,.24);
            border-radius:9px;
            background:linear-gradient(
                135deg,
                rgba(9,39,57,.62),
                rgba(3,15,25,.78)
            );
            overflow:hidden;
        }

        #node-detail .detail-insight::before {
            content:"";
            position:absolute;
            left:0;
            top:0;
            bottom:0;
            width:2px;
            background:#28a9ff;
            box-shadow:0 0 12px rgba(40,169,255,.55);
        }

        #node-detail .detail-insight-title {
            color:#28a9ff;
            font-size:9px;
            font-weight:800;
            letter-spacing:1.3px;
            margin-bottom:6px;
        }

        #node-detail .detail-insight-text {
            color:#9ab2c0;
            font-size:10px;
            line-height:1.5;
        }

        @media (max-width: 430px) {
            #node-detail .detail-grid-modern {
                grid-template-columns:1fr;
            }
        }
    `;

    document.head.appendChild(style);
}


function mostrarDetalle(node) {

    const panel =
        document.getElementById(
            "node-detail"
        );

    if (!panel) {
        return;
    }

    inyectarEstilosDetalle();

    const status =
        normalizarStatus(
            node.status
        );

    const color =
        getStatusColor(
            status
        );

    const valor = (value) =>
        safeText(value) || "-";

    const tipo =
        safeText(node.type) || "PROCESS";

    const nombre =
        safeText(node.name) || "SIN NOMBRE";

    const estadoDescripcion = {
        OK: "Proceso operativo",
        WARNING: "Requiere revisión",
        ERROR: "Proceso con incidencia",
        RUNNING: "Proceso en ejecución",
        UNKNOWN: "Estado no disponible"
    }[status] || "Estado no disponible";

    panel.innerHTML = `

        <div class="detail-modern">

            <div class="detail-top">

                <div class="detail-identity">

                    <div class="detail-kicker">
                        ${tipo}
                    </div>

                    <div class="detail-name">
                        ${nombre}
                    </div>

                    <div class="detail-subtitle">
                        DETALLE DEL PROCESO
                    </div>

                </div>

                <div
                    class="detail-status-modern"
                    style="
                        color:${color};
                        border-color:${color}66;
                        box-shadow:0 0 14px ${color}18;
                    "
                >
                    <span>●</span>
                    ${status}
                </div>

            </div>


            <div class="detail-section">

                <div class="detail-section-title">
                    OPERACIÓN
                </div>

                <div class="detail-grid-modern">

                    <div class="detail-card">
                        <span class="detail-card-label">
                            SECUENCIA
                        </span>
                        <span class="detail-card-value">
                            ${valor(node.sequence)}
                        </span>
                    </div>

                    <div class="detail-card">
                        <span class="detail-card-label">
                            FRECUENCIA
                        </span>
                        <span class="detail-card-value">
                            ${valor(node.frequency)}
                        </span>
                    </div>

                    <div class="detail-card">
                        <span class="detail-card-label">
                            EJECUCIÓN
                        </span>
                        <span class="detail-card-value">
                            ${valor(node.execution)}
                        </span>
                    </div>

                    <div class="detail-card">
                        <span class="detail-card-label">
                            TIPO
                        </span>
                        <span class="detail-card-value">
                            ${valor(node.report_type)}
                        </span>
                    </div>

                </div>

            </div>


            <div class="detail-section">

                <div class="detail-section-title">
                    CONFIGURACIÓN TÉCNICA
                </div>

                <div class="detail-grid-modern">

                    <div class="detail-card">
                        <span class="detail-card-label">
                            SCHEMA
                        </span>
                        <span class="detail-card-value">
                            ${valor(node.schema)}
                        </span>
                    </div>

                    <div class="detail-card">
                        <span class="detail-card-label">
                            SP / LOG
                        </span>
                        <span class="detail-card-value">
                            ${valor(node.sp_log)}
                        </span>
                    </div>

                </div>

            </div>


            <div class="detail-section">

                <div class="detail-section-title">
                    ESTADO OPERATIVO
                </div>

                <div
                    class="detail-state"
                    style="border-color:${color}35;"
                >

                    <span
                        class="detail-state-dot"
                        style="color:${color}; background:${color};"
                    ></span>

                    <div class="detail-state-main">

                        <div
                            class="detail-state-value"
                            style="color:${color};"
                        >
                            ${status}
                        </div>

                        <div class="detail-state-caption">
                            ${estadoDescripcion}
                        </div>

                    </div>

                </div>

            </div>


            <div class="detail-section">

                <div class="detail-section-title">
                    PROCEDIMIENTO / LOG
                </div>

                <div class="detail-code">
                    ${valor(node.sp_log)}
                </div>

            </div>


            <div class="detail-insight">

                <div class="detail-insight-title">
                    ✦ OBSERVABILITY INSIGHT
                </div>

                <div class="detail-insight-text">
                    ${estadoDescripcion}.
                    Estado actual registrado como
                    <strong style="color:${color};">
                        ${status}
                    </strong>.
                </div>

            </div>

        </div>
    `;

    panel.classList.add(
        "active"
    );

}


// ============================================================
// OCULTAR DETALLE
// ============================================================

function ocultarDetalle() {

    const panel =
        document.getElementById(
            "node-detail"
        );


    if (!panel) {
        return;
    }


    panel.classList.remove(
        "active"
    );

}


// ============================================================
// ACTUALIZAR KPIS
// ============================================================

function actualizarKPIs(
    kpis,
    nodes,
    links
) {

    const processes =
        document.getElementById(
            "processes-count"
        );


    const normal =
        document.getElementById(
            "normal-count"
        );


    const warning =
        document.getElementById(
            "warning-count"
        );


    const error =
        document.getElementById(
            "error-count"
        );


    const running =
        document.getElementById(
            "running-count"
        );


    const nodesCount =
        document.getElementById(
            "nodes-count"
        );


    const linksCount =
        document.getElementById(
            "links-count"
        );


    if (processes) {

        processes.textContent =
            kpis.processes ?? 0;

    }


    if (normal) {

        normal.textContent =
            kpis.normal ?? 0;

    }


    if (warning) {

        warning.textContent =
            kpis.warning ?? 0;

    }


    if (error) {

        error.textContent =
            kpis.error ?? 0;

    }


    if (running) {

        running.textContent =
            kpis.running ?? 0;

    }


    if (nodesCount) {

        nodesCount.textContent =
            nodes.length;

    }


    if (linksCount) {

        linksCount.textContent =
            links.length;

    }

}


// ============================================================
// LIVE
// ============================================================

function actualizarLive() {

    const elemento =
        document.getElementById(
            "last-update"
        );


    if (!elemento) {
        return;
    }


    const ahora =
        new Date();


    ultimoTimestamp =
        ahora;


    elemento.textContent =
        ahora.toLocaleTimeString(
            "es-PE",
            {

                hour: "2-digit",

                minute: "2-digit",

                second: "2-digit"

            }
        );

}


// ============================================================
// CARGAR PROCESOS
// ============================================================

async function cargarProcesos() {

    try {

        const response =
            await fetch(

                "/ia-observabilidad/api/procesos",

                {
                    cache:
                        "no-store"
                }

            );


        if (!response.ok) {

            throw new Error(
                "No se pudieron obtener los procesos"
            );

        }


        const data =
            await response.json();


        if (!procesoSelect) {
            return;
        }


        procesoSelect.innerHTML =
            "";


        const todos =
            document.createElement(
                "option"
            );


        todos.value =
            "";


        todos.textContent =
            "Todos los procesos";


        procesoSelect.appendChild(
            todos
        );


        (
            data.procesos || []
        ).forEach(
            proceso => {

                const option =
                    document.createElement(
                        "option"
                    );


                option.value =
                    proceso;


                option.textContent =
                    proceso;


                procesoSelect.appendChild(
                    option
                );

            }
        );


        procesoSelect.value =
            filtroProceso;


    }

    catch (error) {

        console.error(
            "Error cargando procesos:",
            error
        );

    }

}


// ============================================================
// CARGAR GRAFO
// ============================================================

async function cargarGrafo(
    conservarVista = true
) {

    try {

        const proceso =
            procesoSelect

                ? procesoSelect.value

                : filtroProceso;


        const periodo =
            periodoInput

                ? periodoInput.value

                : periodoActual;


        filtroProceso =
            proceso || "";


        periodoActual =
            periodo || "202606";


        const params =
            new URLSearchParams();


        if (filtroProceso) {

            params.set(
                "proceso",
                filtroProceso
            );

        }


        params.set(
            "periodo",
            periodoActual
        );


        const url =
            `/ia-observabilidad/api/grafo?${params.toString()}`;


        console.log(
            "Cargando:",
            url
        );


        const response =
            await fetch(

                url,

                {
                    cache:
                        "no-store"
                }

            );


        if (!response.ok) {

            const errorData =
                await response
                    .json()
                    .catch(
                        () => ({})
                    );


            throw new Error(

                errorData.error ||

                `HTTP ${response.status}`

            );

        }


        const data =
            await response.json();


        console.log(
            "IA Observabilidad:",
            data
        );


        if (
            !data.nodes ||
            !data.links
        ) {

            throw new Error(
                "La API no devolvió nodes/links"
            );

        }


        // ====================================================
        // GUARDAR POSICIONES ACTUALES
        // ====================================================

        if (
            graphData &&
            graphData.nodes
        ) {

            graphData.nodes.forEach(
                node => {

                    if (

                        Number.isFinite(
                            node.x
                        )

                        &&

                        Number.isFinite(
                            node.y
                        )

                        &&

                        Number.isFinite(
                            node.z
                        )

                    ) {

                        posiciones.set(

                            node.id,

                            {

                                x: node.x,

                                y: node.y,

                                z: node.z

                            }

                        );

                    }

                }
            );

        }


        // ====================================================
        // NUEVO DATASET
        // ====================================================

        graphData = {

            nodes:
                data.nodes,

            links:
                data.links

        };


        prepararPosiciones(
            graphData.nodes
        );


        // ====================================================
        // KPIS
        // ====================================================

        actualizarKPIs(

            data.kpis || {},

            graphData.nodes,

            graphData.links

        );


        actualizarLive();


        // ====================================================
        // INICIALIZAR GRAPH
        // ====================================================

        if (!Graph) {

            inicializarGraph();

        }


        // ====================================================
        // CARGAR DATA
        // ====================================================

        Graph.graphData(
            graphData
        );


        Graph.nodeVisibility(
            node =>
                nodoVisible(node)
        );


        Graph.linkVisibility(
            link =>
                linkVisible(link)
        );


        // ====================================================
        // CENTRAR SOLAMENTE CUANDO:
        //
        // false = carga inicial / cambio filtro
        //
        // true = actualización automática
        // ====================================================

        if (!conservarVista) {

            centrarUniverso(
                1200,
                35
            );

        }


        console.log(

            `Grafo cargado: ` +

            `${graphData.nodes.length} nodos / ` +

            `${graphData.links.length} links`

        );

    }

    catch (error) {

        console.error(

            "Error actualizando observabilidad:",

            error

        );


        const mensaje =
            document.getElementById(
                "update-message"
            );


        if (mensaje) {

            mensaje.textContent =
                "No fue posible actualizar los datos. Se conserva la última vista.";


            mensaje.classList.add(
                "visible"
            );


            setTimeout(

                () => {

                    mensaje.classList.remove(
                        "visible"
                    );

                },

                5000

            );

        }

    }

}


// ============================================================
// BUSQUEDA
// ============================================================

function configurarBusqueda() {

    if (!searchInput) {
        return;
    }


    searchInput.addEventListener(

        "input",

        event => {

            searchText =
                event.target.value.trim();


            if (!Graph) {
                return;
            }


            Graph.nodeVisibility(
                node =>
                    nodoVisible(node)
            );


            Graph.linkVisibility(
                link =>
                    linkVisible(link)
            );


            // ------------------------------------------------
            // CENTRAR RESULTADOS DE BUSQUEDA
            // ------------------------------------------------

            if (searchText) {

                centrarUniverso(
                    700,
                    80
                );

            }

        }

    );

}


// ============================================================
// FILTRO PROCESO
// ============================================================

function configurarFiltroProceso() {

    if (!procesoSelect) {
        return;
    }


    procesoSelect.addEventListener(

        "change",

        () => {

            cargarGrafo(
                false
            );

        }

    );

}


// ============================================================
// FILTRO PERIODO
// ============================================================

function configurarFiltroPeriodo() {

    if (!periodoInput) {
        return;
    }


    periodoInput.addEventListener(

        "change",

        () => {

            cargarGrafo(
                false
            );

        }

    );

}


// ============================================================
// BOTÓN CENTRAR
// ============================================================

function configurarBotonCentrar() {

    const boton =
        document.getElementById(
            "btn-center-world"
        );


    if (!boton) {

        console.warn(
            "No existe #btn-center-world"
        );

        return;

    }


    boton.addEventListener(

        "click",

        () => {

            console.log(
                "CENTRAR UNIVERSO"
            );


            centrarUniverso(
                1000,
                100
            );

        }

    );

}


// ============================================================
// ANIMACIÓN
// ============================================================

function animar() {

    requestAnimationFrame(
        animar
    );


    objetosAnimados.forEach(

        item => {

            if (
                !item.object
            ) {
                return;
            }


            item.object.rotation.z +=
                item.speed;

        }

    );

}


animar();


// ============================================================
// RESIZE
// ============================================================

let resizeTimer = null;
let ultimoAnchoGraph = 0;
let ultimaAltoGraph = 0;

function reajustarGraphPorLayout() {

    if (!Graph || !container) {
        return;
    }

    const width = container.clientWidth;
    const height = container.clientHeight;

    if (width < 300 || height < 250) {
        return;
    }

    const cambioImportante =
        Math.abs(width - ultimoAnchoGraph) > 20 ||
        Math.abs(height - ultimaAltoGraph) > 20;

    Graph.width(width);
    Graph.height(height);

    ultimoAnchoGraph = width;
    ultimaAltoGraph = height;

    /*
     * Cuando cambia el tamaño del layout (maximizar,
     * minimizar o contraer sidebar), volvemos a centrar
     * el universo para que nunca quede pegado a una esquina.
     */
    if (cambioImportante && graphData.nodes.length) {

        clearTimeout(resizeTimer);

        resizeTimer = setTimeout(() => {

            centrarUniverso(700, 35);

        }, 180);
    }
}

window.addEventListener(
    "resize",
    reajustarGraphPorLayout
);

/*
 * ResizeObserver detecta cambios provocados por el sidebar
 * aunque el navegador no dispare un resize tradicional.
 */
if (window.ResizeObserver && container) {

    const graphResizeObserver =
        new ResizeObserver(() => {

            reajustarGraphPorLayout();

        });

    graphResizeObserver.observe(container);
}


// ============================================================
// INICIAR
// ============================================================

async function iniciar() {

    console.log(
        "======================================"
    );


    console.log(
        "IA OBSERVABILIDAD - INICIANDO"
    );


    console.log(
        "======================================"
    );


    if (periodoInput) {

        periodoActual =
            periodoInput.value ||
            "202606";

    }


    // --------------------------------------------------------
    // GRAPH
    // --------------------------------------------------------

    inicializarGraph();


    // --------------------------------------------------------
    // EVENTOS
    // --------------------------------------------------------

    configurarBusqueda();

    configurarFiltroProceso();

    configurarFiltroPeriodo();

    configurarBotonCentrar();


    // --------------------------------------------------------
    // DATOS
    // --------------------------------------------------------

    await cargarProcesos();


    await cargarGrafo(
        false
    );


    // --------------------------------------------------------
    // ACTUALIZACIÓN LIVE
    //
    // IMPORTANTE:
    // true = conserva la cámara
    // --------------------------------------------------------

    setInterval(

        () => {

            cargarGrafo(
                true
            );

        },

        10000

    );

}


// ============================================================
// START
// ============================================================

iniciar();