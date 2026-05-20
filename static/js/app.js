// ===============================
// 🚀 CARGA DINÁMICA DE CONTENIDO
// ===============================
let paginaActual = null;

function cargarContenido(url) {

    // 🔥 Evita recargar la misma página
    if (paginaActual === url) {
        console.log("Página ya cargada, evitando duplicado:", url);
        return;
    }

    paginaActual = url;

    $("#contenido").empty().load(url, function (response, status, xhr) {

        if (status === "success") {
            console.log("Contenido cargado correctamente:", url);

            $(".content").removeClass("center-content");

            // 🔥 Ejecutar scripts UNA SOLA VEZ
            ejecutarScriptsDinamicos("#contenido");

            // 🔥 Esperar a que existan elementos clave
            esperarElementoMultiple(["year", "producto"], function () {

                // 🔥 Evitar múltiples inicializaciones
                if (window.__initEjecutado) {
                    console.log("Init ya ejecutado, evitando duplicado");
                    return;
                }

                if (typeof init === "function") {
                    console.log("Inicializando dashboard (init)...");
                    init();
                    window.__initEjecutado = true;

                } else if (typeof initDevoluciones === "function") {
                    console.log("Inicializando devoluciones...");
                    initDevoluciones();
                    window.__initEjecutado = true;

                } else {
                    console.warn("No hay función init disponible");
                }

            });

        } else {
            console.error("Error al cargar contenido:", xhr.status, xhr.statusText);
        }
    });
}


// ===============================
// ⏳ ESPERAR ELEMENTOS
// ===============================
function esperarElementoMultiple(ids, callback) {

    let intentos = 0;

    const intervalo = setInterval(function () {

        const existe = ids.some(id => document.getElementById(id));

        if (existe) {
            clearInterval(intervalo);
            callback();
        }

        // 🔥 evita loop infinito
        intentos++;
        if (intentos > 100) {
            clearInterval(intervalo);
            console.warn("Timeout esperando elementos:", ids);
        }

    }, 50);
}


// ===============================
// ⚙️ EJECUTAR SCRIPTS DINÁMICOS (FIX DUPLICADOS)
// ===============================
function ejecutarScriptsDinamicos(selector) {

    const container = document.querySelector(selector);
    if (!container) return;

    const scripts = container.querySelectorAll("script");

    scripts.forEach(oldScript => {

        const newScript = document.createElement("script");

        if (oldScript.src) {

            // 🔥 evita cargar el mismo script varias veces
            if (document.querySelector(`script[src="${oldScript.src}"]`)) {
                return;
            }

            newScript.src = oldScript.src;
            newScript.async = false;

        } else {
            newScript.textContent = oldScript.innerHTML;
        }

        document.body.appendChild(newScript);
    });
}


// ===============================
// 🔄 ACTUALIZAR DATOS
// ===============================
function actualizarDatos() {

    fetch('/actualizar_datos')
        .then(res => res.json())
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
        .catch(err => console.error('Error al actualizar los datos:', err));
}


// ===============================
// 📊 TABLA
// ===============================
function actualizarTabla(data) {

    let tabla = document.getElementById("tabla-reportes");
    if (!tabla) return;

    let tbody = tabla.querySelector("tbody");
    tbody.innerHTML = "";

    ["reportes_trimestrales", "reportes_mensuales", "reportes_semestrales", "reportes_anuales"]
        .forEach(categoria => {

            if (data[categoria]) {
                data[categoria].forEach(reporte => {

                    tbody.innerHTML += `
                        <tr>
                            <td>${reporte.nombre}</td>
                            <td style="background-color: ${reporte.indicador};">${reporte.indicador}</td>
                            <td>${reporte.nombre_original}</td>
                        </tr>
                    `;
                });
            }
        });
}


// ===============================
// 📂 SUBMENÚS
// ===============================
document.addEventListener('click', function (e) {

    const toggle = e.target.closest('.submenu-toggle');

    if (toggle) {
        e.preventDefault();

        const submenu = toggle.closest('.submenu');

        document.querySelectorAll('.submenu').forEach(sm => {
            if (sm !== submenu) sm.classList.remove('open');
        });

        submenu.classList.toggle('open');
    }
});


// ===============================
// 📌 SIDEBAR
// ===============================
$(document).ready(function () {

    const sidebar = $('.sidebar');
    const toggleButton = $('.menu-toggle');

    $('.sidebar-trigger').on('mouseenter', function () {
        sidebar.removeClass('hidden');
        toggleButton.addClass('hidden');
    });

    toggleButton.on('click', function () {
        sidebar.removeClass('hidden');
        toggleButton.addClass('hidden');
    });

    sidebar.on('mouseleave', function () {
        setTimeout(function () {
            if (!sidebar.is(':hover')) {
                sidebar.addClass('hidden');
                toggleButton.removeClass('hidden');
            }
        }, 300);
    });

});


// ===============================
// 🔔 NOTIFICACIONES
// ===============================
document.addEventListener("DOMContentLoaded", function () {

    const bell = document.getElementById("notificationBell");
    const panel = document.getElementById("notificationPanel");
    const list = document.getElementById("notificationList");
    const count = document.getElementById("notificationCount");

    if (bell && panel) {

        bell.addEventListener("click", function (e) {
            e.stopPropagation();
            panel.classList.toggle("show");
        });

        document.addEventListener("click", function (e) {
            if (!panel.contains(e.target) && !bell.contains(e.target)) {
                panel.classList.remove("show");
            }
        });
    }

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
                        </li>
                    `;
                });

                count.textContent = data.length;
                count.style.display = "block";

                bell.classList.add("blink");

            } else {
                list.innerHTML = "<li>No hay notificaciones nuevas.</li>";
                count.style.display = "none";
                bell.classList.remove("blink");
            }
        })
        .catch(err => console.error("Error cargando notificaciones:", err));
});