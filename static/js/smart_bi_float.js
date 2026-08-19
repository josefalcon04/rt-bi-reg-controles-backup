/* ============================================================
   SMART BI ASSISTANT
   JS INDEPENDIENTE
   ============================================================ */

document.addEventListener("DOMContentLoaded", function () {

    const button = document.getElementById("sbiaButton");
    const windowChat = document.getElementById("sbiaWindow");

    const closeButton = document.getElementById("sbiaClose");
    const minimizeButton = document.getElementById("sbiaMinimize");
    const maximizeButton = document.getElementById("sbiaMaximize");

    const form = document.getElementById("sbiaForm");
    const input = document.getElementById("sbiaInput");
    const messages = document.getElementById("sbiaMessages");

    /* ========================================================
       CONFIGURACIÓN
       ======================================================== */

    const STORAGE_KEY = "smart_bi_assistant_history";

    if (!button || !windowChat) {
        console.warn("[SBIA] Elementos del chat no encontrados.");
        return;
    }

    console.log("[SBIA] Chatbox inicializado correctamente.");

    /* ========================================================
       HISTORIAL
       ======================================================== */

    function obtenerHistorial() {

        try {

            const historial =
                sessionStorage.getItem(STORAGE_KEY);

            if (!historial) {
                return [];
            }

            return JSON.parse(historial);

        } catch (error) {

            console.error(
                "[SBIA] Error leyendo historial:",
                error
            );

            return [];
        }
    }


    function guardarHistorial(historial) {

        try {

            sessionStorage.setItem(
                STORAGE_KEY,
                JSON.stringify(historial)
            );

        } catch (error) {

            console.error(
                "[SBIA] Error guardando historial:",
                error
            );
        }
    }


    function guardarMensaje(texto, tipo) {

        const historial =
            obtenerHistorial();

        historial.push({
            texto: texto,
            tipo: tipo,
            fecha: new Date().toISOString()
        });

        guardarHistorial(historial);
    }


    function cargarHistorial() {

        if (!messages) {
            return;
        }

        const historial =
            obtenerHistorial();

        if (!historial.length) {
            return;
        }

        console.log(
            "[SBIA] Restaurando historial:",
            historial.length,
            "mensajes"
        );

        messages.innerHTML = "";

        historial.forEach(function (mensaje) {

            agregarMensajeDOM(
                mensaje.texto,
                mensaje.tipo
            );

        });

    }


    /* ========================================================
       LIMPIAR HISTORIAL
       ======================================================== */

    function limpiarHistorialChat() {

        try {

            sessionStorage.removeItem(
                STORAGE_KEY
            );

            if (messages) {
                messages.innerHTML = "";
            }

            console.log(
                "[SBIA] Historial del chat eliminado."
            );

        } catch (error) {

            console.error(
                "[SBIA] Error limpiando historial:",
                error
            );
        }
    }


    /*
       Lo dejamos disponible globalmente para que
       el botón "Cerrar sesión" pueda llamarlo.
    */

    window.SBIA_limpiarHistorial =
        limpiarHistorialChat;


    /* ========================================================
       ABRIR
       ======================================================== */

    function abrirChat() {

        windowChat.classList.add(
            "sbia-open"
        );

        windowChat.setAttribute(
            "aria-hidden",
            "false"
        );

        setTimeout(() => {

            if (input) {
                input.focus();
            }

        }, 150);
    }


    /* ========================================================
       CERRAR
       ======================================================== */

    function cerrarChat() {

        /*
           IMPORTANTE:

           NO borrar historial aquí.

           Cerrar el chat NO significa cerrar sesión.
        */

        windowChat.classList.remove(
            "sbia-open"
        );

        windowChat.setAttribute(
            "aria-hidden",
            "true"
        );
    }


    /* ========================================================
       TOGGLE
       ======================================================== */

    button.addEventListener(
        "click",
        function () {

            if (
                windowChat.classList.contains(
                    "sbia-open"
                )
            ) {

                cerrarChat();

            } else {

                abrirChat();

            }

        }
    );


    /* ========================================================
       CERRAR
       ======================================================== */

    if (closeButton) {

        closeButton.addEventListener(
            "click",
            function () {

                cerrarChat();

            }
        );

    }


    /* ========================================================
       MINIMIZAR
       ======================================================== */

    if (minimizeButton) {

        minimizeButton.addEventListener(
            "click",
            function () {

                windowChat.classList.toggle(
                    "sbia-minimized"
                );

            }
        );

    }


    /* ========================================================
       MAXIMIZAR
       ======================================================== */

    if (maximizeButton) {

        maximizeButton.addEventListener(
            "click",
            function () {

                windowChat.classList.toggle(
                    "sbia-maximized"
                );

            }
        );

    }


    /* ========================================================
       ENTER
       ======================================================== */

    if (input) {

        input.addEventListener(
            "keydown",
            function (event) {

                if (
                    event.key === "Enter" &&
                    !event.shiftKey
                ) {

                    event.preventDefault();

                    if (form) {
                        form.requestSubmit();
                    }

                }

            }
        );

    }


    /* ========================================================
       SUBMIT
       ======================================================== */

    if (form) {

        form.addEventListener(
            "submit",
            async function (event) {

                event.preventDefault();

                const pregunta =
                    input.value.trim();

                if (!pregunta) {
                    return;
                }


                /* ============================================
                   MOSTRAR PREGUNTA
                   ============================================ */

                agregarMensaje(
                    pregunta,
                    "user"
                );

                input.value = "";


                /* ============================================
                   INDICADOR DE PROCESAMIENTO
                   ============================================ */

                const thinking =
                    agregarPensando();


                try {

                    const response =
                        await fetch(
                            "/chatbox/ask",
                            {
                                method: "POST",

                                headers: {
                                    "Content-Type":
                                        "application/json"
                                },

                                body: JSON.stringify({
                                    message:
                                        pregunta
                                })
                            }
                        );


                    if (!response.ok) {

                        throw new Error(
                            "Error HTTP " +
                            response.status
                        );

                    }


                    const data =
                        await response.json();


                    /* ========================================
                       ELIMINAR "PENSANDO"
                       ======================================== */

                    eliminarPensando(
                        thinking
                    );


                    const respuesta =
                        data.respuesta ||
                        data.response ||
                        "No se recibió respuesta.";


                    /* ========================================
                       MOSTRAR RESPUESTA
                       ======================================== */

                    agregarMensaje(
                        respuesta,
                        "bot"
                    );


                } catch (error) {

                    console.error(
                        "[SBIA] Error:",
                        error
                    );


                    eliminarPensando(
                        thinking
                    );


                    agregarMensaje(
                        "⚠️ Ocurrió un error al procesar la consulta.",
                        "bot"
                    );

                }

            }
        );

    }


    /* ========================================================
       AGREGAR MENSAJE
       ======================================================== */

    function agregarMensaje(
        texto,
        tipo
    ) {

        if (!messages) {
            return;
        }


        /*
           Primero lo mostramos.
        */

        agregarMensajeDOM(
            texto,
            tipo
        );


        /*
           Luego lo guardamos.

           Esto es lo importante para que
           sobreviva al cambio de menú.
        */

        guardarMensaje(
            texto,
            tipo
        );

    }

    /* ========================================================
   FORMATEADOR DE RESPUESTAS DEL ASISTENTE
   ======================================================== */

function escaparHTML(texto) {
    const div = document.createElement("div");
    div.textContent = texto ?? "";
    return div.innerHTML;
}

function formatearRespuestaChat(texto) {

    if (!texto) {
        return "";
    }

    let contenido = String(texto).trim();
    let tiempo = "";

    const tiempoMatch = contenido.match(
        /\*Procesado por Router en ([^*]+)\*/
    );

    if (tiempoMatch) {
        tiempo = tiempoMatch[1].trim();

        contenido = contenido.replace(
            tiempoMatch[0],
            ""
        ).trim();
    }

    /*
     * Detectar respuesta de metadata.
     */
    const esMetadata =
        /Encontré\s+\d+\s+tablas?/i.test(contenido) &&
        /Definición:/i.test(contenido) &&
        /Campo relacionado:/i.test(contenido);

    /*
     * Respuesta normal.
     */
    if (!esMetadata) {

        let html = escaparHTML(
            contenido
        ).replace(/\r?\n/g, "<br>");

        if (tiempo) {

            html += `
                <div class="sbia-processing-time">
                    Procesado por Router en
                    ${escaparHTML(tiempo)}
                </div>
            `;
        }

        return html;
    }

    /*
     * ====================================================
     * RESPUESTA DE METADATA
     * ====================================================
     */

    let html = "";

    /*
     * Encabezado.
     */
    const encabezadoMatch = contenido.match(
        /^([\s\S]*?)(?=\s*1\.\s+)/i
    );

    if (encabezadoMatch) {

        html += `
            <div class="sbia-result-header">

                <div class="sbia-result-title">
                    🔎 Resultado de búsqueda
                </div>

                <div class="sbia-result-summary">
                    ${escaparHTML(
                        encabezadoMatch[1].trim()
                    )}
                </div>

            </div>
        `;
    }

    /*
     * Detectar tablas.
     */
    const tablaRegex =
        /(\d+)\.\s+([^\s]+)\s+Definición:\s*(.*?)(?=\s+\d+\.\s+|Si quieres,|$)/gis;

    let match;

    while (
        (match = tablaRegex.exec(contenido)) !== null
    ) {

        const numero =
            match[1];

        const nombreCompleto =
            match[2];

        let bloque =
            match[3].trim();

        /*
         * Separar definición y campo.
         */
        const campoIndex =
            bloque.search(
                /Campo relacionado:/i
            );

        let definicion =
            bloque;

        let campos =
            "";

        if (campoIndex !== -1) {

            definicion =
                bloque
                    .substring(
                        0,
                        campoIndex
                    )
                    .trim();

            campos =
                bloque
                    .substring(
                        campoIndex +
                        "Campo relacionado:".length
                    )
                    .trim();
        }

        /*
         * Separar DATABASE.TABLA
         */
        let database =
            "";

        let tabla =
            nombreCompleto;

        const partes =
            nombreCompleto.split(".");

        if (partes.length >= 2) {

            database =
                partes
                    .slice(0, -1)
                    .join(".");

            tabla =
                partes[
                    partes.length - 1
                ];
        }

        /*
         * Limpiar viñeta.
         */
        campos =
            campos
                .replace(
                    /^[•\-]\s*/g,
                    ""
                )
                .trim();

        let camposHTML =
            "";

        if (campos) {

            let campoTexto =
                escaparHTML(
                    campos
                );

            /*
             * Resaltar nombres de campos.
             */
            campoTexto =
                campoTexto.replace(
                    /\b([A-Z][A-Z0-9_]{2,})\b/g,
                    "<strong>$1</strong>"
                );

            camposHTML = `
                <div class="sbia-result-section">

                    <div class="sbia-result-label">
                        🔑 Campo relacionado
                    </div>

                    <div class="sbia-result-field">
                        ${campoTexto}
                    </div>

                </div>
            `;
        }

        /*
         * Tarjeta de tabla.
         */
        html += `
            <div class="sbia-table-card">

                <div class="sbia-table-number">
                    ${escaparHTML(numero)}
                </div>

                <div class="sbia-table-content">

                    <div class="sbia-table-name">
                        ${escaparHTML(tabla)}
                    </div>

                    ${
                        database
                            ? `
                                <div class="sbia-table-database">
                                    ${escaparHTML(database)}
                                </div>
                              `
                            : ""
                    }

                    <div class="sbia-result-section">

                        <div class="sbia-result-label">
                            📋 Definición
                        </div>

                        <div class="sbia-result-definition">
                            ${escaparHTML(definicion)}
                        </div>

                    </div>

                    ${camposHTML}

                </div>

            </div>
        `;
    }

    /*
     * Mensaje final.
     */
    const mensajeFinalMatch =
        contenido.match(
            /(Si quieres,[\s\S]*)$/i
        );

    if (mensajeFinalMatch) {

        html += `
            <div class="sbia-result-followup">
                💡 ${escaparHTML(
                    mensajeFinalMatch[1].trim()
                )}
            </div>
        `;
    }

    /*
     * Tiempo.
     */
    if (tiempo) {

        html += `
            <div class="sbia-processing-time">
                Procesado por Router en
                ${escaparHTML(tiempo)}
            </div>
        `;
    }

    return html;
}
    /* ========================================================
       CREAR MENSAJE EN DOM
       ======================================================== */

    function agregarMensajeDOM(
        texto,
        tipo
    ) {

        if (!messages) {
            return;
        }


        const message =
            document.createElement("div");

        message.className =
            "sbia-message " +
            (
                tipo === "user"
                    ? "sbia-message-user"
                    : "sbia-message-bot"
            );


        const avatar =
            document.createElement("div");

        avatar.className =
            "sbia-message-avatar";

        avatar.textContent =
            tipo === "user"
                ? "👤"
                : "🤖";


        const bubble =
            document.createElement("div");

        bubble.className =
            "sbia-bubble";


        /*
           Mantiene el texto tal como viene
           y evita inyectar HTML.
        */

        if (tipo === "bot") {

    bubble.innerHTML =
        formatearRespuestaChat(texto);

} else {

    bubble.textContent =
        texto;
}


        message.appendChild(
            avatar
        );

        message.appendChild(
            bubble
        );

        messages.appendChild(
            message
        );


        messages.scrollTop =
            messages.scrollHeight;

    }


    /* ========================================================
       INDICADOR "PENSANDO"
       ======================================================== */

    function agregarPensando() {

        if (!messages) {
            return null;
        }


        const message =
            document.createElement("div");

        message.className =
            "sbia-message sbia-message-bot sbia-thinking-message";


        const avatar =
            document.createElement("div");

        avatar.className =
            "sbia-message-avatar";

        avatar.textContent =
            "🤖";


        const bubble =
            document.createElement("div");

        bubble.className =
            "sbia-bubble sbia-thinking";


        bubble.innerHTML = `
            <span></span>
            <span></span>
            <span></span>
        `;


        message.appendChild(
            avatar
        );

        message.appendChild(
            bubble
        );

        messages.appendChild(
            message
        );


        messages.scrollTop =
            messages.scrollHeight;


        return message;

    }


    /* ========================================================
       ELIMINAR "PENSANDO"
       ======================================================== */

    function eliminarPensando(
        elemento
    ) {

        if (
            elemento &&
            elemento.parentNode
        ) {

            elemento.parentNode.removeChild(
                elemento
            );

        }

    }


    /* ========================================================
       LOGOUT
       ======================================================== */

    /*
       IMPORTANTE:

       El historial SOLO se limpia cuando realmente
       se ejecuta el cierre de sesión.

       Buscamos botones/enlaces comunes de logout.
    */

    const logoutSelectors = [
        "#logout",
        "#btnLogout",
        "#logoutButton",
        ".logout",
        ".btn-logout",
        "[data-logout]",
        "a[href*='logout']",
        "a[href*='cerrar-sesion']",
        "a[href*='cerrar_sesion']"
    ];


    logoutSelectors.forEach(
        function (selector) {

            document
                .querySelectorAll(selector)
                .forEach(function (element) {

                    element.addEventListener(
                        "click",
                        function () {

                            console.log(
                                "[SBIA] Cerrando sesión. " +
                                "Eliminando historial."
                            );

                            limpiarHistorialChat();

                        }
                    );

                });

        }
    );


    /* ========================================================
       RESTAURAR HISTORIAL
       ======================================================== */

    cargarHistorial();

});