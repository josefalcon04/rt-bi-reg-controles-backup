/* =========================================================
   SMART BI ASSISTANT
   CHAT FLOTANTE
   =========================================================

   Funciones:
   - Abrir / cerrar
   - Botón circular
   - Minimizar
   - Maximizar / restaurar
   - Redimensionar
   - Enviar con Enter
   - Enviar con botón
   - Mantener historial durante la sesión
   - Recuperar historial al navegar entre módulos

   COMPORTAMIENTO:
   - Al cargar una página:
        CHAT  -> CERRADO
        🤖    -> VISIBLE

   - El chat SOLO se abre al hacer click en 🤖
   ========================================================= */


/* =========================================================
   CONFIGURACIÓN DE SESIÓN
   ========================================================= */

const CHAT_SESSION_KEY =
    "smart_bi_session_active";

const CHAT_HISTORY_KEY =
    "smartBiAssistantHistory";


/* =========================================================
   INICIALIZACIÓN
   ========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    function () {

        console.log(
            "🔥 CHAT FLOAT JS CARGADO"
        );


        /* =====================================================
           ELEMENTOS
           ===================================================== */

        const chatWindow =
            document.getElementById(
                "smartBiChat"
            );

        const openButton =
            document.getElementById(
                "chatOpenButton"
            );

        const minimizeButton =
            document.getElementById(
                "chatMinimize"
            );

        const maximizeButton =
            document.getElementById(
                "chatMaximize"
            );

        const closeButton =
            document.getElementById(
                "chatClose"
            );

        const sendButton =
            document.getElementById(
                "sendMessageButton"
            );

        const input =
            document.getElementById(
                "message"
            );

        const messages =
            document.getElementById(
                "smartBiMessages"
            );

        const status =
            document.getElementById(
                "chatStatus"
            );


        const resizeTopLeft =
            document.querySelector(
                ".chat-resize-tl"
            );

        const resizeBottomRight =
            document.querySelector(
                ".chat-resize-br"
            );


        /* =====================================================
           DEBUG
           ===================================================== */

        console.log(
            "Chat Window:",
            chatWindow
        );

        console.log(
            "Open Button:",
            openButton
        );

        console.log(
            "Minimize:",
            minimizeButton
        );

        console.log(
            "Maximize:",
            maximizeButton
        );

        console.log(
            "Close:",
            closeButton
        );

        console.log(
            "Send:",
            sendButton
        );

        console.log(
            "Input:",
            input
        );

        console.log(
            "Messages:",
            messages
        );


        /* =====================================================
           VALIDACIÓN
           ===================================================== */

        if (!chatWindow) {

            console.error(
                "❌ No se encontró #smartBiChat"
            );

            return;
        }


        if (!messages) {

            console.error(
                "❌ No se encontró #smartBiMessages"
            );

            return;
        }


        if (!input) {

            console.error(
                "❌ No se encontró #message"
            );

            return;
        }


        if (!sendButton) {

            console.error(
                "❌ No se encontró #sendMessageButton"
            );

            return;
        }


        /* =====================================================
           ESTADO INICIAL
           =====================================================

           IMPORTANTE:

           Cada página comienza con:

           CHAT  -> CERRADO
           BOTÓN -> VISIBLE

           No usamos CHAT_OPEN_KEY ni beforeunload
           para evitar que el estado anterior fuerce
           la apertura del chat.
           ===================================================== */

        chatWindow.classList.add(
            "closed"
        );

        chatWindow.classList.remove(
            "minimized"
        );

        chatWindow.classList.remove(
            "maximized"
        );


        if (openButton) {

            openButton.classList.add(
                "visible"
            );

            openButton.style.removeProperty(
                "display"
            );
        }


        console.log(
            "🔒 Chat iniciado CERRADO"
        );


        /* =====================================================
           HISTORIAL
           ===================================================== */

        function obtenerHistorial() {

            try {

                const historial =
                    sessionStorage.getItem(
                        CHAT_HISTORY_KEY
                    );


                if (!historial) {

                    return [];
                }


                return JSON.parse(
                    historial
                );

            }
            catch (error) {

                console.error(
                    "❌ Error leyendo historial:",
                    error
                );

                return [];
            }
        }


        function guardarHistorial(
            historial
        ) {

            try {

                sessionStorage.setItem(
                    CHAT_HISTORY_KEY,
                    JSON.stringify(
                        historial
                    )
                );

            }
            catch (error) {

                console.error(
                    "❌ Error guardando historial:",
                    error
                );
            }
        }


        /* =====================================================
           GUARDAR MENSAJE
           ===================================================== */

        function guardarMensaje(
            tipo,
            texto
        ) {

            const historial =
                obtenerHistorial();


            historial.push({

                tipo:
                    tipo,

                texto:
                    texto,

                fecha:
                    new Date()
                        .toISOString()

            });


            guardarHistorial(
                historial
            );
        }


        /* =====================================================
           CARGAR HISTORIAL
           ===================================================== */

        function cargarHistorial() {

            const historial =
                obtenerHistorial();


            console.log(
                "📚 Historial recuperado:",
                historial
            );


            if (
                !historial.length
            ) {

                return;
            }


            historial.forEach(
                function (mensaje) {

                    if (
                        mensaje.tipo ===
                        "usuario"
                    ) {

                        agregarMensajeUsuario(
                            mensaje.texto,
                            false
                        );
                    }


                    if (
                        mensaje.tipo ===
                        "bot"
                    ) {

                        agregarMensajeBot(
                            mensaje.texto,
                            false
                        );
                    }

                }
            );


            scrollChat();
        }


        /* =====================================================
           ABRIR CHAT
           ===================================================== */

        function abrirChat() {

            console.log(
                "🤖 Abriendo Smart BI Assistant"
            );


            chatWindow.classList.remove(
                "closed"
            );

            chatWindow.classList.remove(
                "minimized"
            );


            if (openButton) {

                openButton.classList.remove(
                    "visible"
                );

                openButton.style.setProperty(
                    "display",
                    "none",
                    "important"
                );
            }


            setTimeout(
                function () {

                    if (input) {

                        input.focus();
                    }


                    scrollChat();

                },
                100
            );
        }


        /* =====================================================
           CERRAR CHAT
           ===================================================== */

        function cerrarChat() {

            console.log(
                "❌ Cerrando Smart BI Assistant"
            );


            guardarHistorial(
                obtenerHistorial()
            );


            chatWindow.classList.add(
                "closed"
            );


            chatWindow.classList.remove(
                "minimized"
            );

            chatWindow.classList.remove(
                "maximized"
            );


            if (openButton) {

                openButton.classList.add(
                    "visible"
                );

                openButton.style.setProperty(
                    "display",
                    "flex",
                    "important"
                );
            }
        }


        /* =====================================================
           BOTÓN CIRCULAR
           ===================================================== */

        if (openButton) {

            openButton.addEventListener(
                "click",
                function (event) {

                    event.preventDefault();

                    event.stopPropagation();


                    abrirChat();

                }
            );
        }


        /* =====================================================
           BOTÓN CERRAR X
           ===================================================== */

        if (closeButton) {

            closeButton.addEventListener(
                "click",
                function (event) {

                    event.preventDefault();

                    event.stopPropagation();


                    cerrarChat();

                }
            );
        }


        /* =====================================================
           MINIMIZAR
           ===================================================== */

        if (minimizeButton) {

            minimizeButton.addEventListener(
                "click",
                function (event) {

                    event.preventDefault();

                    event.stopPropagation();


                    console.log(
                        "🟡 Minimizando chat"
                    );


                    chatWindow.classList.toggle(
                        "minimized"
                    );

                }
            );
        }


        /* =====================================================
           MAXIMIZAR / RESTAURAR
           ===================================================== */

        if (maximizeButton) {

            maximizeButton.addEventListener(
                "click",
                function (event) {

                    event.preventDefault();

                    event.stopPropagation();


                    console.log(
                        "🔵 Maximizando / restaurando chat"
                    );


                    chatWindow.classList.toggle(
                        "maximized"
                    );


                    if (
                        chatWindow.classList.contains(
                            "maximized"
                        )
                    ) {

                        maximizeButton.innerHTML =
                            "❐";

                        maximizeButton.title =
                            "Restaurar";

                    }
                    else {

                        maximizeButton.innerHTML =
                            "□";

                        maximizeButton.title =
                            "Maximizar";
                    }

                }
            );
        }


        /* =====================================================
           MENSAJE USUARIO
           ===================================================== */

        function agregarMensajeUsuario(
            texto,
            guardar = true
        ) {

            const row =
                document.createElement(
                    "div"
                );


            row.className =
                "chat-row user-row";


            const bubble =
                document.createElement(
                    "div"
                );


            bubble.className =
                "chat-bubble user-bubble";


            bubble.textContent =
                texto;


            row.appendChild(
                bubble
            );


            messages.appendChild(
                row
            );


            if (guardar) {

                guardarMensaje(
                    "usuario",
                    texto
                );
            }


            scrollChat();
        }


        /* =====================================================
           MENSAJE BOT
           ===================================================== */

        function agregarMensajeBot(
            texto,
            guardar = true
        ) {

            const row =
                document.createElement(
                    "div"
                );


            row.className =
                "chat-row bot-row";


            const avatar =
                document.createElement(
                    "div"
                );


            avatar.className =
                "chat-avatar-small";


            avatar.textContent =
                "🤖";


            const bubble =
                document.createElement(
                    "div"
                );


            bubble.className =
                "chat-bubble bot-bubble";


            /*
             * Mantener saltos de línea.
             */
            bubble.innerHTML =
                String(texto)
                    .replace(
                        /\n/g,
                        "<br>"
                    );


            row.appendChild(
                avatar
            );

            row.appendChild(
                bubble
            );


            messages.appendChild(
                row
            );


            if (guardar) {

                guardarMensaje(
                    "bot",
                    texto
                );
            }


            scrollChat();
        }


        /* =====================================================
           SCROLL
           ===================================================== */

        function scrollChat() {

            messages.scrollTop =
                messages.scrollHeight;
        }


        /* =====================================================
           ESTADO
           ===================================================== */

        function cambiarEstado(
            texto
        ) {

            if (status) {

                status.textContent =
                    texto;
            }
        }


        /* =====================================================
           ENVIAR MENSAJE
           ===================================================== */

        async function enviarMensaje() {

            const mensaje =
                input.value.trim();


            if (!mensaje) {

                return;
            }


            console.log(
                "💬 Mensaje enviado:",
                mensaje
            );


            /* -----------------------------------------------
               MOSTRAR USUARIO
               ----------------------------------------------- */

            agregarMensajeUsuario(
                mensaje,
                true
            );


            /* -----------------------------------------------
               LIMPIAR INPUT
               ----------------------------------------------- */

            input.value = "";


            /* -----------------------------------------------
               ESTADO
               ----------------------------------------------- */

            cambiarEstado(
                "Procesando consulta..."
            );


            input.disabled =
                true;

            sendButton.disabled =
                true;


            /* -----------------------------------------------
               INDICADOR PROCESANDO
               ----------------------------------------------- */

            const typing =
                document.createElement(
                    "div"
                );


            typing.className =
                "chat-row bot-row";


            typing.innerHTML = `

                <div class="chat-avatar-small">
                    🤖
                </div>

                <div class="chat-bubble bot-bubble">
                    ⏳ Procesando...
                </div>

            `;


            messages.appendChild(
                typing
            );


            scrollChat();


            try {

                console.log(
                    "📡 Enviando POST /chatbox/ask"
                );


                /* =============================================
                   BACKEND FLASK
                   ============================================= */

                const response =
                    await fetch(
                        "/chatbox/ask",
                        {

                            method:
                                "POST",

                            headers: {

                                "Content-Type":
                                    "application/json"

                            },

                            body:
                                JSON.stringify({

                                    message:
                                        mensaje

                                })

                        }
                    );


                console.log(
                    "📡 HTTP Status:",
                    response.status
                );


                const data =
                    await response.json();


                console.log(
                    "🤖 Respuesta backend:",
                    data
                );


                /* =============================================
                   QUITAR PROCESANDO
                   ============================================= */

                typing.remove();


                /* =============================================
                   VALIDAR HTTP
                   ============================================= */

                if (!response.ok) {

                    throw new Error(

                        data.response ||

                        "Error HTTP " +
                        response.status

                    );
                }


                /* =============================================
                   RESPUESTA DEL ASISTENTE
                   ============================================= */

                if (
                    data &&
                    data.response
                ) {

                    agregarMensajeBot(
                        data.response,
                        true
                    );

                }
                else {

                    agregarMensajeBot(
                        "⚠️ El servidor no devolvió una respuesta.",
                        true
                    );
                }


                /* =============================================
                   ESTADO FINAL
                   ============================================= */

                cambiarEstado(
                    "Listo para ayudarte"
                );


            }
            catch (error) {

                console.error(
                    "❌ Error procesando chat:",
                    error
                );


                /* =============================================
                   QUITAR PROCESANDO
                   ============================================= */

                typing.remove();


                /* =============================================
                   MOSTRAR ERROR
                   ============================================= */

                agregarMensajeBot(

                    "❌ Ocurrió un error al procesar " +
                    "tu consulta.\n\n" +

                    error.message,

                    true
                );


                cambiarEstado(
                    "Error al procesar la consulta"
                );

            }


            /* -----------------------------------------------
               RESTAURAR INPUT
               ----------------------------------------------- */

            input.disabled =
                false;

            sendButton.disabled =
                false;


            input.focus();


            scrollChat();
        }


        /* =====================================================
           BOTÓN ENVIAR
           ===================================================== */

        if (sendButton) {

            sendButton.addEventListener(
                "click",
                function (event) {

                    event.preventDefault();

                    event.stopPropagation();


                    enviarMensaje();

                }
            );
        }


        /* =====================================================
           ENTER
           ===================================================== */

        if (input) {

            input.addEventListener(
                "keydown",
                function (event) {

                    if (
                        event.key ===
                        "Enter" &&
                        !event.shiftKey
                    ) {

                        event.preventDefault();


                        enviarMensaje();

                    }

                }
            );
        }


        /* =====================================================
           REDIMENSIONAMIENTO
           ===================================================== */

        let resizing =
            false;

        let resizeDirection =
            null;

        let startX =
            0;

        let startY =
            0;

        let startWidth =
            0;

        let startHeight =
            0;

        let startLeft =
            0;

        let startTop =
            0;


        /* =====================================================
           INICIAR RESIZE
           ===================================================== */

        function iniciarResize(
            event,
            direccion
        ) {

            if (!chatWindow) {

                return;
            }


            /*
             * No redimensionar si está maximizado.
             */
            if (
                chatWindow.classList.contains(
                    "maximized"
                )
            ) {

                return;
            }


            event.preventDefault();

            event.stopPropagation();


            resizing =
                true;


            resizeDirection =
                direccion;


            startX =
                event.clientX;

            startY =
                event.clientY;


            const rect =
                chatWindow.getBoundingClientRect();


            startWidth =
                rect.width;

            startHeight =
                rect.height;

            startLeft =
                rect.left;

            startTop =
                rect.top;


            document.body.style.userSelect =
                "none";
        }


        /* =====================================================
           EJECUTAR RESIZE
           ===================================================== */

        function ejecutarResize(
            event
        ) {

            if (!resizing) {

                return;
            }


            const deltaX =
                event.clientX -
                startX;

            const deltaY =
                event.clientY -
                startY;


            let nuevoAncho =
                startWidth;

            let nuevaAltura =
                startHeight;

            let nuevoLeft =
                startLeft;

            let nuevoTop =
                startTop;


            /* =================================================
               ESQUINA INFERIOR DERECHA
               ================================================= */

            if (
                resizeDirection ===
                "bottom-right"
            ) {

                nuevoAncho =
                    startWidth +
                    deltaX;

                nuevaAltura =
                    startHeight +
                    deltaY;


                nuevoAncho =
                    Math.max(
                        320,
                        Math.min(
                            nuevoAncho,
                            window.innerWidth -
                            startLeft -
                            10
                        )
                    );


                nuevaAltura =
                    Math.max(
                        420,
                        Math.min(
                            nuevaAltura,
                            window.innerHeight -
                            startTop -
                            10
                        )
                    );
            }


            /* =================================================
               ESQUINA SUPERIOR IZQUIERDA
               ================================================= */

            if (
                resizeDirection ===
                "top-left"
            ) {

                nuevoAncho =
                    startWidth -
                    deltaX;

                nuevaAltura =
                    startHeight -
                    deltaY;


                nuevoLeft =
                    startLeft +
                    deltaX;

                nuevoTop =
                    startTop +
                    deltaY;


                const minWidth =
                    320;

                const minHeight =
                    420;


                if (
                    nuevoAncho <
                    minWidth
                ) {

                    nuevoAncho =
                        minWidth;

                    nuevoLeft =
                        startLeft +
                        (
                            startWidth -
                            minWidth
                        );
                }


                if (
                    nuevaAltura <
                    minHeight
                ) {

                    nuevaAltura =
                        minHeight;

                    nuevoTop =
                        startTop +
                        (
                            startHeight -
                            minHeight
                        );
                }


                if (
                    nuevoLeft <
                    10
                ) {

                    nuevoLeft =
                        10;
                }


                if (
                    nuevoTop <
                    10
                ) {

                    nuevoTop =
                        10;
                }
            }


            chatWindow.style.width =
                nuevoAncho +
                "px";


            chatWindow.style.height =
                nuevaAltura +
                "px";


            if (
                resizeDirection ===
                "top-left"
            ) {

                chatWindow.style.left =
                    nuevoLeft +
                    "px";

                chatWindow.style.top =
                    nuevoTop +
                    "px";

                chatWindow.style.right =
                    "auto";

                chatWindow.style.bottom =
                    "auto";
            }

        }


        /* =====================================================
           FINALIZAR RESIZE
           ===================================================== */

        function finalizarResize() {

            if (!resizing) {

                return;
            }


            resizing =
                false;


            resizeDirection =
                null;


            document.body.style.userSelect =
                "";
        }


        /* =====================================================
           EVENTOS DE RESIZE
           ===================================================== */

        if (resizeTopLeft) {

            resizeTopLeft.addEventListener(
                "mousedown",
                function (event) {

                    iniciarResize(
                        event,
                        "top-left"
                    );

                }
            );
        }


        if (resizeBottomRight) {

            resizeBottomRight.addEventListener(
                "mousedown",
                function (event) {

                    iniciarResize(
                        event,
                        "bottom-right"
                    );

                }
            );
        }


        document.addEventListener(
            "mousemove",
            ejecutarResize
        );


        document.addEventListener(
            "mouseup",
            finalizarResize
        );


        /* =====================================================
           CARGAR HISTORIAL
           ===================================================== */

        cargarHistorial();


        /* =====================================================
           LISTO
           ===================================================== */

        console.log(
            "✅ Smart BI Assistant listo"
        );

    }
);