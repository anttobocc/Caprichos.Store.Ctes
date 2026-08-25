/* Editor visual de posición/tamaño de una imagen de portada (categoría o
 * la tarjeta "Pedidos"): arrastrar para mover, botones −/+/↑/↓, campos
 * numéricos y deslizador de tamaño. Los campos se ubican por sufijo de
 * nombre ("..._pos_x" / "..._pos_y" / "..._tamano") para que el mismo
 * script sirva tanto a los campos imagen_pos_x/imagen_pos_y/imagen_tamano
 * de Categoria como a pedidos_imagen_pos_x/pedidos_imagen_pos_y/
 * pedidos_imagen_tamano de ConfiguracionNegocio. Cada editor trabaja sobre
 * el <form> de UNA sola instancia, y todos los controles quedan
 * sincronizados entre sí: mover cualquiera de ellos actualiza de inmediato
 * la vista previa y el resto de los controles. */
(function () {
    "use strict";

    function clamp(valor, minimo, maximo) {
        return Math.min(maximo, Math.max(minimo, valor));
    }

    function iniciar(editor) {
        var form = editor.closest("form");
        if (!form) {
            return;
        }
        var img = editor.querySelector("[data-imagen-preview]");
        var vacio = editor.querySelector("[data-imagen-vacio]");
        var slider = editor.querySelector("[data-tamano-slider]");
        var campoArchivo = form.querySelector('input[type="file"]');
        var nombreArchivo = form.querySelector("[data-nombre-archivo]");
        var campoX = form.querySelector('input[name$="imagen_pos_x"]');
        var campoY = form.querySelector('input[name$="imagen_pos_y"]');
        var campoTamano = form.querySelector('input[name$="imagen_tamano"]');
        if (!img || !campoX || !campoY || !campoTamano) {
            return;
        }

        var LIMITE_POS = 1000;
        var TAMANO_MIN = 50;
        var TAMANO_MAX = 5000;
        var PASO_BOTON = 1;

        var x = parseInt(campoX.value, 10) || 0;
        var y = parseInt(campoY.value, 10) || 0;
        var tamano = parseInt(campoTamano.value, 10) || 260;

        function aplicarPosicion() {
            x = clamp(x, -LIMITE_POS, LIMITE_POS);
            y = clamp(y, -LIMITE_POS, LIMITE_POS);
            img.style.transform = "translate(" + x + "px, " + y + "px)";
            campoX.value = String(x);
            campoY.value = String(y);
        }

        function aplicarTamano() {
            tamano = clamp(tamano, TAMANO_MIN, TAMANO_MAX);
            img.style.height = tamano + "px";
            campoTamano.value = String(tamano);
            if (slider) {
                slider.value = String(tamano);
            }
        }

        img.addEventListener("pointerdown", function (evento) {
            if (img.hidden) {
                return;
            }
            evento.preventDefault();
            var inicioX = evento.clientX;
            var inicioY = evento.clientY;
            var origenX = x;
            var origenY = y;

            function mover(e) {
                x = origenX + (e.clientX - inicioX);
                y = origenY + (e.clientY - inicioY);
                aplicarPosicion();
            }

            function soltar() {
                document.removeEventListener("pointermove", mover);
                document.removeEventListener("pointerup", soltar);
            }

            document.addEventListener("pointermove", mover);
            document.addEventListener("pointerup", soltar);
        });

        campoX.addEventListener("input", function () {
            x = parseInt(campoX.value, 10) || 0;
            aplicarPosicion();
        });

        campoY.addEventListener("input", function () {
            y = parseInt(campoY.value, 10) || 0;
            aplicarPosicion();
        });

        editor.querySelectorAll("[data-ajustar-x]").forEach(function (boton) {
            boton.addEventListener("click", function () {
                x += (parseInt(boton.getAttribute("data-ajustar-x"), 10) || 0) * PASO_BOTON;
                aplicarPosicion();
            });
        });

        editor.querySelectorAll("[data-ajustar-y]").forEach(function (boton) {
            boton.addEventListener("click", function () {
                y += (parseInt(boton.getAttribute("data-ajustar-y"), 10) || 0) * PASO_BOTON;
                aplicarPosicion();
            });
        });

        if (slider) {
            slider.addEventListener("input", function () {
                tamano = parseInt(slider.value, 10) || 260;
                aplicarTamano();
            });
        }

        campoTamano.addEventListener("input", function () {
            tamano = parseInt(campoTamano.value, 10) || 260;
            aplicarTamano();
        });

        if (campoArchivo) {
            campoArchivo.addEventListener("change", function () {
                var archivo = campoArchivo.files && campoArchivo.files[0];
                if (!archivo || !window.FileReader) {
                    return;
                }
                var lector = new FileReader();
                lector.onload = function (evento) {
                    img.src = evento.target.result;
                    img.hidden = false;
                    if (vacio) {
                        vacio.hidden = true;
                    }
                    if (nombreArchivo) {
                        nombreArchivo.textContent = archivo.name;
                        nombreArchivo.classList.remove("admin-imagen-archivo__nombre--vacio");
                    }
                    aplicarPosicion();
                    aplicarTamano();
                };
                lector.readAsDataURL(archivo);
            });
        }
    }

    document.querySelectorAll("[data-imagen-editor]").forEach(iniciar);
})();
