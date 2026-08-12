// ==========================================
// NOTIFICACIONES RT BI ASSISTANT
// ==========================================

document.addEventListener("DOMContentLoaded", function () {

    const notificationButton =
        document.getElementById("notificationButton");

    const notificationPanel =
        document.getElementById("notificationPanel");

    const notificationBadge =
        document.getElementById("notificationBadge");

    const notificationCount =
        document.getElementById("notificationCount");

    const notificationList =
        document.getElementById("notificationList");


    // ==========================================
    // VALIDACIÓN
    // ==========================================

    if (!notificationButton ||
        !notificationPanel ||
        !notificationBadge ||
        !notificationCount ||
        !notificationList) {

        console.warn(
            "⚠️ Elementos de notificaciones no encontrados."
        );

        return;
    }


    // ==========================================
    // ABRIR / CERRAR PANEL
    // ==========================================

    notificationButton.addEventListener("click", function (e) {

        e.stopPropagation();

        notificationPanel.classList.toggle("show");

    });


    // ==========================================
    // EVITAR QUE EL PANEL SE CIERRE AL HACER CLICK
    // ==========================================

    notificationPanel.addEventListener("click", function (e) {

        e.stopPropagation();

    });


    // ==========================================
    // CERRAR AL HACER CLICK FUERA
    // ==========================================

    document.addEventListener("click", function () {

        notificationPanel.classList.remove("show");

    });


    // ==========================================
    // CARGAR NOTIFICACIONES
    // ==========================================

    function cargarNotificaciones() {

        fetch("/notificaciones")

            .then(response => {

                if (!response.ok) {

                    throw new Error(
                        "Error HTTP: " + response.status
                    );

                }

                return response.json();

            })

            .then(data => {

                console.log(
                    "📢 Notificaciones recibidas:",
                    data
                );


                // ==================================
                // ERROR DEVUELTO POR BACKEND
                // ==================================

                if (!Array.isArray(data)) {

                    console.error(
                        "Error en respuesta:",
                        data
                    );

                    return;
                }


                const cantidad = data.length;


                // ==================================
                // ACTUALIZAR CONTADOR
                // ==================================

                notificationCount.textContent =
                    cantidad;


                if (cantidad > 0) {

                    notificationBadge.textContent =
                        cantidad;

                    notificationBadge.style.display =
                        "flex";

                } else {

                    notificationBadge.style.display =
                        "none";

                }


                // ==================================
                // LIMPIAR LISTA
                // ==================================

                notificationList.innerHTML = "";


                // ==================================
                // SIN NOTIFICACIONES
                // ==================================

                if (cantidad === 0) {

                    const vacio =
                        document.createElement("div");

                    vacio.className =
                        "notification-empty";

                    vacio.innerHTML = `
                        <i class="fa-regular fa-circle-check"></i>
                        <span>
                            No hay notificaciones pendientes
                        </span>
                    `;

                    notificationList.appendChild(
                        vacio
                    );

                    return;
                }


                // ==================================
                // CREAR NOTIFICACIONES
                // ==================================

                data.forEach(function (notificacion) {

                    const item =
                        document.createElement("div");

                    item.className =
                        "notification-item";


                    item.innerHTML = `

                        <div class="notification-item-icon">
                            <i class="fa-solid fa-triangle-exclamation"></i>
                        </div>

                        <div class="notification-item-content">

                            <div class="notification-item-title">
                                ${escapeHtml(
                                    notificacion.titulo
                                )}
                            </div>

                            <div class="notification-item-message">
                                ${escapeHtml(
                                    notificacion.mensaje
                                )}
                            </div>

                        </div>

                    `;


                    notificationList.appendChild(
                        item
                    );

                });

            })

            .catch(error => {

                console.error(
                    "❌ Error cargando notificaciones:",
                    error
                );

            });

    }


    // ==========================================
    // PROTECCIÓN CONTRA HTML
    // ==========================================

    function escapeHtml(text) {

        if (text === null ||
            text === undefined) {

            return "";

        }

        return String(text)

            .replace(/&/g, "&amp;")

            .replace(/</g, "&lt;")

            .replace(/>/g, "&gt;")

            .replace(/"/g, "&quot;")

            .replace(/'/g, "&#039;");

    }


    // ==========================================
    // CARGA INICIAL
    // ==========================================

    cargarNotificaciones();


    // ==========================================
    // ACTUALIZACIÓN AUTOMÁTICA
    // ==========================================

    setInterval(
        cargarNotificaciones,
        60000
    );

});