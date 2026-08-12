// ================================
// RT BI Assistant
// Login Animation
// ================================

const mensajes = [

    "Analizando información...",

    "Consultando Data Warehouse...",

    "Detectando tendencias...",

    "Preparando Inteligencia Artificial...",

    "Analizando procesos regulatorios...",

    "Cargando asistentes inteligentes...",

    "Transformando datos en conocimiento..."

];

let indice = 0;

function cambiarTexto(){

    const txt = document.getElementById("statusText");

    if(!txt) return;

    txt.style.opacity = 0;

    setTimeout(()=>{

        indice++;

        txt.innerHTML = mensajes[indice % mensajes.length];

        txt.style.opacity = 1;

    },300);

}

setInterval(cambiarTexto,3000);


//===============================
// Mostrar contraseña
//===============================

function togglePassword(){

    let txt = document.getElementById("password");

    txt.type = txt.type==="password"
        ? "text"
        : "password";

}


//===============================
// Loader botón Login
//===============================

const formulario = document.querySelector("form");

if(formulario){

formulario.addEventListener("submit",function(){

    const boton=document.querySelector(".btn-login");

    boton.disabled=true;

    boton.innerHTML=`
    <span class="spinner-border spinner-border-sm"></span>
    Validando credenciales...
    `;

});

}