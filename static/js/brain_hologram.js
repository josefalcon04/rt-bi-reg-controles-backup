/* ============================================================
   BRAIN HOLOGRAM - THREE.JS
   AI REGULATORIO BI
   VERSION: ORGANIC NEURAL BRAIN
   ============================================================ */

/*
 * IMPORTANTE:
 * Esta versión usa THREE global.
 * En el HTML debe cargarse Three.js ANTES de este archivo.
 */


/* ============================================================
   VARIABLES
   ============================================================ */

let scene = null;
let camera = null;
let renderer = null;

/*
 * Three.js puede llegar como variable global o como módulo ES.
 * Usamos un fallback para que el cerebro funcione con ambos HTML.
 */
let THREE = window.THREE || null;
let threeLoadPromise = null;

let brainGroup = null;
let brainParticles = null;
let brainConnections = null;
let ambientParticles = null;
let coreGlow = null;

let animationFrame = null;

let currentState = "idle";
let pulsePower = 1;
let pulseTarget = 1;

let baseBrainPositions = null;
let brainPositionAttribute = null;

let ambientBasePositions = null;
let ambientPositionAttribute = null;


/* ============================================================
   CONFIGURACIÓN
   ============================================================ */

const CONFIG = {

    /* Cerebro */
    brainParticles: 2400,

    /* Conexiones internas */
    connectionDistance: 1.05,
    maxConnectionsPerPoint: 3,

    /* Partículas alrededor */
    ambientParticles: 180,

    /* Animación */
    rotationSpeed: 0.00065,
    floatSpeed: 0.00065,
    particleMotion: 0.00125,

    /* Colores */
    cyan: 0x00f6ff,
    cyanSoft: 0x00dfff,
    white: 0xffffff,
    green: 0x00ffcc,
    red: 0xff3355

};


/* ============================================================
   UTILIDADES
   ============================================================ */

function randomRange(min, max) {

    return min +
        Math.random() *
        (max - min);

}


function clamp(value, min, max) {

    return Math.max(
        min,
        Math.min(max, value)
    );

}


/* ============================================================
   TEXTURA DE PARTÍCULA
   ============================================================ */

function createGlowTexture() {

    const canvas =
        document.createElement("canvas");

    canvas.width = 64;
    canvas.height = 64;

    const ctx =
        canvas.getContext("2d");

    const gradient =
        ctx.createRadialGradient(
            32,
            32,
            0,
            32,
            32,
            32
        );

    gradient.addColorStop(
        0,
        "rgba(255,255,255,1)"
    );

    gradient.addColorStop(
        0.12,
        "rgba(150,255,255,1)"
    );

    gradient.addColorStop(
        0.35,
        "rgba(0,246,255,0.65)"
    );

    gradient.addColorStop(
        0.70,
        "rgba(0,246,255,0.12)"
    );

    gradient.addColorStop(
        1,
        "rgba(0,0,0,0)"
    );

    ctx.fillStyle = gradient;

    ctx.fillRect(
        0,
        0,
        64,
        64
    );

    return new THREE.CanvasTexture(
        canvas
    );

}


/* ============================================================
   GENERAR PUNTOS DEL CEREBRO
   ============================================================ */

function generateBrainPoints() {

    const points = [];

    const addEllipsoid = (
        count,
        center,
        radius
    ) => {

        for (
            let i = 0;
            i < count;
            i++
        ) {

            /*
             * Distribución volumétrica.
             */

            const u =
                Math.random();

            const v =
                Math.random();

            const theta =
                2 *
                Math.PI *
                u;

            const phi =
                Math.acos(
                    2 * v - 1
                );

            const r =
                Math.cbrt(
                    Math.random()
                );


            let x =
                r *
                Math.sin(phi) *
                Math.cos(theta);

            let y =
                r *
                Math.sin(phi) *
                Math.sin(theta);

            let z =
                r *
                Math.cos(phi);


            x *= radius.x;
            y *= radius.y;
            z *= radius.z;


            /*
             * Pliegues orgánicos.
             * No son una esfera perfecta.
             */

            const foldA =
                Math.sin(
                    y * 2.7 +
                    z * 1.25
                ) * 0.10;

            const foldB =
                Math.sin(
                    y * 5.1 -
                    z * 2.0
                ) * 0.055;

            const foldC =
                Math.sin(
                    z * 4.3 +
                    x * 1.7
                ) * 0.045;


            x +=
                foldA +
                foldB;

            z +=
                foldC;


            /*
             * Separación central.
             */

            if (
                Math.abs(
                    x + center.x
                ) < 0.16
            ) {

                x +=
                    x < 0
                        ? -0.16
                        : 0.16;

            }


            points.push(
                new THREE.Vector3(
                    x + center.x,
                    y + center.y,
                    z + center.z
                )
            );

        }

    };


    /*
     * Hemisferio izquierdo.
     */

    addEllipsoid(
        1000,
        new THREE.Vector3(
            -0.72,
            0.15,
            0
        ),
        new THREE.Vector3(
            1.62,
            2.05,
            2.05
        )
    );


    /*
     * Hemisferio derecho.
     */

    addEllipsoid(
        1000,
        new THREE.Vector3(
            0.72,
            0.15,
            0
        ),
        new THREE.Vector3(
            1.62,
            2.05,
            2.05
        )
    );


    /*
     * Cerebelo.
     */

    addEllipsoid(
        280,
        new THREE.Vector3(
            0,
            -1.38,
            -1.25
        ),
        new THREE.Vector3(
            1.15,
            0.70,
            0.85
        )
    );


    /*
     * Tronco encefálico.
     */

    addEllipsoid(
        110,
        new THREE.Vector3(
            0,
            -2.20,
            -0.55
        ),
        new THREE.Vector3(
            0.42,
            0.95,
            0.48
        )
    );


    return points;

}


/* ============================================================
   CREAR CEREBRO
   ============================================================ */

function createBrain() {

    brainGroup =
        new THREE.Group();


    const points =
        generateBrainPoints();


    /*
     * Escala global.
     * El cerebro entra completo en el viewport.
     */

    brainGroup.scale.set(
        9,
        9,
        9
    );


    /*
     * Posición.
     */

    brainGroup.position.set(
        0,
        0.25,
        0
    );


    /* ========================================================
       PARTÍCULAS DEL CEREBRO
       ======================================================== */

    const positions = [];

    points.forEach(
        point => {

            positions.push(
                point.x,
                point.y,
                point.z
            );

        }
    );


    const geometry =
        new THREE.BufferGeometry();

    geometry.setAttribute(
        "position",
        new THREE.Float32BufferAttribute(
            positions,
            3
        )
    );


    brainPositionAttribute =
        geometry.getAttribute(
            "position"
        );


    baseBrainPositions =
        new Float32Array(
            brainPositionAttribute.array
        );


    const particleMaterial =
        new THREE.PointsMaterial({

            color:
                CONFIG.cyan,

            size:
                0.075,

            map:
                createGlowTexture(),

            transparent:
                true,

            opacity:
                0.88,

            blending:
                THREE.AdditiveBlending,

            depthWrite:
                false

        });


    brainParticles =
        new THREE.Points(
            geometry,
            particleMaterial
        );


    brainGroup.add(
        brainParticles
    );


    /* ========================================================
       CONEXIONES NEURONALES
       ======================================================== */

    const linePositions = [];

    /*
     * Para evitar N² excesivo:
     * cada punto busca conexiones limitadas.
     */

    for (
        let i = 0;
        i < points.length;
        i++
    ) {

        let connections = 0;

        const a =
            points[i];


        /*
         * Buscar vecinos cercanos.
         * Muestreo parcial para mantener fluidez.
         */

        const searchStart =
            Math.max(
                0,
                i - 90
            );

        const searchEnd =
            Math.min(
                points.length,
                i + 90
            );


        for (
            let j = searchStart;
            j < searchEnd;
            j++
        ) {

            if (
                j === i
            ) {
                continue;
            }


            const b =
                points[j];


            const distance =
                a.distanceTo(b);


            if (
                distance <
                CONFIG.connectionDistance
            ) {

                /*
                 * Solo una parte de las
                 * conexiones para que
                 * el cerebro respire.
                 */

                if (
                    Math.random() >
                    0.36
                ) {
                    continue;
                }


                linePositions.push(

                    a.x,
                    a.y,
                    a.z,

                    b.x,
                    b.y,
                    b.z

                );


                connections++;


                if (
                    connections >=
                    CONFIG.maxConnectionsPerPoint
                ) {
                    break;
                }

            }

        }

    }


    const lineGeometry =
        new THREE.BufferGeometry();

    lineGeometry.setAttribute(
        "position",
        new THREE.Float32BufferAttribute(
            linePositions,
            3
        )
    );


    const lineMaterial =
        new THREE.LineBasicMaterial({

            color:
                CONFIG.cyanSoft,

            transparent:
                true,

            opacity:
                0.19,

            blending:
                THREE.AdditiveBlending,

            depthWrite:
                false

        });


    brainConnections =
        new THREE.LineSegments(
            lineGeometry,
            lineMaterial
        );


    brainGroup.add(
        brainConnections
    );


    /* ========================================================
   CEREBRO CENTRAL NEON
   ELIMINAR FONDO DEL PNG
   ======================================================== */

const brainTextureLoader =
    new THREE.TextureLoader();

const brainImage =
    brainTextureLoader.load(
        "/static/img/brain_neon.png"
    );

/*
 * Canvas intermedio para eliminar
 * automáticamente el fondo oscuro
 * del PNG.
 */

const brainCanvas =
    document.createElement("canvas");

const brainCtx =
    brainCanvas.getContext("2d");

brainImage.colorSpace =
    THREE.SRGBColorSpace;

brainImage.onUpdate = null;

const brainMaterial =
    new THREE.SpriteMaterial({

        map:
            brainImage,

        color:
            CONFIG.white,

        transparent:
            true,

        opacity:
            0.95,

        blending:
            THREE.AdditiveBlending,

        depthWrite:
            false
    });

coreGlow =
    new THREE.Sprite(
        brainMaterial
    );
coreGlow.position.set(
    0,
    0.05,
    0.45
);

/*
 * Tamaño inicial del cerebro.
 * Puedes aumentar estos valores después.
 */
coreGlow.scale.set(
    2,
    2,
    2
);

brainGroup.add(
    coreGlow
);


    scene.add(
        brainGroup
    );

}


/* ============================================================
   PARTÍCULAS ALREDEDOR DEL CEREBRO
   ============================================================ */

function createAmbientParticles() {

    const positions = [];

    /*
     * CAMPO NEURONAL DE FONDO
     *
     * Se extiende por todo el viewport.
     * El cerebro central NO se modifica.
     */

    const aspect =
        window.innerWidth /
        Math.max(
            window.innerHeight,
            1
        );

    /*
     * Ancho dinámico según pantalla.
     *
     * En pantallas anchas aumentamos X.
     */
    const fieldWidth =
        Math.max(
            18,
            9 * aspect
        );

    const fieldHeight = 7.5;

    const fieldDepth = 5.5;


    /*
     * Cantidad de partículas
     */
    const particleCount = 900;


    for (
        let i = 0;
        i < particleCount;
        i++
    ) {

        /*
         * Distribución horizontal completa
         */
        const x =
            randomRange(
                -fieldWidth,
                fieldWidth
            );


        /*
         * Distribución vertical
         */
        const y =
            randomRange(
                -fieldHeight,
                fieldHeight
            );


        /*
         * Profundidad
         */
        const z =
            randomRange(
                -fieldDepth,
                fieldDepth
            );


        positions.push(
            x,
            y,
            z
        );
    }


    const geometry =
        new THREE.BufferGeometry();


    geometry.setAttribute(
        "position",
        new THREE.Float32BufferAttribute(
            positions,
            3
        )
    );


    ambientPositionAttribute =
        geometry.getAttribute(
            "position"
        );


    ambientBasePositions =
        new Float32Array(
            ambientPositionAttribute.array
        );


    const material =
        new THREE.PointsMaterial({

            color:
                CONFIG.cyan,

            size:
                0.055,

            map:
                createGlowTexture(),

            transparent:
                true,

            opacity:
                0.48,

            blending:
                THREE.AdditiveBlending,

            depthWrite:
                false
        });


    ambientParticles =
        new THREE.Points(
            geometry,
            material
        );


    scene.add(
        ambientParticles
    );
}


/* ============================================================
   ESCENA
   ============================================================ */

function createScene() {

    scene =
        new THREE.Scene();


    camera =
        new THREE.PerspectiveCamera(
            32,
            1,
            0.1,
            100
        );


    /*
     * Distancia pensada para que el
     * cerebro completo quede visible.
     */

    camera.position.set(
        0,
        0,
        25.5
    );


    camera.lookAt(
        0,
        0,
        0
    );


    renderer =
        new THREE.WebGLRenderer({

            alpha:
                true,

            antialias:
                true,

            powerPreference:
                "high-performance"

        });


    renderer.setPixelRatio(
        Math.min(
            window.devicePixelRatio,
            2
        )
    );


    renderer.setClearColor(
        0x000000,
        0
    );


    createBrain();

    createAmbientParticles();

}


/* ============================================================
   RESIZE
   ============================================================ */

function resize() {

    const container =
        document.getElementById(
            "brainHologram"
        );


    if (!container) {
        return;
    }


    const width =
        container.clientWidth;

    const height =
        container.clientHeight;


    if (
        width <= 0 ||
        height <= 0
    ) {
        return;
    }


    camera.aspect =
        width / height;


    camera.updateProjectionMatrix();


    renderer.setSize(
        width,
        height,
        false
    );

}


/* ============================================================
   ANIMACIÓN DE PARTÍCULAS DEL CEREBRO
   ============================================================ */

function animateBrainParticles(time) {

    if (
        !brainPositionAttribute ||
        !baseBrainPositions
    ) {
        return;
    }


    const positions =
        brainPositionAttribute.array;


    const motion =
        0.018 *
        pulsePower;


    for (
        let i = 0;
        i < positions.length;
        i += 3
    ) {

        const bx =
            baseBrainPositions[i];

        const by =
            baseBrainPositions[i + 1];

        const bz =
            baseBrainPositions[i + 2];


        const phase =
            (
                i * 0.013
            );


        positions[i] =
            bx +
            Math.sin(
                time *
                    0.0011 +
                phase
            ) *
            motion;


        positions[i + 1] =
            by +
            Math.cos(
                time *
                    0.0010 +
                phase
            ) *
            motion;


        positions[i + 2] =
            bz +
            Math.sin(
                time *
                    0.0008 +
                phase
            ) *
            motion *
            0.7;

    }


    brainPositionAttribute.needsUpdate =
        true;

}


/* ============================================================
   ANIMACIÓN DE PARTÍCULAS EXTERNAS
   ============================================================ */

function animateAmbientParticles(time) {

    if (
        !ambientPositionAttribute ||
        !ambientBasePositions
    ) {
        return;
    }


    const positions =
        ambientPositionAttribute.array;


    for (
        let i = 0;
        i < positions.length;
        i += 3
    ) {

        const bx =
            ambientBasePositions[i];

        const by =
            ambientBasePositions[i + 1];

        const bz =
            ambientBasePositions[i + 2];


        const phase =
            i * 0.027;


        const orbit =
            time *
            0.00012;


        positions[i] =
            bx *
            Math.cos(orbit) -
            bz *
            Math.sin(orbit);


        positions[i + 1] =
            by +
            Math.sin(
                time *
                    0.001 +
                phase
            ) *
            0.10;


        positions[i + 2] =
            bx *
            Math.sin(orbit) +
            bz *
            Math.cos(orbit);

    }


    ambientPositionAttribute.needsUpdate =
        true;

}


/* ============================================================
   LOOP PRINCIPAL
   ============================================================ */

function animate() {

    animationFrame =
        requestAnimationFrame(
            animate
        );


    if (
        !brainGroup
    ) {
        return;
    }


    const time =
        Date.now();


    /*
     * Movimiento global suave.
     */

    brainGroup.rotation.y +=
        CONFIG.rotationSpeed;


    brainGroup.rotation.x =
        Math.sin(
            time *
            0.00022
        ) *
        0.035;


    brainGroup.position.y =
        0.25 +
        Math.sin(
            time *
            CONFIG.floatSpeed
        ) *
        0.16;


    /*
     * Movimiento de neuronas.
     */

    animateBrainParticles(
        time
    );


    animateAmbientParticles(
        time
    );


    /*
     * Pulse suavizado.
     */

    pulsePower +=
        (
            pulseTarget -
            pulsePower
        ) *
        0.045;


    /*
     * Intensidad de partículas.
     */

    if (
        brainParticles
    ) {

        brainParticles.material.size =
            0.065 +
            (
                0.025 *
                pulsePower
            );


        brainParticles.material.opacity =
            clamp(
                0.62 +
                (
                    0.11 *
                    pulsePower
                ),
                0.55,
                0.96
            );

    }


    /*
     * Intensidad de conexiones.
     */

    if (
        brainConnections
    ) {

        brainConnections.material.opacity =
            clamp(
                0.12 +
                (
                    0.07 *
                    pulsePower
                ),
                0.10,
                0.34
            );

    }


    /*
     * Núcleo pulsante.
     */

    if (
        coreGlow
    ) {

        const coreScale =
            1 +
            (
                Math.sin(
                    time *
                    0.0025
                ) *
                0.18 *
                pulsePower
            );


        coreGlow.scale.set(
            coreScale,
            coreScale,
            coreScale
        );


        coreGlow.material.opacity =
            clamp(
                0.65 +
                (
                    0.10 *
                    pulsePower
                ),
                0.60,
                1
            );

    }


    /*
     * Partículas externas.
     */

    if (
        ambientParticles
    ) {

        ambientParticles.material.opacity =
            clamp(
                0.42 +
                (
                    0.10 *
                    pulsePower
                ),
                0.35,
                0.75
            );

    }


    renderer.render(
        scene,
        camera
    );

}


/* ============================================================
   ESTADO IDLE
   ============================================================ */

function idle() {

    currentState =
        "idle";

    pulseTarget =
        1;

}


/* ============================================================
   ACTIVAR
   ============================================================ */

function activate(
    agent = null
) {

    currentState =
        "active";


    pulseTarget =
        3.4;


    if (
        brainParticles
    ) {

        brainParticles.material.color
            .setHex(
                CONFIG.cyan
            );

    }


    if (
        brainConnections
    ) {

        brainConnections.material.color
            .setHex(
                CONFIG.cyanSoft
            );

    }


    if (
        coreGlow
    ) {

        coreGlow.material.color
            .setHex(
                CONFIG.white
            );

    }


    console.log(
        "🧠 Brain ACTIVE:",
        agent || "IA"
    );


    /*
     * Después de un pulso vuelve
     * gradualmente a estado normal.
     */

    setTimeout(
        () => {

            if (
                currentState ===
                "active"
            ) {

                pulseTarget =
                    1;

            }

        },
        520
    );

}


/* ============================================================
   COMPLETADO
   ============================================================ */

function complete(
    agent = null
) {

    currentState =
        "completed";


    pulseTarget =
        2.2;


    if (
        brainParticles
    ) {

        brainParticles.material.color
            .setHex(
                CONFIG.green
            );

    }


    if (
        brainConnections
    ) {

        brainConnections.material.color
            .setHex(
                CONFIG.green
            );

    }


    if (
        coreGlow
    ) {

        coreGlow.material.color
            .setHex(
                CONFIG.green
            );

    }


    console.log(
        "🧠 Brain COMPLETE:",
        agent || "IA"
    );


    setTimeout(
        () => {

            if (
                currentState ===
                "completed"
            ) {

                if (
                    brainParticles
                ) {

                    brainParticles.material.color
                        .setHex(
                            CONFIG.cyan
                        );

                }


                if (
                    brainConnections
                ) {

                    brainConnections.material.color
                        .setHex(
                            CONFIG.cyanSoft
                        );

                }


                if (
                    coreGlow
                ) {

                    coreGlow.material.color
                        .setHex(
                            CONFIG.white
                        );

                }


                idle();

            }

        },
        900
    );

}


/* ============================================================
   ERROR
   ============================================================ */

function error() {

    currentState =
        "error";


    pulseTarget =
        4.0;


    if (
        brainParticles
    ) {

        brainParticles.material.color
            .setHex(
                CONFIG.red
            );

    }


    if (
        brainConnections
    ) {

        brainConnections.material.color
            .setHex(
                CONFIG.red
            );

    }


    if (
        coreGlow
    ) {

        coreGlow.material.color
            .setHex(
                CONFIG.red
            );

    }


    console.log(
        "🧠 Brain ERROR"
    );

}


/* ============================================================
   INIT
   ============================================================ */

function loadThree() {

    if (THREE) {
        return Promise.resolve(THREE);
    }

    if (threeLoadPromise) {
        return threeLoadPromise;
    }

    console.log(
        "🧠 Three.js no está disponible como global. Cargando módulo..."
    );

    threeLoadPromise = import(
        "https://cdn.jsdelivr.net/npm/three@0.179.1/build/three.module.js"
    )
        .then((threeModule) => {

            THREE = threeModule;
            window.THREE = threeModule;

            console.log(
                "🧠 Three.js cargado correctamente:",
                threeModule.REVISION
            );

            return THREE;
        })
        .catch((error) => {

            console.error(
                "🧠 Brain Hologram: no se pudo cargar Three.js.",
                error
            );

            threeLoadPromise = null;
            throw error;
        });

    return threeLoadPromise;
}


function init() {

    if (window.__brainHologramInitialized) {
        console.log("🧠 Brain Hologram: ya estaba iniciado.");
        return;
    }

    window.__brainHologramInitialized = true;

    const container =
        document.getElementById(
            "brainHologram"
        );

    if (!container) {
        console.warn(
            "Brain Hologram: #brainHologram no encontrado."
        );
        return;
    }

    loadThree()
        .then(() => {

            if (renderer) {
                return;
            }

            createScene();

            container.appendChild(
                renderer.domElement
            );

            resize();

            window.addEventListener(
                "resize",
                resize
            );

            animate();

            console.log(
                "🧠 Organic Neural Brain iniciado."
            );
        })
        .catch(() => {
            /* Error ya informado por loadThree(). */
        });
}


/* ============================================================
   API GLOBAL
   ============================================================ */

window.brainHologram = {

    init,

    idle,

    activate,

    complete,

    error

};
