/* Editor visual sobre la previsualización REAL del sitio (mismo template,
 * mismo CSS que ve un cliente). Se carga solo cuando el panel renderiza una
 * página en modo edición (ver base_catalogo.html); nunca en el frontend
 * público normal.
 *
 * Cada imagen editable trae en su HTML (agregado condicionalmente por los
 * templates cuando modo_edicion es verdadero):
 *   data-editable-imagen           (marca el elemento como editable)
 *   data-entidad                   categoria | producto | combo | configuracion
 *   data-id                        pk de la entidad (ausente para configuracion)
 *   data-prefijo                   imagen | pedidos_imagen | portada_imagen
 *   data-modo                      "recorte" (object-position % + scale) o
 *                                   "flotante" (translate en vw, decoración
 *                                   de categoría/pedidos)
 *   data-nombre                    etiqueta para mostrar en el panel
 *
 * Las posiciones/zoom YA vienen aplicadas por el CSS público vía variables
 * custom (--img-x/--img-y/--img-zoom para "recorte", --imagen-x/--imagen-y/
 * --imagen-size para "flotante") — este script lee esos valores actuales
 * directamente del elemento, así que arrancar a editar nunca "resetea"
 * nada, y actualiza esas mismas variables al arrastrar/ajustar, por lo que
 * el preview es la página real, no una imitación. */
(function () {
    "use strict";

    var FACTOR_VW_FLOTANTE = 0.0151858; // 1 unidad (de 100) = 1.51858vw, igual que catalogo.css
    var TERCERO_DEFAULT = {flotante: 260, recorte: 100};
    var TERCERO_RANGO = {flotante: [50, 5000], recorte: [100, 200]};
    var PASO_BOTON_POS = {flotante: 1, recorte: 2};
    var PASO_BOTON_TERCERO = {flotante: 10, recorte: 5};
    var SIGNO_DRAG = {flotante: 1, recorte: -1};

    function clamp(valor, minimo, maximo) {
        return Math.min(maximo, Math.max(minimo, valor));
    }

    function leerVar(el, nombre, porDefecto) {
        var valor = parseFloat(getComputedStyle(el).getPropertyValue(nombre));
        return isNaN(valor) ? porDefecto : valor;
    }

    function estadoInicial(el) {
        var modo = el.getAttribute("data-modo");
        if (modo === "recorte") {
            return {
                x: leerVar(el, "--img-x", 50),
                y: leerVar(el, "--img-y", 50),
                tercero: leerVar(el, "--img-zoom", 100),
            };
        }
        return {
            x: leerVar(el, "--imagen-x", 50),
            y: leerVar(el, "--imagen-y", 50),
            tercero: leerVar(el, "--imagen-size", 260),
        };
    }

    function aplicarEstado(el, estado) {
        var modo = el.getAttribute("data-modo");
        if (modo === "recorte") {
            el.style.setProperty("--img-x", estado.x);
            el.style.setProperty("--img-y", estado.y);
            el.style.setProperty("--img-zoom", estado.tercero);
        } else {
            el.style.setProperty("--imagen-x", estado.x);
            el.style.setProperty("--imagen-y", estado.y);
            el.style.setProperty("--imagen-size", estado.tercero);
        }
    }

    function iniciar() {
        var elementos = Array.prototype.slice.call(document.querySelectorAll("[data-editable-imagen]"));
        if (!elementos.length) {
            return;
        }

        // Estado por elemento: "guardado" = último valor persistido (o el
        // que trae la página al cargar); "actual" = borrador en memoria que
        // se ve en pantalla pero todavía no se guardó.
        var estados = new WeakMap();
        elementos.forEach(function (el) {
            var inicial = estadoInicial(el);
            estados.set(el, {guardado: inicial, actual: Object.assign({}, inicial)});
        });

        var aviso = document.createElement("div");
        aviso.className = "ppe-aviso";
        aviso.innerHTML = '<span class="ppe-aviso__punto"></span> Modo edición — hacé click en cualquier imagen marcada para moverla o hacer zoom' +
            ' <a href="/panel/" class="ppe-aviso__volver">← Volver al panel</a>';
        document.body.appendChild(aviso);

        var panel = document.createElement("div");
        panel.className = "ppe-panel";
        panel.hidden = true;
        panel.innerHTML =
            '<div class="ppe-panel__header">' +
                '<span class="ppe-panel__nombre" data-ppe-nombre></span>' +
                '<button type="button" class="ppe-panel__cerrar" aria-label="Cerrar">✕</button>' +
            "</div>" +
            '<div class="ppe-panel__eje">' +
                "<label>X</label>" +
                '<button type="button" data-ppe-boton="x" data-delta="-1">−</button>' +
                '<input type="number" data-ppe-campo="x">' +
                '<button type="button" data-ppe-boton="x" data-delta="1">+</button>' +
            "</div>" +
            '<div class="ppe-panel__eje">' +
                "<label>Y</label>" +
                '<button type="button" data-ppe-boton="y" data-delta="-1">−</button>' +
                '<input type="number" data-ppe-campo="y">' +
                '<button type="button" data-ppe-boton="y" data-delta="1">+</button>' +
            "</div>" +
            '<div class="ppe-panel__eje">' +
                "<label data-ppe-label-tercero>Zoom</label>" +
                '<button type="button" data-ppe-boton="tercero" data-delta="-1">−</button>' +
                '<input type="number" data-ppe-campo="tercero">' +
                '<button type="button" data-ppe-boton="tercero" data-delta="1">+</button>' +
            "</div>" +
            '<div class="ppe-panel__acciones">' +
                '<button type="button" data-ppe-restablecer>Restablecer</button>' +
                '<button type="button" data-ppe-cancelar>Cancelar</button>' +
                '<button type="button" class="ppe-panel__guardar" data-ppe-guardar>Guardar cambios</button>' +
            "</div>" +
            '<p class="ppe-panel__estado" data-ppe-estado></p>';
        document.body.appendChild(panel);

        var campoX = panel.querySelector('[data-ppe-campo="x"]');
        var campoY = panel.querySelector('[data-ppe-campo="y"]');
        var campoTercero = panel.querySelector('[data-ppe-campo="tercero"]');
        var labelTercero = panel.querySelector("[data-ppe-label-tercero]");
        var nombreEl = panel.querySelector("[data-ppe-nombre]");
        var estadoTexto = panel.querySelector("[data-ppe-estado]");

        var actual = null; // elemento actualmente seleccionado

        function limitesTercero(modo) {
            return TERCERO_RANGO[modo];
        }

        function refrescarPanel() {
            if (!actual) {
                return;
            }
            var estado = estados.get(actual);
            var modo = actual.getAttribute("data-modo");
            campoX.value = Math.round(estado.actual.x);
            campoY.value = Math.round(estado.actual.y);
            campoTercero.value = Math.round(estado.actual.tercero);
            labelTercero.textContent = modo === "flotante" ? "Tamaño" : "Zoom";
            nombreEl.textContent = actual.getAttribute("data-nombre") || "Imagen";
        }

        function posicionarPanel() {
            if (!actual) {
                return;
            }
            var rect = actual.getBoundingClientRect();
            var anchoPanel = 250;
            var margen = 12;
            var left = rect.right + margen;
            if (left + anchoPanel > window.innerWidth - margen) {
                left = rect.left - anchoPanel - margen;
            }
            if (left < margen) {
                left = clamp(rect.left, margen, Math.max(margen, window.innerWidth - anchoPanel - margen));
            }
            var top = clamp(rect.top, 52, Math.max(52, window.innerHeight - 320));
            panel.style.left = left + "px";
            panel.style.top = top + "px";
        }

        function mostrarEstado(mensaje, tipo) {
            estadoTexto.textContent = mensaje || "";
            estadoTexto.classList.remove("ppe-panel__estado--ok", "ppe-panel__estado--error");
            if (tipo) {
                estadoTexto.classList.add("ppe-panel__estado--" + tipo);
            }
        }

        function seleccionar(el) {
            if (actual === el) {
                return;
            }
            if (actual) {
                actual.classList.remove("ppe-seleccionada");
            }
            actual = el;
            actual.classList.add("ppe-seleccionada");
            panel.hidden = false;
            mostrarEstado("");
            refrescarPanel();
            posicionarPanel();
        }

        function cerrarPanel() {
            if (actual) {
                actual.classList.remove("ppe-seleccionada");
            }
            actual = null;
            panel.hidden = true;
        }

        function actualizarDesdeEstado() {
            if (!actual) {
                return;
            }
            var estado = estados.get(actual);
            var modo = actual.getAttribute("data-modo");
            var limites = limitesTercero(modo);
            estado.actual.x = clamp(estado.actual.x, 0, 100);
            estado.actual.y = clamp(estado.actual.y, 0, 100);
            estado.actual.tercero = clamp(estado.actual.tercero, limites[0], limites[1]);
            aplicarEstado(actual, estado.actual);
            refrescarPanel();
        }

        elementos.forEach(function (el) {
            el.addEventListener("pointerdown", function (evento) {
                evento.preventDefault();
                seleccionar(el);

                var estado = estados.get(el);
                var modo = el.getAttribute("data-modo");
                var signo = SIGNO_DRAG[modo];
                var inicioX = evento.clientX;
                var inicioY = evento.clientY;
                var origenX = estado.actual.x;
                var origenY = estado.actual.y;
                var rect = el.getBoundingClientRect();
                var refAncho = modo === "recorte" ? (rect.width || 1) : (window.innerWidth * FACTOR_VW_FLOTANTE);
                var refAlto = modo === "recorte" ? (rect.height || 1) : (window.innerWidth * FACTOR_VW_FLOTANTE);
                var movido = false;

                function mover(e) {
                    var deltaX = e.clientX - inicioX;
                    var deltaY = e.clientY - inicioY;
                    if (Math.abs(deltaX) > 2 || Math.abs(deltaY) > 2) {
                        movido = true;
                    }
                    var deltaPorcentualX = (deltaX / refAncho) * 100;
                    var deltaPorcentualY = (deltaY / refAlto) * 100;
                    estado.actual.x = origenX + signo * deltaPorcentualX;
                    estado.actual.y = origenY + signo * deltaPorcentualY;
                    actualizarDesdeEstado();
                    if (actual === el) {
                        posicionarPanel();
                    }
                }

                function soltar() {
                    document.removeEventListener("pointermove", mover);
                    document.removeEventListener("pointerup", soltar);
                }

                document.addEventListener("pointermove", mover);
                document.addEventListener("pointerup", soltar);
            });
        });

        // Mientras se edita, ninguna imagen editable debe navegar (algunas
        // están envueltas en un <a> que en el sitio normal lleva al
        // detalle del producto).
        document.addEventListener("click", function (evento) {
            if (evento.target.closest("[data-editable-imagen]")) {
                evento.preventDefault();
                evento.stopPropagation();
            }
        }, true);

        panel.querySelectorAll("[data-ppe-boton]").forEach(function (boton) {
            boton.addEventListener("click", function () {
                if (!actual) {
                    return;
                }
                var estado = estados.get(actual);
                var modo = actual.getAttribute("data-modo");
                var eje = boton.getAttribute("data-ppe-boton");
                var delta = parseInt(boton.getAttribute("data-delta"), 10);
                if (eje === "tercero") {
                    estado.actual.tercero += delta * PASO_BOTON_TERCERO[modo];
                } else {
                    estado.actual[eje] += delta * PASO_BOTON_POS[modo];
                }
                actualizarDesdeEstado();
            });
        });

        [["x", campoX], ["y", campoY], ["tercero", campoTercero]].forEach(function (par) {
            var eje = par[0];
            var input = par[1];
            input.addEventListener("input", function () {
                if (!actual) {
                    return;
                }
                var estado = estados.get(actual);
                var valor = parseFloat(input.value);
                if (!isNaN(valor)) {
                    estado.actual[eje] = valor;
                    actualizarDesdeEstado();
                }
            });
        });

        panel.querySelector("[data-ppe-restablecer]").addEventListener("click", function () {
            if (!actual) {
                return;
            }
            var estado = estados.get(actual);
            var modo = actual.getAttribute("data-modo");
            estado.actual = {x: 50, y: 50, tercero: TERCERO_DEFAULT[modo]};
            actualizarDesdeEstado();
            mostrarEstado("Restablecido (sin guardar todavía).");
        });

        panel.querySelector("[data-ppe-cancelar]").addEventListener("click", function () {
            if (!actual) {
                return;
            }
            var estado = estados.get(actual);
            estado.actual = Object.assign({}, estado.guardado);
            actualizarDesdeEstado();
            mostrarEstado("Cambios descartados.");
        });

        panel.querySelector(".ppe-panel__cerrar").addEventListener("click", cerrarPanel);

        panel.querySelector("[data-ppe-guardar]").addEventListener("click", function () {
            if (!actual) {
                return;
            }
            var el = actual;
            var estado = estados.get(el);
            var payload = {
                entidad: el.getAttribute("data-entidad"),
                id: el.getAttribute("data-id") ? parseInt(el.getAttribute("data-id"), 10) : null,
                prefijo: el.getAttribute("data-prefijo"),
                pos_x: Math.round(estado.actual.x),
                pos_y: Math.round(estado.actual.y),
                valor: Math.round(estado.actual.tercero),
            };
            mostrarEstado("Guardando…");
            fetch(window.CAPRICHO_GUARDAR_IMAGEN_URL, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": window.CAPRICHO_CSRF_TOKEN,
                },
                credentials: "same-origin",
                body: JSON.stringify(payload),
            })
                .then(function (respuesta) {
                    return respuesta.json().then(function (datos) {
                        return {ok: respuesta.ok, datos: datos};
                    });
                })
                .then(function (resultado) {
                    if (resultado.ok && resultado.datos.ok) {
                        estado.guardado = Object.assign({}, estado.actual);
                        mostrarEstado("Guardado ✓", "ok");
                    } else {
                        var mensaje = (resultado.datos && resultado.datos.error) || "No se pudo guardar.";
                        mostrarEstado(mensaje, "error");
                    }
                })
                .catch(function () {
                    mostrarEstado("Error de conexión al guardar.", "error");
                });
        });

        document.addEventListener("keydown", function (evento) {
            if (evento.key === "Escape") {
                cerrarPanel();
            }
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", iniciar);
    } else {
        iniciar();
    }
})();
