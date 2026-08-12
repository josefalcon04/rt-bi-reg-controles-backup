document.addEventListener("DOMContentLoaded", function () {

    const boton = document.getElementById("userMenuButton");
    const menu = document.getElementById("userMenu");

    if (!boton || !menu) return;

    boton.addEventListener("click", function (e) {

        e.stopPropagation();

        menu.classList.toggle("show");

    });

    document.addEventListener("click", function () {

        menu.classList.remove("show");

    });

});