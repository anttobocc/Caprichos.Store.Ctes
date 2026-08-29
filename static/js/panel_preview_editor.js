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
    // "flotante-movil": mismo concepto que "flotante" (traduce a
    // --imagen-x/-y/-size, ver estadoInicial/aplicarEstado) pero para las
    // imágenes de .m-card en catalogo.css. A diferencia de "flotante"
    // (recorte fijo dentro de la tarjeta desktop) y "recorte" (0-100
    // siempre), acá la imagen es una capa libre sobre TODA la tarjeta
    // mobile: el rango de posición se extiende bien afuera de 0-100 (ver
    // POS_RANGO) para poder arrastrarla completamente hacia cualquier
    // lado, y el de tamaño no tiene techo atado a ningún recuadro fijo.
    var TERCERO_DEFAULT = {flotante: 260, recorte: 100, "flotante-movil": 100};
    var TERCERO_RANGO = {flotante: [50, 5000], recorte: [100, 200], "flotante-movil": [20, 400]};
    // Rango de X/Y por modo — "flotante" y "recorte" se quedan en 0-100
    // (comportamiento desktop sin cambios); "flotante-movil" es el único
    // que se extiende afuera de ese rango.
    var POS_RANGO = {flotante: [0, 100], recorte: [0, 100], "flotante-movil": [-100, 200]};
    var PASO_BOTON_POS = {flotante: 1, recorte: 2, "flotante-movil": 2};
    var PASO_BOTON_TERCERO = {flotante: 10, recorte: 5, "flotante-movil": 10};
    var SIGNO_DRAG = {flotante: 1, recorte: -1, "flotante-movil": 1};

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
            ' <label class="ppe-aviso__vista">Vista: ' +
                '<select data-ppe-vista>' +
                    '<option value="desktop">Desktop</option>' +
                    '<option value="mobile">Mobile</option>' +
                '</select>' +
            "</label>" +
            ' <a href="/panel/" class="ppe-aviso__volver">← Volver al panel</a>';
        document.body.appendChild(aviso);

        // Selector Desktop/Mobile: agrega body.ppe-vista-mobile o
        // body.ppe-vista-desktop, que en catalogo.css fuerzan cuál de
        // .home-desktop/.home-mobile se ve, sin depender del ancho real
        // de la ventana (el panel normalmente se abre en un navegador de
        // escritorio, así que sin esto nunca se podría ni ver ni tocar
        // las imágenes de .home-mobile para editarlas). Arranca en
        // "desktop" explícito (no ambiguo) para que el primer cambio de
        // vista sea siempre predecible.
        document.body.classList.add("ppe-vista-desktop");
        var selectVista = aviso.querySelector("[data-ppe-vista]");
        selectVista.addEventListener("change", function () {
            cerrarPanel();
            document.body.classList.remove("ppe-vista-desktop", "ppe-vista-mobile");
            document.body.classList.add("ppe-vista-" + selectVista.value);
        });

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
            labelTercero.textContent = modo === "recorte" ? "Zoom" : "Tamaño";
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
            var limitesPos = POS_RANGO[modo];
            estado.actual.x = clamp(estado.actual.x, limitesPos[0], limitesPos[1]);
            estado.actual.y = clamp(estado.actual.y, limitesPos[0], limitesPos[1]);
            estado.actual.tercero = clamp(estado.actual.tercero, limites[0], limites[1]);
            aplicarEstado(actual, estado.actual);
            refrescarPanel();
        }

        // Estado de arrastre ÚNICO a nivel módulo (no una closure por
        // pointerdown): antes cada pointerdown agregaba su propio par de
        // listeners mover/soltar a document, y si un pointerup no llegaba a
        // disparar ese soltar puntual (drag interrumpido, dos clicks muy
        // seguidos, etc.) el listener quedaba pegado escuchando para
        // siempre — un mousemove de OTRA imagen lo disparaba igual y
        // terminaba reescribiendo estado de la imagen equivocada. Con un
        // único estado compartido, un pointerdown nuevo simplemente
        // reemplaza al anterior en vez de acumularse.
        var arrastre = null;

        function iniciarArrastre(el, evento) {
            var estado = estados.get(el);
            var modo = el.getAttribute("data-modo");
            var rect = el.getBoundingClientRect();
            arrastre = {
                el: el,
                pointerId: evento.pointerId,
                estado: estado,
                signo: SIGNO_DRAG[modo],
                inicioX: evento.clientX,
                inicioY: evento.clientY,
                origenX: estado.actual.x,
                origenY: estado.actual.y,
                // refAncho/refAlto son los px que equivalen a un recorrido
                // COMPLETO de 0 a 100 (no a 1 punto): más abajo se divide
                // deltaX/deltaY por esto y se multiplica por 100, así que acá
                // ya hay que dar la referencia "completa". En "recorte" eso
                // es el ancho/alto real del recuadro (a lo ancho del
                // recuadro = 0 a 100%). En "flotante" el CSS público mueve
                // la imagen 1.51858vw por cada punto (ver catalogo.css,
                // .categoria-card__imagen), o sea 151.858vw en los 100
                // puntos completos. En "flotante-movil" el CSS mueve la
                // imagen 1% de SU PROPIO recuadro por cada punto (ver
                // .m-card__imagen img), o sea el 100% de ese recuadro —
                // rect.width/height, igual que "recorte" pero sin invertir
                // el signo (ver SIGNO_DRAG).
                refAncho: modo === "flotante" ? (window.innerWidth * FACTOR_VW_FLOTANTE * 100) : (rect.width || 1),
                refAlto: modo === "flotante" ? (window.innerWidth * FACTOR_VW_FLOTANTE * 100) : (rect.height || 1),
            };
        }

        elementos.forEach(function (el) {
            el.addEventListener("pointerdown", function (evento) {
                evento.preventDefault();
                seleccionar(el);
                iniciarArrastre(el, evento);
            });
        });

        document.addEventListener("pointermove", function (evento) {
            if (!arrastre || evento.pointerId !== arrastre.pointerId) {
                return;
            }
            var deltaX = evento.clientX - arrastre.inicioX;
            var deltaY = evento.clientY - arrastre.inicioY;
            var deltaPorcentualX = (deltaX / arrastre.refAncho) * 100;
            var deltaPorcentualY = (deltaY / arrastre.refAlto) * 100;
            arrastre.estado.actual.x = arrastre.origenX + arrastre.signo * deltaPorcentualX;
            arrastre.estado.actual.y = arrastre.origenY + arrastre.signo * deltaPorcentualY;
            actualizarDesdeEstado();
            if (actual === arrastre.el) {
                posicionarPanel();
            }
        });

        function terminarArrastre(evento) {
            if (!arrastre || (evento && evento.pointerId !== arrastre.pointerId)) {
                return;
            }
            arrastre = null;
        }

        document.addEventListener("pointerup", terminarArrastre);
        document.addEventListener("pointercancel", terminarArrastre);

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
