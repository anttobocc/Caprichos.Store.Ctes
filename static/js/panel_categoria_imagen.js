/* Editor visual de posición/tamaño de la imagen de portada de una
 * categoría: arrastrar para mover, deslizador para el tamaño. Actualiza
 * los campos ocultos imagen_pos_x / imagen_pos_y / imagen_tamano del mismo
 * formulario (sin mostrarle nunca coordenadas al administrador). */
(function () {
    "use strict";

    function iniciar(editor) {
        var form = editor.closest("form");
        if (!form) {
            return;
        }
        var img = editor.querySelector("[data-imagen-preview]");
        var vacio = editor.querySelector("[data-imagen-vacio]");
        var slider = editor.querySelector("[data-tamano-slider]");
        var campoArchivo = form.querySelector('input[name="imagen_categoria"]');
        var campoX = form.querySelector('input[name="imagen_pos_x"]');
        var campoY = form.querySelector('input[name="imagen_pos_y"]');
        var campoTamano = form.querySelector('input[name="imagen_tamano"]');
        if (!img || !campoX || !campoY || !campoTamano) {
            return;
        }

        var x = parseInt(campoX.value, 10) || 0;
        var y = parseInt(campoY.value, 10) || 0;

        function aplicarPosicion() {
            img.style.transform = "translate(" + x + "px, " + y + "px)";
            campoX.value = String(x);
            campoY.value = String(y);
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

        if (slider) {
            slider.addEventListener("input", function () {
                campoTamano.value = slider.value;
                img.style.height = slider.value + "px";
            });
        }

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
                    aplicarPosicion();
                };
                lector.readAsDataURL(archivo);
            });
        }
    }

    document.querySelectorAll("[data-imagen-editor]").forEach(iniciar);
})();
