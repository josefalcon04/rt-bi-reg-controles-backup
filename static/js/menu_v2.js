const userButton = document.getElementById("userMenuButton");
const userMenu = document.getElementById("userMenu");

// Abrir / cerrar menú
userButton.addEventListener("click", function (e) {

    e.stopPropagation();

    userMenu.classList.toggle("show");

});

// Permite hacer clic dentro del menú sin cerrarlo
userMenu.addEventListener("click", function (e) {

    e.stopPropagation();

});

// Cierra el menú solo cuando se hace clic fuera
document.addEventListener("click", function () {

    userMenu.classList.remove("show");

});
document.addEventListener("DOMContentLoaded", function () {

    console.log("MENU V2 CARGADO");

    // ===========================
    // Sidebar
    // ===========================

    const sidebar = document.getElementById("sidebar");
    const boton = document.getElementById("toggleSidebar");

    let colapsado = false;

    boton.addEventListener("click", function () {

        colapsado = !colapsado;

        sidebar.classList.toggle("collapsed", colapsado);

    });

    sidebar.addEventListener("mouseenter", function () {

        if (colapsado)
            sidebar.classList.remove("collapsed");

    });

    sidebar.addEventListener("mouseleave", function () {

        if (colapsado)
            sidebar.classList.add("collapsed");

    });

    // ===========================
    // Submenús
    // ===========================

    const toggles = document.querySelectorAll(".submenu-toggle");

    console.log("Submenus encontrados:", toggles.length);

    toggles.forEach(function(toggle){

        toggle.addEventListener("click", function(e){

            e.preventDefault();

            console.log("CLICK:", this);

            const submenu = this.nextElementSibling;

            console.log("SUBMENU:", submenu);

            if(submenu){

                submenu.classList.toggle("open");

            }

            this.classList.toggle("active");

        });

    });

});

// ==========================================
// FAVORITOS
// ==========================================

document.querySelectorAll(".favorito").forEach(function(star){

    star.addEventListener("click", function(e){

        e.preventDefault();

        e.stopPropagation();

        const idMenu = this.dataset.menu;

        fetch("/favoritos/toggle",{

            method:"POST",

            headers:{
                "Content-Type":"application/json"
            },

            body:JSON.stringify({

                id_menu:idMenu

            })

        })

        .then(r=>r.json())

        .then(data => {

    if (data.ok) {

        window.location.reload();

    }

});

    });

});
// ==========================================
// BUSCADOR DE MÓDULOS
// ==========================================

const buscador = document.getElementById("buscarMenu");

buscador.addEventListener("keyup", function () {

    const texto = this.value.toLowerCase();

    document.querySelectorAll(".sidebar-menu > li").forEach(menu => {

        const titulo = menu.querySelector("a span");

        if (!titulo) return;

        const nombre = titulo.textContent.toLowerCase();

        let visible = nombre.includes(texto);

        // Buscar también en los submenús
        menu.querySelectorAll(".submenu-content li").forEach(sub => {

            const textoSub = sub.textContent.toLowerCase();

            if (textoSub.includes(texto)) {

                visible = true;

            }

        });

        menu.style.display = visible ? "" : "none";

    });

});