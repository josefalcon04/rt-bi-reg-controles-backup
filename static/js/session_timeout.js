// ==========================================
// SESSION TIMEOUT RT BI ASSISTANT
// ==========================================

// Para pruebas: 30 segundos
// Producción: 20 * 60 * 1000

//const TIEMPO_INACTIVIDAD = 10 * 1000;
const TIEMPO_INACTIVIDAD = 20 * 60 * 1000;

// Segundos del aviso
const SEGUNDOS_AVISO = 60;

let temporizador = null;
let contador = null;

//--------------------------------------------
// Reinicia contador de inactividad
//--------------------------------------------

function reiniciarTemporizador() {

    clearTimeout(temporizador);

    temporizador = setTimeout(
        mostrarAvisoSesion,
        TIEMPO_INACTIVIDAD
    );

}

//--------------------------------------------
// Muestra el modal
//--------------------------------------------

function mostrarAvisoSesion() {

    const modal = new bootstrap.Modal(
        document.getElementById("modalSessionExpired")
    );

    modal.show();

    let segundos = SEGUNDOS_AVISO;

    document.getElementById("countdown").textContent = segundos;

    clearInterval(contador);

    contador = setInterval(function () {

        segundos--;

        document.getElementById("countdown").textContent = segundos;

        if (segundos <= 0) {            

            clearInterval(contador);
            
            window.location.replace("/logout");

        }

    }, 1000);

}

//--------------------------------------------
// Botón continuar trabajando
//--------------------------------------------

document
    .getElementById("btnContinuarSesion")
    .addEventListener("click", function () {

        clearInterval(contador);

        bootstrap.Modal
            .getInstance(
                document.getElementById("modalSessionExpired")
            )
            .hide();

        reiniciarTemporizador();

    });

//--------------------------------------------
// Eventos de actividad
//--------------------------------------------

[
    "mousemove",
    "mousedown",
    "keydown",
    "scroll",
    "touchstart",
    "click"
].forEach(evento => {

    document.addEventListener(
        evento,
        reiniciarTemporizador
    );

});

//--------------------------------------------
// Inicio
//--------------------------------------------

reiniciarTemporizador();