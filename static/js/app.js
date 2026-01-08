// Carga dinámica del contenido
function cargarContenido(url) {
    $("#contenido").load(url, function (response, status, xhr) {
        if (status === "success") {
            console.log("Contenido cargado correctamente:", url);
            $(".content").addClass("center-content");

            // Ejecutar scripts embebidos si hay
            ejecutarScriptsDinamicos("#contenido");
        } else {
            console.error("Error al cargar contenido:", xhr.status, xhr.statusText);
        }
    });
}

// Ejecuta scripts dinámicos que vienen dentro del HTML cargado
function ejecutarScriptsDinamicos(selector) {
    $(selector).find("script").each(function () {
        var scriptText = $(this).text();
        var scriptTag = document.createElement("script");
        scriptTag.textContent = scriptText;
        document.body.appendChild(scriptTag);
    });
}

// Actualizar datos desde endpoint JSON
function actualizarDatos() {
    fetch('/actualizar_datos')
        .then(response => response.json())
        .then(data => {
            const contenedores = {
                'trimestrales': document.querySelector('.grid-container .panel:nth-child(1) .report-container'),
                'mensuales': document.querySelector('.grid-container .panel:nth-child(2) .report-container'),
                'semestrales': document.querySelector('.grid-container .panel:nth-child(3) .report-container'),
                'anuales': document.querySelector('.grid-container .panel:nth-child(4) .report-container')
            };

            Object.keys(data).forEach(tipo => {
                const container = contenedores[tipo];
                if (container) {
                    container.innerHTML = '';
                    data[tipo].forEach(reporte => {
                        container.innerHTML += `
                            <div class="status">
                                <span class="status-indicator ${reporte.indicador}"></span>                                    
                                <a href="${reporte.url}" target="_blank">${reporte.nombre}</a>
                            </div>
                        `;
                    });
                }
            });
        })
        .catch(error => console.error('Error al actualizar los datos:', error));
}

// Actualiza tabla HTML con nuevos datos
function actualizarTabla(data) {
    let tabla = document.getElementById("tabla-reportes");
    if (!tabla) {
        console.error("No se encontró la tabla con id 'tabla-reportes'");
        return;
    }

    let tbody = tabla.querySelector("tbody");
    tbody.innerHTML = "";

    ["reportes_trimestrales", "reportes_mensuales", "reportes_semestrales", "reportes_anuales"].forEach(categoria => {
        if (data[categoria]) {
            data[categoria].forEach(reporte => {
                let row = `<tr>
                    <td>${reporte.nombre}</td>
                    <td style="background-color: ${reporte.indicador};">${reporte.indicador}</td>
                    <td>${reporte.nombre_original}</td>
                </tr>`;
                tbody.innerHTML += row;
            });
        }
    });
}

// Manejo de submenús
document.addEventListener('click', function (e) {
    const toggle = e.target.closest('.submenu-toggle');
    if (toggle) {
        e.preventDefault();
        const submenu = toggle.closest('.submenu');

        // Cierra todos los submenús excepto el actual
        document.querySelectorAll('.submenu').forEach(function (sm) {
            if (sm !== submenu) sm.classList.remove('open');
        });

        submenu.classList.toggle('open');
    }
});

// Control del sidebar
$(document).ready(function () {
    const sidebar = $('.sidebar');
    const toggleButton = $('.menu-toggle');

    // Mostrar sidebar al pasar el mouse por el borde
    $('.sidebar-trigger').on('mouseenter', function () {
        sidebar.removeClass('hidden');
        toggleButton.addClass('hidden');
    });

    // Mostrar sidebar con el botón ☰
    toggleButton.on('click', function () {
        sidebar.removeClass('hidden');
        toggleButton.addClass('hidden');
    });

    // Ocultar sidebar al salir con el mouse (después de un pequeño retardo para evitar parpadeo)
    sidebar.on('mouseleave', function () {
        setTimeout(() => {
            if (!sidebar.is(':hover')) {
                sidebar.addClass('hidden');
                toggleButton.removeClass('hidden');
            }
        }, 300);
    });

    // Prevenir cierre al hacer clic dentro del sidebar
    sidebar.on('click', function (event) {
        event.stopPropagation();
    });

    // Cierre si haces clic fuera del sidebar y del botón
    $(document).on('click', function (event) {
        const isClickInsideSidebar = $(event.target).closest('.sidebar').length;
        const isClickOnToggle = $(event.target).closest('.menu-toggle').length;

        if (!isClickInsideSidebar && !isClickOnToggle && !sidebar.hasClass('hidden')) {
            sidebar.addClass('hidden');
            toggleButton.removeClass('hidden');
        }
    });
});
// ===============================
// 🔔 Notificaciones
// ===============================
document.addEventListener("DOMContentLoaded", function () {
    const bell = document.getElementById("notificationBell");
    const panel = document.getElementById("notificationPanel");
    const list = document.getElementById("notificationList");
    const count = document.getElementById("notificationCount");

    if (bell && panel) {
        // Mostrar/ocultar el panel
        bell.addEventListener("click", function (e) {
            e.stopPropagation();
            panel.classList.toggle("show");
        });

        // Cerrar si se hace clic fuera del panel
        document.addEventListener("click", function (e) {
            if (!panel.contains(e.target) && !bell.contains(e.target)) {
                panel.classList.remove("show");
            }
        });
    }

    // 🚀 Cargar notificaciones dinámicamente desde Flask
    fetch('/notificaciones')
        .then(res => res.json())
        .then(data => {
            if (!list || !count) return;

            if (data && data.length > 0) {
                list.innerHTML = "";
                data.forEach(n => {
                    list.innerHTML += `
                        <li>
                            <strong>${n.titulo}</strong><br>
                            <span>${n.mensaje}</span><br>
                            <small>Periodo: ${n.periodo} | Frecuencia: ${n.frecuencia}</small>
                        </li>`;
                });

                count.textContent = data.length;
                count.style.display = "block";

                // 🔥 Hacer que la campanita parpadee si hay notificaciones
                bell.classList.add("blink");
            } else {
                list.innerHTML = "<li>No hay notificaciones nuevas.</li>";
                count.style.display = "none";

                // Detener el parpadeo si no hay alertas
                bell.classList.remove("blink");
            }
        })
        .catch(err => {
            console.error("Error cargando notificaciones:", err);
            if (list) list.innerHTML = "<li>Error cargando notificaciones.</li>";
        });
});
