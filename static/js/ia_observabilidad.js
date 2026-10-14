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

// ============================================================
// VISIBILIDAD DEL GRAFO
// Al buscar un nodo, mostrar también sus relaciones cercanas.
// Dos saltos permiten: INPUT -> PROCESS -> otros INPUTS.
// ============================================================

let cacheIdsVisibles = null;
let cacheTextoBusqueda = null;
let cacheReferenciaGraphData = null;

function obtenerIdsVisiblesPorBusqueda() {

    if (
        cacheIdsVisibles &&
        cacheTextoBusqueda === searchText &&
        cacheReferenciaGraphData === graphData
    ) {
        return cacheIdsVisibles;
    }

    const nodes = graphData.nodes || [];
    const links = graphData.links || [];
    const visibles = new Set();

    // Sin búsqueda: conservar el universo completo.
    if (!searchText) {
        nodes.forEach(node => visibles.add(node.id));
    } else {
        const nodosPorId = new Map(
            nodes.map(node => [String(node.id), node])
        );

        const coincidencias = nodes.filter(
            node => nodoCoincideBusqueda(node)
        );

        // Siempre incluir las coincidencias directas.
        const distancia = new Map();

        coincidencias.forEach(node => {
            const id = String(node.id);
            visibles.add(node.id);
            distancia.set(id, 0);
        });

        // Construir relaciones en ambos sentidos para no depender
        // de si la API entrega INPUT -> PROCESS o PROCESS -> INPUT.
        const adyacencias = new Map();

        function agregarAdyacencia(origen, destino) {
            const origenId = String(origen);
            const destinoId = String(destino);

            if (
                !nodosPorId.has(origenId) ||
                !nodosPorId.has(destinoId)
            ) {
                return;
            }

            if (!adyacencias.has(origenId)) {
                adyacencias.set(origenId, new Set());
            }

            adyacencias.get(origenId).add(destinoId);
        }

        links.forEach(link => {
            const sourceId = String(
                typeof link.source === "object"
                    ? link.source.id
                    : link.source
            );

            const targetId = String(
                typeof link.target === "object"
                    ? link.target.id
                    : link.target
            );

            agregarAdyacencia(sourceId, targetId);
            agregarAdyacencia(targetId, sourceId);
        });

        // Mostrar hasta dos saltos desde cada coincidencia.
        // Así, al buscar un INPUT, se muestra su PROCESS y los
        // INPUTS hermanos relacionados con ese mismo proceso.
        const cola = coincidencias.map(node => ({
            id: String(node.id),
            profundidad: 0
        }));

        for (let i = 0; i < cola.length; i++) {
            const actual = cola[i];

            if (actual.profundidad >= 2) {
                continue;
            }

            const vecinos = adyacencias.get(actual.id) || new Set();

            vecinos.forEach(vecinoId => {
                const nuevaProfundidad = actual.profundidad + 1;
                const profundidadAnterior = distancia.get(vecinoId);

                if (
                    profundidadAnterior !== undefined &&
                    profundidadAnterior <= nuevaProfundidad
                ) {
                    return;
                }

                distancia.set(vecinoId, nuevaProfundidad);

                const nodo = nodosPorId.get(vecinoId);
                if (nodo) {
                    visibles.add(nodo.id);
                }

                cola.push({
                    id: vecinoId,
                    profundidad: nuevaProfundidad
                });
            });
        }
    }

    cacheIdsVisibles = visibles;
    cacheTextoBusqueda = searchText;
    cacheReferenciaGraphData = graphData;

    return visibles;
}


function nodoVisible(node) {
    if (!node) return false;

    return obtenerIdsVisiblesPorBusqueda().has(node.id);
}


function linkVisible(link) {

    const source =
        typeof link.source === "object"
            ? link.source
            : graphData.nodes.find(
                n => String(n.id) === String(link.source)
            );

    const target =
        typeof link.target === "object"
            ? link.target
            : graphData.nodes.find(
                n => String(n.id) === String(link.target)
            );

    if (!source || !target) {
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


// ============================================================
// VER FLUJO - NUEVO COMPONENTE ADITIVO
// No altera la topología ni los filtros del grafo principal.
// ============================================================

function flowEscape(value) {
    return safeText(value).replace(/[&<>"']/g, char => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    }[char]));
}

function flowGetNodeId(value) {
    return String(
        value && typeof value === "object" ? value.id : value
    );
}

function flowGetRelatedNodes(query) {
    const nodes = graphData.nodes || [];
    const links = graphData.links || [];
    const normalizedQuery = safeText(query).trim().toUpperCase();
    const byId = new Map(nodes.map(node => [String(node.id), node]));

    const directMatches = nodes.filter(node => {
        const searchable = [
            node.name, node.type, node.status, node.schema,
            node.sp_log, node.sequence
        ].map(safeText).join(" ").toUpperCase();
        return searchable.includes(normalizedQuery);
    });

    if (!directMatches.length) return { matches: [], nodes: [] };

    const adjacency = new Map();
    function connect(a, b) {
        a = String(a); b = String(b);
        if (!byId.has(a) || !byId.has(b)) return;
        if (!adjacency.has(a)) adjacency.set(a, new Set());
        if (!adjacency.has(b)) adjacency.set(b, new Set());
        adjacency.get(a).add(b);
        adjacency.get(b).add(a);
    }

    links.forEach(link => connect(flowGetNodeId(link.source), flowGetNodeId(link.target)));

    // Se parte de la coincidencia directa y se recupera el flujo
    // relacionado hasta dos saltos: INPUTS ↔ PROCESS ↔ REPORT.
    const included = new Set();
    const distance = new Map();
    const queue = directMatches.map(node => ({ id: String(node.id), depth: 0 }));
    queue.forEach(item => {
        included.add(item.id);
        distance.set(item.id, 0);
    });

    for (let i = 0; i < queue.length; i++) {
        const current = queue[i];
        if (current.depth >= 2) continue;
        (adjacency.get(current.id) || new Set()).forEach(nextId => {
            const nextDepth = current.depth + 1;
            if (distance.has(nextId) && distance.get(nextId) <= nextDepth) return;
            distance.set(nextId, nextDepth);
            included.add(nextId);
            queue.push({ id: nextId, depth: nextDepth });
        });
    }

    const related = Array.from(included)
        .map(id => byId.get(id))
        .filter(Boolean);

    return { matches: directMatches, nodes: related };
}

function flowStatusHtml(node) {
    const status = normalizarStatus(node.status);
    const color = getStatusColor(status);
    return `<span class="flow-status" style="color:${color}">
        <i class="flow-status-dot"></i>${flowEscape(status)}
    </span>`;
}

function flowCardHtml(node, isMatch) {
    const type = safeText(node.type).toUpperCase();
    const details = [];
    if (node.schema) details.push(["Esquema", node.schema]);
    if (node.frequency) details.push(["Frecuencia", node.frequency]);
    const day = node.execution_day || node.day_execution || node.executionDay || "";
    if (day !== "") details.push(["Día de ejecución", day]);
    if ((type === "PROCESS" || type === "REPORT") && node.sp_log) details.push(["SP / Log", node.sp_log]);
    if (type === "REPORT" && node.report_type) details.push(["Tipo", node.report_type]);
    const id = String(node.id);
    const icon = type === "INPUT" ? "▤" : type === "PROCESS" ? "⚙" : "▥";
    return `<article class="flow-card flow-node flow-node-${type.toLowerCase()}${isMatch ? " is-match" : ""}" data-flow-node-id="${flowEscape(id)}" data-flow-type="${flowEscape(type)}" title="${flowEscape(node.name || node.id)}">
        <span class="flow-node-port flow-node-port-in"></span><span class="flow-node-port flow-node-port-out"></span>
        <div class="flow-card-icon" aria-hidden="true">${icon}</div>
        <div class="flow-card-main"><div class="flow-card-top"><span class="flow-card-type">${flowEscape(type)}</span>${flowStatusHtml(node)}</div>
        <h3 class="flow-card-name">${flowEscape(node.name || node.id)}</h3>
        <div class="flow-card-details">${details.map(([label, value]) => `<div class="flow-detail-row"><span>${flowEscape(label)}</span><strong>${flowEscape(value)}</strong></div>`).join("")}</div></div>
    </article>`;
}

function flowDrawConnections(nodes) {
    const canvas = document.getElementById("flow-canvas");
    const svg = document.getElementById("flow-connections");
    if (!canvas || !svg) return;
    const rect = canvas.getBoundingClientRect();
    const width = Math.max(canvas.scrollWidth, rect.width);
    const height = Math.max(canvas.scrollHeight, rect.height);
    svg.setAttribute("width", width);
    svg.setAttribute("height", height);
    svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
    const visible = new Set(nodes.map(n => String(n.id)));
    const nodeEls = new Map(Array.from(canvas.querySelectorAll("[data-flow-node-id]")).map(el => [el.dataset.flowNodeId, el]));
    const paths = [];
    (graphData.links || []).forEach(link => {
        const sourceId = flowGetNodeId(link.source);
        const targetId = flowGetNodeId(link.target);
        if (!visible.has(sourceId) || !visible.has(targetId)) return;
        const sourceEl = nodeEls.get(sourceId), targetEl = nodeEls.get(targetId);
        if (!sourceEl || !targetEl) return;
        const a = sourceEl.getBoundingClientRect(), b = targetEl.getBoundingClientRect();
        const x1 = a.right - rect.left + canvas.scrollLeft;
        const y1 = a.top + a.height / 2 - rect.top + canvas.scrollTop;
        const x2 = b.left - rect.left + canvas.scrollLeft;
        const y2 = b.top + b.height / 2 - rect.top + canvas.scrollTop;
        const bend = Math.max(45, (x2 - x1) * .48);
        const type = safeText((nodeEls.get(sourceId)?.dataset.flowType) || "INPUT").toLowerCase();
        const color = type === "input" ? "#28c4ff" : type === "process" ? "#22e58a" : "#ffc857";
        const d = `M ${x1} ${y1} C ${x1 + bend} ${y1}, ${x2 - bend} ${y2}, ${x2} ${y2}`;
        paths.push(`<path class="flow-link-halo" d="${d}" stroke="${color}"/><path class="flow-link-path" d="${d}" stroke="${color}" marker-end="url(#flow-arrow)"/>`);
    });
    svg.innerHTML = `<defs><marker id="flow-arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L6,3 z" fill="#bceeff"/></marker></defs>${paths.join("")}`;
}

function abrirFlujo() {
    const query = safeText(searchInput && searchInput.value).trim();
    const overlay = document.getElementById("flow-overlay");
    const content = document.getElementById("flow-content");
    const meta = document.getElementById("flow-meta-bar");
    const title = document.getElementById("flow-title");
    const subtitle = document.getElementById("flow-subtitle");
    if (!overlay || !content || !meta) return;
    if (!query) {
        if (searchInput) { searchInput.focus(); searchInput.setCustomValidity("Escribe un proceso, input o reporte para ver su flujo."); searchInput.reportValidity(); searchInput.setCustomValidity(""); }
        return;
    }
    const result = flowGetRelatedNodes(query);
    if (!result.matches.length) {
        title.textContent = "No se encontró el elemento";
        subtitle.textContent = "VERIFICA EL TEXTO DE BÚSQUEDA";
        meta.innerHTML = `<span>Búsqueda: <strong>${flowEscape(query)}</strong></span><span>Periodo: <strong>${flowEscape(periodoInput?.value || periodoActual)}</strong></span>`;
        content.innerHTML = `<div class="flow-empty"><strong>No encontramos coincidencias</strong>No hay un nodo relacionado con “${flowEscape(query)}” en los datos cargados. Revisa el nombre o limpia los filtros del panel principal e inténtalo nuevamente.</div>`;
    } else {
        const directIds = new Set(result.matches.map(node => String(node.id)));
        const nodes = result.nodes;
        const inputs = nodes.filter(node => safeText(node.type).toUpperCase() === "INPUT");
        const processes = nodes.filter(node => safeText(node.type).toUpperCase() === "PROCESS");
        const reports = nodes.filter(node => safeText(node.type).toUpperCase() === "REPORT");
        const primary = result.matches[0];
        title.textContent = safeText(primary.name || "Flujo de dependencias");
        subtitle.textContent = `${inputs.length} INPUT(S)  →  ${processes.length} PROCESS  →  ${reports.length} REPORT(S)`;
        meta.innerHTML = `<span>Elemento buscado: <strong>${flowEscape(query)}</strong></span><span>Coincidencias: <strong>${result.matches.length}</strong></span><span>Periodo: <strong>${flowEscape(periodoInput?.value || periodoActual)}</strong></span><span>Consulta: <strong>${new Date().toLocaleString("es-PE")}</strong></span>`;
        const lane = (cls, label, desc, laneNodes) => `<section class="flow-stage ${cls}"><header class="flow-stage-heading"><span class="flow-stage-symbol"></span><div><strong>${label}</strong><small>${desc} · ${laneNodes.length}</small></div></header><div class="flow-stage-nodes">${laneNodes.map(node => flowCardHtml(node, directIds.has(String(node.id)))).join("") || `<div class="flow-empty">Sin elementos relacionados</div>`}</div></section>`;
        content.innerHTML = `<div class="flow-toolbar"><label class="flow-search-inline"><span>⌕</span><input id="flow-search-inline-input" value="${flowEscape(query)}" aria-label="Buscar en el flujo"><button type="button" id="flow-search-clear" title="Limpiar búsqueda">×</button></label><div class="flow-toolbar-actions"><button type="button" data-flow-action="fit">⛶ <span>Ajustar</span></button><button type="button" data-flow-action="pan">✥ <span>Mover</span></button><button type="button" data-flow-action="zoom-in">⊕ <span>Zoom +</span></button><button type="button" data-flow-action="zoom-out">⊖ <span>Zoom −</span></button><button type="button" data-flow-action="fullscreen">⛶ <span>Pantalla completa</span></button><button type="button" data-flow-action="new-tab">↗ <span>Abrir aparte</span></button><button type="button" data-flow-action="download-png">⇩ <span>Descargar PNG</span></button></div></div><div class="flow-workspace" id="flow-workspace"><div class="flow-canvas-wrap" id="flow-canvas-wrap"><div class="flow-canvas" id="flow-canvas"><svg id="flow-connections" class="flow-connections" aria-hidden="true"></svg><div class="flow-stages">${lane("inputs", "INPUTS", "Fuentes de entrada", inputs)}${lane("processes", "PROCESS", "Procesamiento", processes)}${lane("reports", "REPORTS", "Salida regulatoria", reports)}</div></div></div><div class="flow-minimap" id="flow-minimap" aria-label="Minimapa del flujo"><div class="flow-mini-columns"><i></i><i></i><i></i><svg viewBox="0 0 100 70" preserveAspectRatio="none"><path d="M8 15 C35 15 35 25 50 25 S70 20 92 20 M8 35 C35 35 35 45 50 45 S70 40 92 40 M8 55 C35 55 35 45 50 45 S70 60 92 60"/></svg></div></div></div>`;
        requestAnimationFrame(() => {
            // Registrar los controles antes de dibujar conexiones: si el dibujo
            // falla por algún dato puntual, los botones seguirán funcionando.
            configurarControlesFlujo();
            try {
                flowDrawConnections(nodes);
            } catch (error) {
                console.error("No se pudieron dibujar algunas conexiones del flujo", error);
            }
        });
    }
    overlay.classList.add("is-open"); overlay.setAttribute("aria-hidden", "false"); document.body.classList.add("flow-modal-open");
    const closeButton = document.getElementById("btn-cerrar-flujo"); if (closeButton) closeButton.focus();
}

function configurarControlesFlujo() {
    const workspace = document.getElementById("flow-workspace");
    const canvas = document.getElementById("flow-canvas");
    if (!workspace || !canvas) return;

    // Estado guardado en el workspace: permite reabrir el flujo sin
    // perder el control ni registrar manejadores duplicados.
    if (!workspace._flowViewState) {
        workspace._flowViewState = {
            scale: 1, x: 0, y: 0, dragging: false,
            startX: 0, startY: 0, baseX: 0, baseY: 0
        };
    }
    const state = workspace._flowViewState;
    const apply = () => {
        const currentCanvas = document.getElementById("flow-canvas");
        if (!currentCanvas) return;
        currentCanvas.style.transform = `translate(${state.x}px, ${state.y}px) scale(${state.scale})`;
        currentCanvas.style.transformOrigin = "0 0";
    };

    // La barra de herramientas es hermana de #flow-workspace, no hija.
    // Por eso los clicks se delegan en #flow-content, que contiene ambos.
    const flowContent = document.getElementById("flow-content");
    if (!flowContent) return;

    if (flowContent.dataset.flowEventsReady !== "1") {
        flowContent.dataset.flowEventsReady = "1";

        flowContent.addEventListener("click", async event => {
            const button = event.target.closest("[data-flow-action]");
            if (!button || !flowContent.contains(button)) return;

            event.preventDefault();
            event.stopPropagation();
            const action = button.dataset.flowAction;
            console.debug("[IA Observabilidad][Flujo] Click detectado:", action);
            const currentCanvas = document.getElementById("flow-canvas");
            if (!currentCanvas) return;

            if (action === "zoom-in") state.scale = Math.min(3, state.scale + .15);
            else if (action === "zoom-out") state.scale = Math.max(.2, state.scale - .15);
            else if (action === "fit") {
                const availableW = Math.max(100, workspace.clientWidth - 50);
                const availableH = Math.max(100, workspace.clientHeight - 50);
                const canvasW = Math.max(currentCanvas.scrollWidth, currentCanvas.offsetWidth, 1);
                const canvasH = Math.max(currentCanvas.scrollHeight, currentCanvas.offsetHeight, 1);
                state.scale = Math.min(1, availableW / canvasW, availableH / canvasH);
                state.x = Math.max(12, (workspace.clientWidth - canvasW * state.scale) / 2);
                state.y = Math.max(12, (workspace.clientHeight - canvasH * state.scale) / 2);
            } else if (action === "pan") {
                workspace.classList.toggle("pan-mode");
                button.classList.toggle("active", workspace.classList.contains("pan-mode"));
            } else if (action === "fullscreen") {
                const win = document.querySelector("#flow-overlay .flow-window");
                try {
                    if (document.fullscreenElement) await document.exitFullscreen();
                    else if (win && win.requestFullscreen) await win.requestFullscreen();
                    else alert("Pantalla completa no está disponible en este navegador. Prueba con F11.");
                } catch (error) {
                    console.error("No se pudo activar pantalla completa:", error);
                    alert("El navegador no permitió activar pantalla completa. Prueba con F11.");
                }
            } else if (action === "new-tab") {
                abrirFlujoEnPestana();
            } else if (action === "download-png") {
                await descargarFlujoPNG();
            }
            apply();
        });

        workspace.addEventListener("wheel", event => {
            event.preventDefault();
            const oldScale = state.scale;
            state.scale = Math.max(.2, Math.min(3, state.scale + (event.deltaY < 0 ? .08 : -.08)));
            const rect = workspace.getBoundingClientRect();
            const px = event.clientX - rect.left, py = event.clientY - rect.top;
            state.x = px - (px - state.x) * (state.scale / oldScale);
            state.y = py - (py - state.y) * (state.scale / oldScale);
            apply();
        }, { passive: false });

        workspace.addEventListener("pointerdown", event => {
            if (event.button !== 0 || event.target.closest("button,input,label,a")) return;
            state.dragging = true;
            state.startX = event.clientX;
            state.startY = event.clientY;
            state.baseX = state.x;
            state.baseY = state.y;
            workspace.classList.add("is-dragging");
            try { workspace.setPointerCapture(event.pointerId); } catch (_) {}
        });

        workspace.addEventListener("pointermove", event => {
            if (!state.dragging) return;
            state.x = state.baseX + event.clientX - state.startX;
            state.y = state.baseY + event.clientY - state.startY;
            apply();
        });

        const stopDragging = () => {
            state.dragging = false;
            workspace.classList.remove("is-dragging");
        };
        workspace.addEventListener("pointerup", stopDragging);
        workspace.addEventListener("pointercancel", stopDragging);
        workspace.addEventListener("lostpointercapture", stopDragging);

        flowContent.addEventListener("click", event => {
            if (event.target.closest("#flow-search-clear")) {
                const search = document.getElementById("flow-search-inline-input");
                if (search) {
                    search.value = "";
                    search.focus();
                }
            }
        });

        workspace.addEventListener("keydown", event => {
            if (event.key === "Enter" && event.target.id === "flow-search-inline-input" && event.target.value.trim()) {
                if (searchInput) searchInput.value = event.target.value.trim();
                abrirFlujo();
            }
        });
    }

    // Garantiza que el canvas recién creado quede en un estado inicial válido.
    apply();
}
function abrirFlujoEnPestana() {
    const source = document.querySelector("#flow-overlay .flow-window");
    if (!source) return;
    const popup = window.open("", "_blank");
    if (!popup) {
        alert("El navegador bloqueó la nueva pestaña. Permite las ventanas emergentes para este sitio.");
        return;
    }
    const clone = source.cloneNode(true);
    clone.querySelector("#btn-cerrar-flujo")?.remove();
    clone.style.cssText = "width:100%;height:100vh;max-width:none;max-height:none;border-radius:0;";
    const cssHref = document.querySelector('link[href*="ia_observabilidad.css"]')?.href || "/static/css/ia_observabilidad.css";
    popup.document.open();
    popup.document.write(`<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>IA Observabilidad - Flujo</title><link rel="stylesheet" href="${cssHref}"><style>html,body{margin:0;width:100%;height:100%;overflow:hidden;background:#020812}.flow-overlay{display:block!important;position:static!important;inset:auto!important;padding:0!important;background:#020812!important;opacity:1!important;visibility:visible!important}.flow-window{width:100%!important;height:100vh!important;max-width:none!important;max-height:none!important;border-radius:0!important}.flow-workspace{cursor:grab!important}.flow-workspace.is-dragging{cursor:grabbing!important}</style></head><body><div class="flow-overlay is-open" id="flow-overlay"></div></body></html>`);
    popup.document.close();
    popup.document.getElementById("flow-overlay").appendChild(popup.document.importNode(clone, true));

    const doc = popup.document;
    const workspace = doc.getElementById("flow-workspace");
    const canvas = doc.getElementById("flow-canvas");
    if (!workspace || !canvas) return;
    let scale = 1, x = 0, y = 0, dragging = false, sx = 0, sy = 0, bx = 0, by = 0;
    const apply = () => { canvas.style.transform = `translate(${x}px,${y}px) scale(${scale})`; canvas.style.transformOrigin = "0 0"; };
    doc.querySelectorAll("#flow-content [data-flow-action]").forEach(button => button.addEventListener("click", async event => {
        const action = button.dataset.flowAction;
        if (action === "zoom-in") scale = Math.min(2.5, scale + .15);
        if (action === "zoom-out") scale = Math.max(.25, scale - .15);
        if (action === "fit") { scale = Math.min(1, (workspace.clientWidth - 40) / Math.max(canvas.scrollWidth, 1)); x = 12; y = 12; }
        if (action === "pan") { workspace.classList.toggle("pan-mode"); button.classList.toggle("active"); }
        if (action === "fullscreen") { if (doc.fullscreenElement) await doc.exitFullscreen?.(); else await doc.querySelector(".flow-window")?.requestFullscreen?.(); }
        if (action === "new-tab") alert("El flujo ya está abierto en una pestaña independiente.");
        if (action === "download-png") {
            if (!popup.html2canvas) {
                const script = doc.createElement("script");
                script.src = "https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js";
                script.onload = () => popupFlowPNG(popup, canvas);
                script.onerror = () => popup.alert("No se pudo cargar el exportador PNG. Verifica tu conexión.");
                doc.head.appendChild(script);
            } else popupFlowPNG(popup, canvas);
        }
        apply();
    }));
    workspace.addEventListener("wheel", event => { event.preventDefault(); const old = scale; scale = Math.max(.25, Math.min(2.5, scale + (event.deltaY < 0 ? .08 : -.08))); const r = workspace.getBoundingClientRect(), px = event.clientX-r.left, py = event.clientY-r.top; x = px-(px-x)*(scale/old); y = py-(py-y)*(scale/old); apply(); }, {passive:false});
    workspace.addEventListener("pointerdown", event => { if (event.button !== 0 || event.target.closest("button,input,label")) return; dragging=true; sx=event.clientX; sy=event.clientY; bx=x; by=y; workspace.classList.add("is-dragging"); workspace.setPointerCapture?.(event.pointerId); });
    workspace.addEventListener("pointermove", event => { if (!dragging) return; x=bx+event.clientX-sx; y=by+event.clientY-sy; apply(); });
    ["pointerup","pointercancel"].forEach(name => workspace.addEventListener(name, () => {dragging=false;workspace.classList.remove("is-dragging");}));
    const search = doc.getElementById("flow-search-inline-input");
    doc.getElementById("flow-search-clear")?.addEventListener("click", () => { if (search) search.value = ""; });
    doc.title = "IA Observabilidad - " + (doc.getElementById("flow-title")?.textContent || "Flujo");
}

async function popupFlowPNG(popup, canvas) {
    const previous = canvas.style.transform;
    canvas.style.transform = "none";
    try {
        await new Promise(resolve => popup.requestAnimationFrame(resolve));
        const image = await popup.html2canvas(canvas, {backgroundColor:"#030b14",scale:2,useCORS:true,width:canvas.scrollWidth,height:canvas.scrollHeight});
        const link = popup.document.createElement("a"); link.download="flujo_ia_observabilidad.png"; link.href=image.toDataURL("image/png"); link.click();
    } catch (error) { popup.console.error(error); popup.alert("No se pudo generar el PNG."); }
    finally { canvas.style.transform = previous; }
}

async function cargarExportadorPNG() {
    if (typeof window.html2canvas === "function") return window.html2canvas;

    return new Promise((resolve, reject) => {
        const existente = document.querySelector('script[data-flow-html2canvas="1"]');
        if (existente) {
            existente.addEventListener("load", () => {
                typeof window.html2canvas === "function"
                    ? resolve(window.html2canvas)
                    : reject(new Error("html2canvas no quedó disponible"));
            }, { once: true });
            existente.addEventListener("error", () => reject(new Error("No se pudo cargar html2canvas")), { once: true });
            return;
        }

        const script = document.createElement("script");
        script.src = "https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js";
        script.async = true;
        script.dataset.flowHtml2canvas = "1";
        script.onload = () => {
            if (typeof window.html2canvas === "function") resolve(window.html2canvas);
            else reject(new Error("html2canvas no quedó disponible después de cargar"));
        };
        script.onerror = () => reject(new Error("No se pudo cargar el exportador PNG; revisa la conexión o las restricciones de red"));
        document.head.appendChild(script);
    });
}

async function guardarCanvasPNG(canvas, html2canvasFn, nombreArchivo) {
    const originalTransform = canvas.style.transform;
    const originalOrigin = canvas.style.transformOrigin;
    const originalPosition = canvas.style.position;
    const originalLeft = canvas.style.left;
    const originalTop = canvas.style.top;

    try {
        // Captura el diagrama completo, sin el zoom/desplazamiento de la vista.
        canvas.style.transform = "none";
        canvas.style.transformOrigin = "top left";
        await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));

        const imageCanvas = await html2canvasFn(canvas, {
            backgroundColor: "#030b14",
            scale: 2,
            useCORS: true,
            logging: false,
            width: Math.max(canvas.scrollWidth, canvas.offsetWidth),
            height: Math.max(canvas.scrollHeight, canvas.offsetHeight),
            windowWidth: Math.max(document.documentElement.clientWidth, canvas.scrollWidth),
            windowHeight: Math.max(document.documentElement.clientHeight, canvas.scrollHeight)
        });

        const blob = await new Promise((resolve, reject) => {
            if (!imageCanvas.toBlob) {
                try {
                    const data = imageCanvas.toDataURL("image/png");
                    resolve(data);
                } catch (error) { reject(error); }
                return;
            }
            imageCanvas.toBlob(result => result ? resolve(result) : reject(new Error("No se pudo convertir el diagrama a PNG")), "image/png");
        });

        const link = document.createElement("a");
        link.download = nombreArchivo || "flujo_ia_observabilidad.png";
        link.style.display = "none";
        if (typeof blob === "string") {
            link.href = blob;
        } else {
            const url = URL.createObjectURL(blob);
            link.href = url;
            link.dataset.objectUrl = url;
        }
        document.body.appendChild(link);
        link.click();
        link.remove();
        if (link.dataset.objectUrl) setTimeout(() => URL.revokeObjectURL(link.dataset.objectUrl), 1500);
    } finally {
        canvas.style.transform = originalTransform;
        canvas.style.transformOrigin = originalOrigin;
        canvas.style.position = originalPosition;
        canvas.style.left = originalLeft;
        canvas.style.top = originalTop;
    }
}

async function descargarFlujoPNG() {
    const canvas = document.getElementById("flow-canvas");
    if (!canvas) {
        alert("No se encontró el diagrama para descargar. Cierra y vuelve a abrir VER FLUJO.");
        return;
    }

    const button = document.querySelector('[data-flow-action="download-png"]');
    const labelOriginal = button ? button.innerHTML : "";
    if (button) {
        button.disabled = true;
        button.innerHTML = "⏳ <span>Generando PNG...</span>";
    }

    try {
        const html2canvasFn = await cargarExportadorPNG();
        await guardarCanvasPNG(canvas, html2canvasFn, "flujo_ia_observabilidad.png");
    } catch (error) {
        console.error("Error exportando flujo PNG:", error);
        alert("No se pudo descargar el PNG. Si aparece un error de red, el navegador no pudo cargar el exportador; revisa la conexión o las restricciones de internet y vuelve a intentarlo.");
    } finally {
        if (button) {
            button.disabled = false;
            button.innerHTML = labelOriginal || "⇩ <span>Descargar PNG</span>";
        }
    }
}

function cerrarFlujo() {
    const overlay = document.getElementById("flow-overlay");
    if (!overlay) return;
    overlay.classList.remove("is-open");
    overlay.setAttribute("aria-hidden", "true");
    document.body.classList.remove("flow-modal-open");
    const button = document.getElementById("btn-ver-flujo");
    if (button) button.focus();
}

function configurarBotonVerFlujo() {
    const button = document.getElementById("btn-ver-flujo");
    const closeButton = document.getElementById("btn-cerrar-flujo");
    const overlay = document.getElementById("flow-overlay");

    if (button) button.addEventListener("click", abrirFlujo);
    if (closeButton) closeButton.addEventListener("click", cerrarFlujo);
    if (overlay) {
        overlay.addEventListener("click", event => {
            if (event.target === overlay) cerrarFlujo();
        });
    }
    document.addEventListener("keydown", event => {
        if (event.key === "Escape") cerrarFlujo();
    });
}

// Inicialización aditiva del botón de flujo.
configurarBotonVerFlujo();

window.addEventListener("resize", () => { const c = document.getElementById("flow-canvas"); if (c && document.getElementById("flow-overlay")?.classList.contains("is-open")) flowDrawConnections(graphData.nodes || []); });
