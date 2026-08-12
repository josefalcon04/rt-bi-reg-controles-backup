// ==========================================
// CALENDARIO DE REPORTES
// ==========================================

// ------------------------------------------
// Pintar lista de reportes
// ------------------------------------------

function pintarReportes(reportes) {

    const listaReportes =
        document.getElementById("lista-reportes");

    if (!listaReportes) {
        return;
    }

    listaReportes.innerHTML = "";

    // No existen resultados
    if (reportes.length === 0) {

        listaReportes.innerHTML =
            "<p style='color:gray;'>No se encontraron reportes</p>";

        return;
    }

    // Pintar cada reporte
    reportes.forEach(function (reporte) {

        const div =
            document.createElement("div");

        div.classList.add("reporte");

        // Color
        const color =
            document.createElement("span");

        color.classList.add("reporte-color");

        color.style.backgroundColor =
            reporte.color;

        // Nombre
        const nombre =
            document.createElement("span");

        nombre.classList.add("reporte-nombre");

        nombre.textContent =
            reporte.nombre;

        // Día
        const fecha =
            document.createElement("span");

        fecha.classList.add("reporte-dia");

        fecha.textContent =
            ` (${reporte.dia})`;

        // Agregar elementos
        div.appendChild(color);

        div.appendChild(nombre);

        div.appendChild(fecha);

        listaReportes.appendChild(div);

    });

}


// ------------------------------------------
// Mostrar reportes de un día
// ------------------------------------------

function mostrarReportes(dia, reportes) {

    const contenedor =
        document.getElementById("barra-reportes");

    if (!contenedor) {
        return;
    }

    if (reportes.length > 0) {

        contenedor.style.display = "block";

        const reportesDia =
            reportes.map(function (reporte) {

                return {

                    dia: dia,

                    nombre: reporte.nombre,

                    color: reporte.color

                };

            });

        pintarReportes(reportesDia);

    } else {

        contenedor.style.display = "none";

    }

}


// ------------------------------------------
// Filtrar reportes
// ------------------------------------------

function filtrarReportes() {

    const input =
        document.getElementById(
            "busqueda-reporte"
        );

    const contenedor =
        document.getElementById(
            "barra-reportes"
        );

    if (!input || !contenedor) {
        return;
    }

    const texto =
        input.value
            .toLowerCase()
            .trim();

    contenedor.style.display = "block";

    // Si está vacío
    if (texto === "") {

        document.getElementById(
            "lista-reportes"
        ).innerHTML = "";

        return;
    }

    // Buscar reportes
    const filtrados =
        todosReportes.filter(function (reporte) {

            return String(reporte.nombre)
                .toLowerCase()
                .includes(texto);

        });

    // --------------------------------------
    // Eliminar duplicados por nombre
    // --------------------------------------

    const unicosMap =
        new Map();

    filtrados.forEach(function (reporte) {

        const clave =
            String(reporte.nombre)
                .toLowerCase()
                .trim();

        if (!unicosMap.has(clave)) {

            unicosMap.set(
                clave,
                reporte
            );

        }

    });

    const unicos =
        Array.from(
            unicosMap.values()
        );

    pintarReportes(unicos);

}


// ------------------------------------------
// Inicialización
// ------------------------------------------

document.addEventListener(
    "DOMContentLoaded",
    function () {

        console.log(
            "CALENDARIO JS CARGADO"
        );

        const buscador =
            document.getElementById(
                "busqueda-reporte"
            );

        if (buscador) {

            buscador.addEventListener(
                "keyup",
                filtrarReportes
            );

        }

    }
);