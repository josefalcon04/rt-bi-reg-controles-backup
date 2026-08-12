document.addEventListener("DOMContentLoaded", () => {

    const form = document.getElementById("formPassword");

    if (!form) return;

    const actual = document.getElementById("password_actual");
    const nueva = document.getElementById("password_nueva");
    const confirmar = document.getElementById("password_confirmar");

    const strengthBar = document.getElementById("strengthBar");
    const strengthText = document.getElementById("strengthText");

    const mensaje = document.getElementById("mensajePassword");
    const matchMessage = document.getElementById("matchMessage");

    const btnGuardar = document.getElementById("btnGuardarPassword");

    //--------------------------------------------------
    // Mostrar / Ocultar contraseña
    //--------------------------------------------------

    document.querySelectorAll(".toggle-password").forEach(btn => {

        btn.addEventListener("click", () => {

            const input = document.getElementById(btn.dataset.target);

            if (input.type === "password") {

                input.type = "text";

                btn.innerHTML =
                    '<i class="fa-solid fa-eye-slash"></i>';

                btn.classList.add("active-eye");

            } else {

                input.type = "password";

                btn.innerHTML =
                    '<i class="fa-solid fa-eye"></i>';

                btn.classList.remove("active-eye");

            }

        });

    });

    //--------------------------------------------------
    // Reglas
    //--------------------------------------------------

    function regla(id, cumple) {

        const item = document.getElementById(id);

        if (cumple) {

            item.className = "rule-ok";

            item.innerHTML =
                '<i class="fa-solid fa-circle-check"></i> ' +
                item.textContent.replace(/^.*? /, "");

        } else {

            item.className = "rule-error";

            item.innerHTML =
                '<i class="fa-solid fa-circle-xmark"></i> ' +
                item.textContent.replace(/^.*? /, "");

        }

    }

    //--------------------------------------------------
    // Validación
    //--------------------------------------------------

    function validarPassword() {

        const pwd = nueva.value;
        
        if (pwd.length === 0) {

            strengthBar.style.width = "0%";

            strengthBar.className = "progress-bar";

            strengthText.innerHTML = "Escriba una contraseña...";

            matchMessage.innerHTML = "";

            btnGuardar.disabled = true;

            return;

        }
        

        const longitud = pwd.length >= 12;
        const mayuscula = /[A-Z]/.test(pwd);
        const minuscula = /[a-z]/.test(pwd);
        const numero = /\d/.test(pwd);
        const especial = /[^A-Za-z0-9]/.test(pwd);

        regla("rule-length", longitud);
        regla("rule-upper", mayuscula);
        regla("rule-lower", minuscula);
        regla("rule-number", numero);
        regla("rule-special", especial);

        let puntos = 0;

        if (longitud) puntos++;
        if (mayuscula) puntos++;
        if (minuscula) puntos++;
        if (numero) puntos++;
        if (especial) puntos++;

        //------------------------------------------------

        switch (puntos) {

            case 0:

            case 1:

                strengthBar.style.width = "20%";

                strengthBar.className =
                    "progress-bar bg-danger";

                strengthText.innerHTML =
                    "🔴 Muy débil";

                break;

            case 2:

                strengthBar.style.width = "40%";

                strengthBar.className =
                    "progress-bar bg-warning";

                strengthText.innerHTML =
                    "🟠 Débil";

                break;

            case 3:

                strengthBar.style.width = "60%";

                strengthBar.className =
                    "progress-bar bg-info";

                strengthText.innerHTML =
                    "🔵 Regular";

                break;

            case 4:

                strengthBar.style.width = "80%";

                strengthBar.className =
                    "progress-bar bg-primary";

                strengthText.innerHTML =
                    "🟢 Buena";

                break;

            case 5:

                strengthBar.style.width = "100%";

                strengthBar.className =
                    "progress-bar bg-success";

                strengthText.innerHTML =
                    "🟢 Muy fuerte";

                break;

        }

        //------------------------------------------------

        if (
            confirmar.value.length > 0
        ) {

            if (pwd === confirmar.value) {

                matchMessage.className =
                    "match-ok";

                matchMessage.innerHTML =
                    '<i class="fa-solid fa-circle-check"></i> Las contraseñas coinciden';

            } else {

                matchMessage.className =
                    "match-error";

                matchMessage.innerHTML =
                    '<i class="fa-solid fa-circle-xmark"></i> Las contraseñas no coinciden';

            }

        } else {

            matchMessage.innerHTML = "";

        }

        //------------------------------------------------

        btnGuardar.disabled = !(
            longitud &&
            mayuscula &&
            minuscula &&
            numero &&
            especial &&
            pwd === confirmar.value &&
            actual.value.length > 0
        );

    }

    actual.addEventListener("keyup", () => {

            if (confirmar.value.length > 0 || nueva.value.length > 0) {

                validarPassword();

            }

        });

    nueva.addEventListener("keyup", function(){

        console.log("ESCRIBIENDO NUEVA");

        validarPassword();

    });

    confirmar.addEventListener("keyup", validarPassword);

    //--------------------------------------------------
    // Guardar
    //--------------------------------------------------

    form.addEventListener("submit", async function (e) {

        e.preventDefault();

        btnGuardar.disabled = true;

        const datos = new FormData(form);

        try {

            const respuesta = await fetch(
                "/cambiar-password",
                {
                    method: "POST",
                    body: datos
                }
            );

            const json = await respuesta.json();

            if (json.ok) {

                mensaje.innerHTML =
                    '<div class="alert alert-success">' +
                    json.mensaje +
                    '</div>';

                form.reset();

                strengthBar.style.width = "0%";

                strengthText.innerHTML =
                    "Escriba una contraseña...";

                matchMessage.innerHTML = "";

                setTimeout(() => {

                    bootstrap.Modal
                        .getInstance(
                            document.getElementById("modalPassword")
                        )
                        .hide();

                }, 1500);

            } else {

                mensaje.innerHTML =
                    '<div class="alert alert-danger">' +
                    json.mensaje +
                    '</div>';

            }

        } catch (err) {

            mensaje.innerHTML =
                '<div class="alert alert-danger">Error al conectar con el servidor.</div>';

        }

        validarPassword();

    });

});