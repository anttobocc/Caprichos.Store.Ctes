/* Panel lateral del carrito (drawer desde la derecha), checkout inline
 * (sin página aparte) y el control de cantidad "− N +" reutilizable en
 * cualquier página (detalle de producto, carrito, drawer).
 *
 * El drawer ya viene renderizado en el HTML de cada página (ver
 * base_catalogo.html + pedidos/_carrito_drawer.html vía el context
 * processor carrito_resumen), así que abrirlo es solo mostrar/animar el
 * panel que ya existe. Al agregar/quitar/actualizar un producto, o al
 * finalizar el pedido, el servidor devuelve el panel (o la confirmación)
 * ya renderizado de nuevo (HTML) más la cantidad total, y acá simplemente
 * se reemplaza el contenido: la sesión y la base de datos siguen siendo
 * la única fuente de verdad, esto solo evita la recarga completa. */
(function () {
    "use strict";

    function drawer() {
        return document.querySelector("[data-carrito-drawer]");
    }

    function abrir() {
        var el = drawer();
        if (!el) {
            return;
        }
        el.hidden = false;
        // Fuerza el reflow antes de agregar la clase para que la transición
        // de entrada (translateX) se dispare siempre, incluso si el panel
        // acababa de quedar "hidden" recién ahora.
        void el.offsetWidth;
        el.classList.add("carrito-drawer--abierto");
        document.body.classList.add("carrito-drawer-abierto");
    }

    function cerrar() {
        var el = drawer();
        if (!el || el.hidden) {
            return;
        }
        el.classList.remove("carrito-drawer--abierto");
        document.body.classList.remove("carrito-drawer-abierto");
        setTimeout(function () {
            if (!el.classList.contains("carrito-drawer--abierto")) {
                el.hidden = true;
            }
        }, 320);
    }

    function actualizarContador(cantidad) {
        var contador = document.querySelector(".icono-accion__contador");
        if (contador && cantidad !== undefined) {
            contador.textContent = cantidad;
        }
    }

    function actualizarCuerpo(html) {
        var cuerpo = document.querySelector("[data-carrito-cuerpo]");
        if (cuerpo && html !== undefined) {
            cuerpo.innerHTML = html;
        }
    }

    function enviarFormulario(form, alExito) {
        return fetch(form.action, {
            method: "POST",
            headers: { "X-Requested-With": "XMLHttpRequest" },
            credentials: "same-origin",
            body: new FormData(form),
        })
            .then(function (respuesta) {
                return respuesta.json().then(function (datos) {
                    return { ok: respuesta.ok, datos: datos };
                });
            })
            .then(function (resultado) {
                if (resultado.ok && resultado.datos.ok) {
                    actualizarContador(resultado.datos.cantidad);
                    actualizarCuerpo(resultado.datos.html);
                    if (alExito) {
                        alExito(resultado.datos);
                    }
                    return resultado.datos;
                }
                if (resultado.datos && resultado.datos.error) {
                    window.alert(resultado.datos.error);
                }
                return resultado.datos;
            })
            .catch(function () {
                // Sin JS/red: se comporta como un form normal (recarga y
                // redirige), igual que antes de este panel.
                form.submit();
            });
    }

    /* ------------------------------ Stepper "− N +" ------------------------------ */
    /* Reutilizable en cualquier página: solo necesita que el botón −/+ esté
     * dentro del mismo contenedor que un input [data-stepper-valor]. Si ese
     * contenedor es, además, un <form data-carrito-actualizar-form>, cada
     * cambio dispara de una la actualización real del carrito (AJAX); en
     * cualquier otro lado (ej. el formulario de "Agregar al carrito" de la
     * página de producto) solo ajusta el número, sin enviar nada. */
    function ajustarStepper(boton, delta) {
        var contenedor = boton.closest(".stepper-cantidad");
        if (!contenedor) {
            return;
        }
        var input = contenedor.querySelector("[data-stepper-valor]");
        if (!input) {
            return;
        }
        var minimo = parseInt(input.min, 10) || 1;
        var actual = parseInt(input.value, 10) || minimo;
        var nuevo = Math.max(minimo, actual + delta);
        if (nuevo === actual) {
            return;
        }
        input.value = nuevo;

        var formCarrito = contenedor.closest("[data-carrito-actualizar-form]");
        if (formCarrito) {
            enviarFormulario(formCarrito);
        }
    }

    document.addEventListener("click", function (evento) {
        var menos = evento.target.closest("[data-stepper-menos]");
        if (menos) {
            ajustarStepper(menos, -1);
            return;
        }
        var mas = evento.target.closest("[data-stepper-mas]");
        if (mas) {
            ajustarStepper(mas, 1);
            return;
        }
        if (evento.target.closest("[data-carrito-abrir]")) {
            evento.preventDefault();
            abrir();
            return;
        }
        if (evento.target.closest("[data-carrito-cerrar]")) {
            cerrar();
        }
    });

    document.addEventListener("keydown", function (evento) {
        if (evento.key === "Escape") {
            cerrar();
        }
    });

    /* ------------------------------ Formularios ------------------------------ */
    document.addEventListener("submit", function (evento) {
        // Actualizar cantidad desde el drawer (también se dispara solo,
        // sin submit, desde el stepper de arriba — este listener cubre el
        // caso sin JS-stepper, ej. si el input se edita a mano).
        var formActualizar = evento.target.closest("[data-carrito-actualizar-form]");
        if (formActualizar) {
            evento.preventDefault();
            enviarFormulario(formActualizar);
            return;
        }

        var formAgregar = evento.target.closest(".producto-detalle__form");
        if (formAgregar) {
            evento.preventDefault();
            enviarFormulario(formAgregar, abrir);
            return;
        }

        var formQuitar = evento.target.closest("[data-carrito-eliminar-form]");
        if (formQuitar) {
            evento.preventDefault();
            enviarFormulario(formQuitar);
            return;
        }

        var formCheckout = evento.target.closest("[data-carrito-checkout-form]");
        if (formCheckout) {
            evento.preventDefault();
            finalizarPedido(formCheckout);
        }
    });

    function limpiarErrores(form) {
        form.querySelectorAll("[data-error-para]").forEach(function (el) {
            el.textContent = "";
        });
        var general = form.querySelector("[data-error-general]");
        if (general) {
            general.hidden = true;
            general.textContent = "";
        }
    }

    function mostrarErrores(form, datos) {
        limpiarErrores(form);
        if (datos.errors) {
            Object.keys(datos.errors).forEach(function (campo) {
                var el = form.querySelector('[data-error-para="' + campo + '"]');
                var mensaje = datos.errors[campo].map(function (e) { return e.message || e; }).join(" ");
                if (el) {
                    el.textContent = mensaje;
                } else {
                    mostrarErrorGeneral(form, mensaje);
                }
            });
        } else if (datos.error) {
            mostrarErrorGeneral(form, datos.error);
        }
    }

    function mostrarErrorGeneral(form, mensaje) {
        var general = form.querySelector("[data-error-general]");
        if (general) {
            general.hidden = false;
            general.textContent = mensaje;
        }
    }

    function finalizarPedido(form) {
        var boton = form.querySelector("[data-carrito-finalizar-boton]");
        limpiarErrores(form);
        if (boton) {
            boton.disabled = true;
        }
        fetch(form.action, {
            method: "POST",
            headers: { "X-Requested-With": "XMLHttpRequest" },
            credentials: "same-origin",
            body: new FormData(form),
        })
            .then(function (respuesta) {
                return respuesta.json().then(function (datos) {
                    return { ok: respuesta.ok, datos: datos };
                });
            })
            .then(function (resultado) {
                if (resultado.ok && resultado.datos.ok) {
                    actualizarContador(0);
                    actualizarCuerpo(resultado.datos.html);
                } else {
                    mostrarErrores(form, resultado.datos || {});
                }
            })
            .catch(function () {
                form.submit();
            })
            .finally(function () {
                if (boton) {
                    boton.disabled = false;
                }
            });
    }
})();
