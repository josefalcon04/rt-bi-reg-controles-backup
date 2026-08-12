document.addEventListener("DOMContentLoaded", function () {

    console.log("======================================");
    console.log("MONITOREO NORMA JS INICIADO");
    console.log("======================================");


    // =====================================================
    // ELEMENTOS
    // =====================================================

    const buscador = document.getElementById("buscadorReportes");

    const filtroEstado =
        document.getElementById("filtroEstado") ||
        document.querySelector(".monitoreo-status-filter select");

    const reportItems =
        Array.from(document.querySelectorAll(".report-item"));

    const tabs =
        document.querySelectorAll(".monitoreo-tab");

    const tabContents =
        document.querySelectorAll(".monitoreo-tab-content");

    const contador =
        document.querySelector(".monitoreo-count");


    console.log("Buscador:", buscador);
    console.log("Filtro:", filtroEstado);
    console.log("Reportes encontrados:", reportItems.length);


    // =====================================================
    // NORMALIZAR ESTADO
    // =====================================================

    function normalizarTexto(valor) {

        if (!valor) {
            return "";
        }

        return String(valor)
            .trim()
            .toLowerCase()
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "");
    }


    // =====================================================
// OBTENER ESTADO REAL DEL REPORTE
// =====================================================

function obtenerEstado(item) {

    let estado =
        item.dataset.estado ||
        "";

    estado = normalizarTexto(estado);


    // =============================================
    // VERDE
    // =============================================

    if (
        estado === "green" ||
        estado === "verde" ||
        estado.includes("exito") ||
        estado.includes("exitoso") ||
        estado === "success" ||
        estado === "ok"
    ) {

        return "green";
    }


    // =============================================
    // AMARILLO
    // =============================================

    if (
        estado === "yellow" ||
        estado === "amarillo" ||
        estado.includes("pendiente") ||
        estado === "warning" ||
        estado === "warn"
    ) {

        return "yellow";
    }


    // =============================================
    // ROJO
    // =============================================

    if (
        estado === "red" ||
        estado === "rojo" ||
        estado.includes("error") ||
        estado.includes("fallido") ||
        estado.includes("fallo") ||
        estado === "danger"
    ) {

        return "red";
    }


    // =============================================
    // GRIS
    // =============================================

    return "grey";
}

    // =====================================================
    // APLICAR COLOR A LOS INDICADORES
    // =====================================================

    function aplicarEstados() {

        reportItems.forEach(function (item) {

            const indicador =
                item.querySelector(".status-indicator");

            if (!indicador) {
                return;
            }


            const estado =
                obtenerEstado(item);


            // Guardamos el estado normalizado
            item.dataset.estadoNormalizado = estado;


            // Limpiar clases anteriores

            indicador.classList.remove(
                "success",
                "warning",
                "error",
                "unknown"
            );


            // Aplicar clase

            indicador.classList.add(estado);


            console.log(
                "Reporte:",
                item.innerText.trim(),
                "| Estado original:",
                item.dataset.estado,
                "| Estado normalizado:",
                estado
            );

        });

    }


    // Ejecutar inmediatamente
    aplicarEstados();


    // =====================================================
    // ACTUALIZAR CONTADOR
    // =====================================================

    function actualizarContador(cantidad) {

        if (!contador) {
            return;
        }

        contador.textContent =
            cantidad + (
                cantidad === 1
                    ? " reporte"
                    : " reportes"
            );
    }


    // =====================================================
// FILTRAR REPORTES
// =====================================================

function filtrarReportes() {

    const texto =
        buscador
            ? normalizarTexto(buscador.value)
            : "";


    const estadoSeleccionado =
        filtroEstado
            ? normalizarTexto(filtroEstado.value)
            : "todos";


    let visibles = 0;


    reportItems.forEach(function (item) {

        const elementoNombre =
            item.querySelector(".report-name") ||
            item.querySelector("a");


        const nombre =
            elementoNombre
                ? normalizarTexto(
                    elementoNombre.textContent
                )
                : normalizarTexto(
                    item.textContent
                );


        const estado =
            item.dataset.estadoNormalizado ||
            obtenerEstado(item);


        // =============================================
        // FILTRO TEXTO
        // =============================================

        const coincideTexto =
            !texto ||
            nombre.includes(texto);


        // =============================================
        // FILTRO ESTADO
        // =============================================

        let coincideEstado = true;


        if (
            estadoSeleccionado &&
            estadoSeleccionado !== "todos" &&
            estadoSeleccionado !== "all"
        ) {

            coincideEstado =
                estado === estadoSeleccionado;

        }


        // =============================================
        // MOSTRAR / OCULTAR
        // =============================================

        if (
            coincideTexto &&
            coincideEstado
        ) {

            item.style.display = "";

            visibles++;

        }
        else {

            item.style.display = "none";

        }

    });


    actualizarContador(visibles);


    console.log(
        "======================================"
    );

    console.log(
        "ESTADO SELECCIONADO:",
        estadoSeleccionado
    );

    console.log(
        "REPORTES VISIBLES:",
        visibles
    );

    console.log(
        "======================================"
    );
}


    // =====================================================
    // EVENTO BUSCADOR
    // =====================================================

    if (buscador) {

        buscador.addEventListener(
            "input",
            filtrarReportes
        );

    }


    // =====================================================
    // EVENTO COMBO ESTADO
    // =====================================================

    if (filtroEstado) {

        filtroEstado.addEventListener(
            "change",
            function () {

                console.log(
                    "Cambio de estado:",
                    filtroEstado.value
                );

                filtrarReportes();

            }
        );

    }
    else {

        console.warn(
            "No se encontró el combo de estados."
        );

    }


    // =====================================================
    // TABS
    // =====================================================

    tabs.forEach(function (tab) {

        tab.addEventListener(
            "click",
            function () {

                const tabSeleccionado =
                    tab.dataset.tab;


                // Quitar active de tabs

                tabs.forEach(function (t) {

                    t.classList.remove(
                        "active"
                    );

                });


                // Activar tab

                tab.classList.add(
                    "active"
                );


                // Ocultar contenidos

                tabContents.forEach(
                    function (contenido) {

                        contenido.classList.remove(
                            "active"
                        );

                    }
                );


                // Mostrar contenido correspondiente

                const contenido =
                    document.getElementById(
                        tabSeleccionado
                    );


                if (contenido) {

                    contenido.classList.add(
                        "active"
                    );

                }


                // Volver a aplicar filtros

                filtrarReportes();

            }
        );

    });


    // =====================================================
    // EJECUCIÓN INICIAL
    // =====================================================

    filtrarReportes();


    // =====================================================
    // DEBUG
    // =====================================================

    console.log(
        "Total reportes:",
        reportItems.length
    );

    console.log(
        "Filtro estado:",
        filtroEstado
            ? filtroEstado.value
            : "NO ENCONTRADO"
    );

});