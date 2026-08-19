/* ============================================================
   RT BI
   AI AGENT FLOW MONITOR
   NEURAL HOLOGRAPHIC ENGINE
   ============================================================ */

(() => {

    "use strict";


    /* ============================================================
       CONFIGURACIÓN
       ============================================================ */

    const POLL_INTERVAL = 500;

    let pollingTimer = null;

    let initialized = false;

    let processing = false;

    let completed = false;

    let eventIndex = 0;

    const processedEvents = new Set();

    let nodes = [];

    let connections = [];


    /* ============================================================
       EVENTOS DE INICIO
       ============================================================ */

    const START_EVENTS = [

        "CHAT_RECEIVED",
        "CHAT_START",
        "QUERY_RECEIVED",
        "REQUEST_RECEIVED",
        "CONSULTA_RECIBIDA"

    ];


    /* ============================================================
       EVENTOS DE FIN
       ============================================================ */

    const FINISH_EVENTS = [

        "CHAT_FINISHED",
        "CHAT_COMPLETE",
        "CHAT_COMPLETED",
        "QUERY_FINISHED",
        "QUERY_COMPLETED",
        "REQUEST_FINISHED",
        "EXECUTION_FINISHED"

    ];


    /* ============================================================
       MAPA VISUAL DE LA RED
       ============================================================ */

    const NETWORK = [

        { x: 15, y: 45 },
        { x: 24, y: 32 },
        { x: 33, y: 43 },

        { x: 42, y: 28 },
        { x: 50, y: 21 },
        { x: 58, y: 31 },

        { x: 67, y: 43 },
        { x: 76, y: 33 },
        { x: 85, y: 46 },

        { x: 25, y: 60 },
        { x: 36, y: 68 },

        { x: 50, y: 63 },

        { x: 64, y: 68 },
        { x: 75, y: 58 }

    ];


    const CONNECTIONS = [

        [0, 1],
        [1, 2],

        [2, 3],
        [3, 4],
        [4, 5],
        [5, 6],

        [6, 7],
        [7, 8],

        [1, 9],
        [9, 10],

        [2, 11],

        [6, 12],
        [12, 13]

    ];


    /* ============================================================
       DOM
       ============================================================ */

    let monitor;

    let neuralSpace;

    let neuralNetwork;

    let neuralCore;

    let coreStatus;

    let eventBubble;

    let eventNameElement;

    let eventDetailElement;

    let flowText;

    let executionStatus;

    let executionQuery;

    let executionAgent;

    let executionCurrentEvent;

    let executionCurrentState;

    let eventsList;

    let eventCounter;


    /* ============================================================
       INICIALIZACIÓN
       ============================================================ */

    function init() {

        if (initialized) {
            return;
        }


        monitor =
            document.getElementById(
                "neuralMonitor"
            );


        if (!monitor) {

            console.warn(
                "[NEURAL] No se encontró #neuralMonitor"
            );

            return;

        }


        initialized = true;


        neuralSpace =
            document.getElementById(
                "neuralSpace"
            );


        neuralNetwork =
            document.getElementById(
                "neuralNetwork"
            );


        neuralCore =
            document.getElementById(
                "neuralCore"
            );


        coreStatus =
            document.getElementById(
                "neuralCoreStatus"
            );


        eventBubble =
            document.getElementById(
                "neuralEventBubble"
            );


        eventNameElement =
            document.getElementById(
                "neuralEventName"
            );


        eventDetailElement =
            document.getElementById(
                "neuralEventDetail"
            );


        flowText =
            document.getElementById(
                "neuralFlowText"
            );


        executionStatus =
            document.getElementById(
                "executionStatus"
            );


        executionQuery =
            document.getElementById(
                "executionQuery"
            );


        executionAgent =
            document.getElementById(
                "executionAgent"
            );


        executionCurrentEvent =
            document.getElementById(
                "executionCurrentEvent"
            );


        executionCurrentState =
            document.getElementById(
                "executionCurrentState"
            );


        eventsList =
            document.getElementById(
                "neuralEventsList"
            );


        eventCounter =
            document.getElementById(
                "eventCounter"
            );


        createStars();

        createNetwork();

        createHolographicBrain();

        startPolling();


        console.log(
            "🧠 AI Neural Monitor inicializado"
        );

    }


    /* ============================================================
       ESTRELLAS
       ============================================================ */

    function createStars() {

        if (!neuralSpace) {
            return;
        }


        neuralSpace.innerHTML = "";


        for (
            let i = 0;
            i < 130;
            i++
        ) {

            const star =
                document.createElement(
                    "span"
                );


            star.className =
                "neural-star";


            if (
                Math.random() > .86
            ) {

                star.classList.add(
                    "big"
                );

            }


            star.style.left =
                `${Math.random() * 100}%`;


            star.style.top =
                `${Math.random() * 100}%`;


            star.style.animationDelay =
                `${Math.random() * 4}s`;


            star.style.animationDuration =
                `${2 + Math.random() * 5}s`;


            neuralSpace.appendChild(
                star
            );

        }

    }


    /* ============================================================
       RED NEURONAL
       ============================================================ */

    function createNetwork() {

        if (!neuralNetwork) {
            return;
        }


        neuralNetwork.innerHTML = "";


        nodes = [];

        connections = [];


        /* ========================================================
           CONEXIONES
           ======================================================== */

        CONNECTIONS.forEach(
            (pair, index) => {

                const a =
                    NETWORK[pair[0]];


                const b =
                    NETWORK[pair[1]];


                const line =
                    document.createElement(
                        "div"
                    );


                line.className =
                    "neural-connection";


                const dx =
                    b.x - a.x;


                const dy =
                    b.y - a.y;


                const distance =
                    Math.sqrt(
                        dx * dx +
                        dy * dy
                    );


                const angle =
                    Math.atan2(
                        dy,
                        dx
                    ) *
                    180 /
                    Math.PI;


                line.style.left =
                    `${a.x}%`;


                line.style.top =
                    `${a.y}%`;


                line.style.width =
                    `${distance}%`;


                line.style.transform =
                    `rotate(${angle}deg)`;


                line.dataset.index =
                    index;


                neuralNetwork.appendChild(
                    line
                );


                connections.push(
                    line
                );

            }
        );


        /* ========================================================
           NODOS
           ======================================================== */

        NETWORK.forEach(
            (point, index) => {

                const node =
                    document.createElement(
                        "div"
                    );


                node.className =
                    "neural-node";


                node.style.left =
                    `${point.x}%`;


                node.style.top =
                    `${point.y}%`;


                node.dataset.index =
                    index;


                neuralNetwork.appendChild(
                    node
                );


                nodes.push(
                    node
                );

            }
        );

    }


    function createHolographicBrain() {

    const container =
        document.getElementById(
            "neuralCoreSvg"
        );

    if (!container) {
        return;
    }


    /* ========================================================
       CEREBRO HOLOGRÁFICO
       ======================================================== */

    let particles = "";


    const PARTICLES = [

        [18, 28],
        [25, 18],
        [34, 12],
        [45, 9],
        [58, 12],
        [70, 18],
        [80, 28],

        [12, 40],
        [20, 48],
        [25, 62],
        [30, 72],

        [42, 20],
        [52, 17],
        [64, 22],

        [76, 42],
        [82, 52],
        [76, 65],

        [68, 78],
        [56, 85],
        [43, 82],

        [30, 82],
        [20, 70],

        [38, 36],
        [48, 30],
        [60, 34],

        [35, 52],
        [47, 47],
        [62, 50],

        [38, 66],
        [50, 60],
        [62, 67]

    ];


    PARTICLES.forEach(
        (point, index) => {

            const size =
                0.7 +
                Math.random() * 1.6;

            const delay =
                Math.random() * 3;

            particles += `

                <circle
                    class="brain-particle"
                    cx="${point[0]}"
                    cy="${point[1]}"
                    r="${size}"
                    style="
                        animation-delay:
                        ${delay}s;
                    "
                />

            `;
        }
    );


    container.innerHTML = `

        <svg
            viewBox="0 0 100 100"
            xmlns="http://www.w3.org/2000/svg"
            aria-hidden="true"
        >

            <!-- ==========================================
                 PARTÍCULAS HOLOGRÁFICAS
                 ========================================== -->

            <g
                class="brain-particles"
            >

                ${particles}

            </g>


            <!-- ==========================================
                 CONEXIONES DEL CEREBRO
                 ========================================== -->

            <g
                class="brain-connections"
            >

                <line
                    x1="20"
                    y1="48"
                    x2="38"
                    y2="36"
                    class="brain-path"
                />

                <line
                    x1="38"
                    y1="36"
                    x2="48"
                    y2="30"
                    class="brain-path"
                />

                <line
                    x1="48"
                    y1="30"
                    x2="60"
                    y2="34"
                    class="brain-path"
                />

                <line
                    x1="60"
                    y1="34"
                    x2="76"
                    y2="42"
                    class="brain-path"
                />

                <line
                    x1="25"
                    y1="62"
                    x2="35"
                    y2="52"
                    class="brain-path"
                />

                <line
                    x1="35"
                    y1="52"
                    x2="47"
                    y2="47"
                    class="brain-path"
                />

                <line
                    x1="47"
                    y1="47"
                    x2="62"
                    y2="50"
                    class="brain-path"
                />

                <line
                    x1="30"
                    y1="72"
                    x2="38"
                    y2="66"
                    class="brain-path"
                />

                <line
                    x1="38"
                    y1="66"
                    x2="50"
                    y2="60"
                    class="brain-path"
                />

                <line
                    x1="50"
                    y1="60"
                    x2="62"
                    y2="67"
                    class="brain-path"
                />

                <line
                    x1="62"
                    y1="67"
                    x2="68"
                    y2="78"
                    class="brain-path"
                />

            </g>


            <!-- ==========================================
                 SILUETA CEREBRAL
                 ========================================== -->

            <path
                class="brain-path"
                d="
                    M50 20

                    C40 12
                    27 18
                    27 29

                    C17 28
                    13 37
                    18 44

                    C11 53
                    18 64
                    28 63

                    C27 74
                    38 82
                    46 76

                    C48 83
                    52 83
                    54 76

                    C62 82
                    73 74
                    72 63

                    C82 64
                    89 53
                    82 44

                    C87 37
                    83 28
                    73 29

                    C73 18
                    60 12
                    50 20

                    Z
                "
            />


            <!-- ==========================================
                 DIVISIÓN CEREBRAL
                 ========================================== -->

            <path
                class="brain-path"
                d="
                    M50 21
                    L50 77
                "
            />


            <!-- ==========================================
                 RED INTERNA
                 ========================================== -->

            <path
                class="brain-path"
                d="
                    M28 34
                    C38 34 43 40 44 49
                    C44 58 39 64 31 66
                "
            />

            <path
                class="brain-path"
                d="
                    M72 34
                    C62 34 57 40 56 49
                    C56 58 61 64 69 66
                "
            />


            <!-- ==========================================
                 NODOS PRINCIPALES
                 ========================================== -->

            <circle
                class="brain-node"
                cx="38"
                cy="36"
                r="1.5"
            />

            <circle
                class="brain-node"
                cx="47"
                cy="47"
                r="1.8"
            />

            <circle
                class="brain-node"
                cx="62"
                cy="50"
                r="1.8"
            />

            <circle
                class="brain-node"
                cx="50"
                cy="60"
                r="2"
            />

            <circle
                class="brain-node"
                cx="35"
                cy="66"
                r="1.4"
            />

            <circle
                class="brain-node"
                cx="68"
                cy="78"
                r="1.4"
            />

        </svg>

    `;
}

    /* ============================================================
       NUEVA CONSULTA
       ============================================================ */

    function startNeural() {

        processing = true;

        completed = false;

        eventIndex = 0;


        clearVisualState();

    /* ========================================================
       THREE.JS - ACTIVAR CEREBRO
       ======================================================== */

    if (window.brainHologram) {

        window.brainHologram.activate(
            "AI REGULATORIO BI"
        );

    }


        if (neuralCore) {

            neuralCore.classList.remove(
                "completed"
            );

            neuralCore.classList.add(
                "thinking"
            );

        }


        if (coreStatus) {

            coreStatus.textContent =
                "PROCESANDO CONSULTA";

        }


        if (flowText) {

            flowText.textContent =
                "PROCESANDO";

        }


        if (executionStatus) {

            executionStatus.textContent =
                "RUNNING";

        }


        if (executionCurrentState) {

            executionCurrentState.textContent =
                "Procesando";

        }


        if (eventBubble) {

            eventBubble.classList.remove(
                "completed"
            );

            eventBubble.classList.add(
                "active"
            );

        }


        console.log(
            "⚡ Consulta iniciada"
        );

    }


    /* ============================================================
       PROCESAR EVENTO
       ============================================================ */

    function processNeuralEvent(
        name,
        raw
    ) {

        if (!name) {
            return;
        }


        if (!processing) {

            startNeural();

        }


        if (completed) {
            return;
        }


        const index =
            eventIndex %
            nodes.length;


        const node =
            nodes[index];


        if (!node) {
            return;
        }


        /* ========================================================
           NODO ACTIVO
           ======================================================== */

        node.classList.remove(
            "completed"
        );


        node.classList.add(
            "active"
        );

        /* ========================================================
           THREE.JS - PULSO NEURONAL
           ======================================================== */

        if (window.brainHologram) {

            const detail =
                raw?.detalle ||
                raw?.detail ||
                raw?.data ||
                {};

            const agent =
                typeof detail === "object"
                    ? (
                        detail.agente ||
                        detail.agent ||
                        "IA"
                    )
                    : "IA";

            window.brainHologram.activate(
                agent
            );

        }


        /* ========================================================
           CONEXIÓN
           ======================================================== */

        const connectionIndex =
            Math.max(
                0,
                index - 1
            );


        const connection =
            connections[
                connectionIndex %
                connections.length
            ];


        if (connection) {

            connection.classList.add(
                "active"
            );


            setTimeout(
                () => {

                    connection.classList.remove(
                        "active"
                    );

                    connection.classList.add(
                        "completed"
                    );

                },
                700
            );

        }


        /* ========================================================
           EVENTO VISUAL
           ======================================================== */

        showCurrentEvent(
            name,
            raw
        );


        /* ========================================================
           ORBE
           ======================================================== */

        createEventOrb(
            node
        );


        /* ========================================================
           MARCAR NODO
           ======================================================== */

        /* ========================================================
           THREE.JS - COMPLETAR EVENTO
           ======================================================== */

        if (window.brainHologram) {

            window.brainHologram.complete(
                "AI REGULATORIO BI"
            );

        }

        setTimeout(
            () => {

                node.classList.remove(
                    "active"
                );

                node.classList.add(
                    "completed"
                );

            },
            650
        );


        /* ========================================================
           REGISTRO
           ======================================================== */

        addEventRow(
            name,
            raw
        );


        updateExecution(
            name,
            raw
        );


        eventIndex++;

    }


    /* ============================================================
       EVENTO VISUAL
       ============================================================ */

    function showCurrentEvent(
        name,
        raw
    ) {

        if (eventNameElement) {

            eventNameElement.textContent =
                formatEventName(
                    name
                );

        }


        if (eventDetailElement) {

            eventDetailElement.textContent =
                getEventDetail(
                    raw
                );

        }


        if (eventBubble) {

            eventBubble.classList.remove(
                "completed"
            );

            eventBubble.classList.add(
                "active"
            );

        }


        if (coreStatus) {

            coreStatus.textContent =
                formatEventName(
                    name
                )
                .toUpperCase();

        }

    }


    /* ============================================================
       ORBE
       ============================================================ */

    function createEventOrb(
        node
    ) {

        if (!node || !monitor) {
            return;
        }


        const orb =
            document.createElement(
                "div"
            );


        orb.className =
            "neural-event-orb";


        orb.style.left =
            node.style.left;


        orb.style.top =
            node.style.top;


        monitor.appendChild(
            orb
        );


        setTimeout(
            () => {

                orb.classList.add(
                    "completed"
                );

            },
            650
        );


        setTimeout(
            () => {

                orb.remove();

            },
            1600
        );

    }


    /* ============================================================
       FINALIZAR
       ============================================================ */

    function completeNeural() {

        processing = false;

        completed = true;


        if (neuralCore) {

            neuralCore.classList.remove(
                "thinking"
            );

            neuralCore.classList.add(
                "completed"
            );

        }


        if (coreStatus) {

            coreStatus.textContent =
                "CONSULTA COMPLETADA";

        }


        if (flowText) {

            flowText.textContent =
                "EXECUCIÓN COMPLETADA";

        }


        if (executionStatus) {

            executionStatus.textContent =
                "COMPLETED";

        }


        if (executionCurrentState) {

            executionCurrentState.textContent =
                "Completado";

        }


        if (eventBubble) {

            eventBubble.classList.remove(
                "active"
            );

            eventBubble.classList.add(
                "completed"
            );

        }


        nodes.forEach(
            node => {

                node.classList.remove(
                    "active"
                );

                node.classList.add(
                    "completed"
                );

            }
        );


        connections.forEach(
            connection => {

                connection.classList.remove(
                    "active"
                );

                connection.classList.add(
                    "completed"
                );

            }
        );


        console.log(
            "✅ Ejecución completada"
        );

    }


    /* ============================================================
       LIMPIAR
       ============================================================ */

    function clearVisualState() {

        nodes.forEach(
            node => {

                node.classList.remove(
                    "active",
                    "completed"
                );

            }
        );


        connections.forEach(
            connection => {

                connection.classList.remove(
                    "active",
                    "completed"
                );

            }
        );


        document
            .querySelectorAll(
                ".neural-event-orb"
            )
            .forEach(
                orb => orb.remove()
            );

    }


    /* ============================================================
       ACTUALIZAR EJECUCIÓN
       ============================================================ */

    function updateExecution(
        name,
        raw
    ) {

        if (executionCurrentEvent) {

            executionCurrentEvent.textContent =
                formatEventName(
                    name
                );

        }


        if (!raw) {
            return;
        }


        const detail =
            raw.detalle ||
            raw.detail ||
            raw.data ||
            {};


        if (
            typeof detail !==
            "object"
        ) {

            return;

        }


        const pregunta =
            detail.pregunta ||
            detail.query ||
            detail.consulta;


        const agente =
            detail.agente ||
            detail.agent;


        if (
            pregunta &&
            executionQuery
        ) {

            executionQuery.textContent =
                pregunta;

        }


        if (
            agente &&
            executionAgent
        ) {

            executionAgent.textContent =
                agente;

        }

    }


    /* ============================================================
       REGISTRO
       ============================================================ */

    function addEventRow(
        name,
        raw
    ) {

        if (!eventsList) {
            return;
        }


        const empty =
            eventsList.querySelector(
                ".neural-empty-events"
            );


        if (empty) {
            empty.remove();
        }


        const row =
            document.createElement(
                "div"
            );


        row.className =
            "neural-event-row";


        const time =
            raw?.hora ||
            raw?.time ||
            new Date()
                .toLocaleTimeString(
                    "es-PE",
                    {
                        hour12: false
                    }
                );


        const status =
            String(
                raw?.estado ||
                raw?.status ||
                "RUNNING"
            ).toUpperCase();


        const detail =
            getEventDetail(
                raw
            );


        row.innerHTML = `

            <span class="event-row-time">
                ${escapeHtml(time)}
            </span>

            <span class="event-row-name">
                ${escapeHtml(
                    formatEventName(name)
                )}
            </span>

            <span class="event-row-status">
                ${escapeHtml(status)}
            </span>

            <span class="event-row-detail">
                ${escapeHtml(detail)}
            </span>

        `;


        if (
            status.includes(
                "ERROR"
            )
        ) {

            row.classList.add(
                "error"
            );

        }


        eventsList.prepend(
            row
        );


        while (
            eventsList.children.length >
            30
        ) {

            eventsList.lastElementChild.remove();

        }


        updateCounter();

    }


    /* ============================================================
       CONTADOR
       ============================================================ */

    function updateCounter() {

        if (!eventCounter) {
            return;
        }


        const count =
            eventsList
                ? eventsList.children.length
                : 0;


        eventCounter.textContent =
            `${count} EVENTOS`;

    }


    /* ============================================================
       OBTENER DETALLE
       ============================================================ */

    function getEventDetail(
        raw
    ) {

        if (!raw) {

            return "Proceso ejecutándose";

        }


        const detail =
            raw.detalle ||
            raw.detail ||
            raw.data;


        if (
            typeof detail ===
            "string"
        ) {

            return detail;

        }


        if (
            detail &&
            typeof detail ===
            "object"
        ) {

            return (
                detail.pregunta ||
                detail.query ||
                detail.consulta ||
                detail.agente ||
                detail.agent ||
                detail.mensaje ||
                detail.message ||
                "Proceso ejecutándose"
            );

        }


        return (
            raw.message ||
            raw.mensaje ||
            "Proceso ejecutándose"
        );

    }


    /* ============================================================
       FORMATEAR EVENTO
       ============================================================ */

    function formatEventName(
        name
    ) {

        if (!name) {
            return "PROCESANDO";
        }


        return String(name)

            .replaceAll(
                "_",
                " "
            )

            .toLowerCase()

            .replace(
                /\b\w/g,
                char =>
                    char.toUpperCase()
            );

    }


    /* ============================================================
       NORMALIZAR
       ============================================================ */

    function normalizeEvent(
        raw
    ) {

        if (!raw) {
            return null;
        }


        if (
            typeof raw ===
            "string"
        ) {

            return {

                name: raw,

                id: raw,

                raw: raw

            };

        }


        const name =
            raw.event ||
            raw.event_name ||
            raw.type ||
            raw.name ||
            raw.evento ||
            raw.accion ||
            raw.action ||
            raw.message;


        if (!name) {
            return null;
        }


        const id =
            raw.id ||
            raw.event_id ||
            raw.timestamp ||
            raw.ts ||
            `${name}-${JSON.stringify(raw)}`;


        return {

            name:
                String(name),

            id:
                String(id),

            raw:
                raw

        };

    }


    /* ============================================================
       EXTRAER EVENTOS
       ============================================================ */

    function extractEvents(
        data
    ) {

        if (!data) {
            return [];
        }


        if (
            Array.isArray(data)
        ) {

            return data;

        }


        if (
            Array.isArray(
                data.events
            )
        ) {

            return data.events;

        }


        if (
            Array.isArray(
                data.eventos
            )
        ) {

            return data.eventos;

        }


        if (
            Array.isArray(
                data.data
            )
        ) {

            return data.data;

        }


        if (
            Array.isArray(
                data.results
            )
        ) {

            return data.results;

        }


        if (
            data.event ||
            data.event_name ||
            data.type ||
            data.name
        ) {

            return [data];

        }


        return [];

    }


    /* ============================================================
       POLLING
       ============================================================ */

    function startPolling() {

        if (pollingTimer) {
            return;
        }


        pollAgentEvents();


        pollingTimer =
            setInterval(
                pollAgentEvents,
                POLL_INTERVAL
            );

    }


    /* ============================================================
       CONSULTAR BACKEND
       ============================================================ */

    async function pollAgentEvents() {

        try {

            const response =
                await fetch(
                    "/agent_events",
                    {
                        method:
                            "GET",

                        cache:
                            "no-store",

                        headers: {

                            "Cache-Control":
                                "no-cache"

                        }

                    }
                );


            if (
                !response.ok
            ) {

                return;

            }


            const data =
                await response.json();


            const rawEvents =
                extractEvents(
                    data
                );


            rawEvents.forEach(
                rawEvent => {

                    const event =
                        normalizeEvent(
                            rawEvent
                        );


                    if (!event) {
                        return;
                    }


                    if (
                        processedEvents.has(
                            event.id
                        )
                    ) {

                        return;

                    }


                    processedEvents.add(
                        event.id
                    );


                    processIncomingEvent(
                        event
                    );

                }
            );


        } catch (error) {

            /*
             * Silencioso.
             * No queremos llenar consola.
             */

        }

    }


    /* ============================================================
       PROCESAR EVENTO REAL
       ============================================================ */

    function processIncomingEvent(
        event
    ) {

        const name =
            event.name
                .toUpperCase();


        console.log(
            "[NEURAL EVENT]",
            name
        );


        if (
            START_EVENTS.includes(
                name
            )
        ) {

            startNeural();

            return;

        }


        if (
            FINISH_EVENTS.includes(
                name
            )
        ) {

            processNeuralEvent(
                name,
                event.raw
            );


            setTimeout(
                () => {

                    completeNeural();

                },
                700
            );


            return;

        }


        processNeuralEvent(
            name,
            event.raw
        );

    }


    /* ============================================================
       SEGURIDAD HTML
       ============================================================ */

    function escapeHtml(
        value
    ) {

        return String(
            value ?? ""
        )

            .replaceAll(
                "&",
                "&amp;"
            )

            .replaceAll(
                "<",
                "&lt;"
            )

            .replaceAll(
                ">",
                "&gt;"
            )

            .replaceAll(
                '"',
                "&quot;"
            )

            .replaceAll(
                "'",
                "&#039;"
            );

    }


    /* ============================================================
       API GLOBAL
       ============================================================ */

    window.AgentNeural = {

        init,

        start:
            startNeural,

        event:
            processNeuralEvent,

        complete:
            completeNeural,

        reset:
            clearVisualState

    };


    /* ============================================================
       ARRANQUE
       ============================================================ */

    if (
        document.readyState ===
        "loading"
    ) {

        document.addEventListener(
            "DOMContentLoaded",
            init
        );

    } else {

        init();

    }


})();