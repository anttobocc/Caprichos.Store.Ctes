/* Variantes de producto: dos responsabilidades independientes.
 *
 * 1) Prellena las variantes de un producto NUEVO según su categoría
 *    (Empanadas: cantidad x modalidad; Alfajores/Tartas: solo cantidad;
 *    otras categorías: sin plantilla, formset vacío como hasta ahora).
 *    Solo actúa sobre paneles marcados data-modo="crear": al editar un
 *    producto existente nunca se tocan sus variantes ya guardadas por este
 *    script. Depende de window.CAPRICHO_PLANTILLAS_VARIANTES (JSON
 *    embebido por la vista, clave = id de categoría, valor = lista de
 *    {nombre, modalidad, modalidad_label}).
 *
 * 2) Reordena las variantes arrastrando su fila (como una playlist): cada
 *    fila tiene un handle "⠿⠿" (data-arrastrar); al soltarla se recalcula
 *    el campo oculto "orden" de cada fila según su posición final en el
 *    DOM. No hay input numérico de orden visible para el usuario. */
(function () {
    "use strict";

    function crearCampo(tag, attrs) {
        var el = document.createElement(tag);
        Object.keys(attrs || {}).forEach(function (clave) {
            if (attrs[clave] !== undefined && attrs[clave] !== null) {
                el.setAttribute(clave, attrs[clave]);
            }
        });
        return el;
    }

    function campoConEtiqueta(etiqueta, hijo) {
        var contenedor = document.createElement("div");
        contenedor.className = "admin-variante-fila__campo";
        var label = document.createElement("label");
        label.textContent = etiqueta;
        contenedor.appendChild(label);
        contenedor.appendChild(hijo);
        return contenedor;
    }

    function construirFila(indice, fila) {
        var div = document.createElement("div");
        div.className = "admin-variante-fila";
        div.setAttribute("data-variante-fila", "");

        var orden = crearCampo("input", {
            type: "hidden", name: "variantes-" + indice + "-orden", value: String(indice),
        });
        div.appendChild(orden);

        var handle = crearCampo("button", { type: "button", "data-arrastrar": "", "aria-label": "Arrastrar para reordenar" });
        handle.className = "admin-variante-fila__handle";
        handle.textContent = "⠿⠿";
        div.appendChild(handle);

        var modalidadHijo;
        if (fila.modalidad) {
            var envoltorioModalidad = document.createElement("span");
            envoltorioModalidad.textContent = fila.modalidad_label || fila.modalidad;
            var modalidadOculto = crearCampo("input", {
                type: "hidden", name: "variantes-" + indice + "-modalidad", value: fila.modalidad,
            });
            envoltorioModalidad.appendChild(modalidadOculto);
            modalidadHijo = envoltorioModalidad;
        } else {
            modalidadHijo = crearCampo("input", {
                type: "hidden", name: "variantes-" + indice + "-modalidad", value: "",
            });
        }
        div.appendChild(campoConEtiqueta("Modalidad", modalidadHijo));

        var nombre = crearCampo("input", {
            type: "text", name: "variantes-" + indice + "-nombre", value: fila.nombre,
        });
        div.appendChild(campoConEtiqueta("Cantidad", nombre));

        var precio = crearCampo("input", {
            type: "number", step: "0.01", min: "0", name: "variantes-" + indice + "-precio",
        });
        div.appendChild(campoConEtiqueta("Precio", precio));

        var eliminarVacio = document.createElement("span");
        eliminarVacio.className = "admin-variante-fila__eliminar admin-variante-fila__eliminar--vacio";
        eliminarVacio.setAttribute("aria-hidden", "true");
        div.appendChild(eliminarVacio);

        return div;
    }

    function repoblar(panel, categoriaId) {
        var plantillas = window.CAPRICHO_PLANTILLAS_VARIANTES || {};
        var filas = plantillas[categoriaId];
        var cuerpo = panel.querySelector("[data-variantes-body]");
        var totalInput = panel.querySelector('input[name="variantes-TOTAL_FORMS"]');
        if (!cuerpo || !totalInput) {
            return;
        }
        cuerpo.innerHTML = "";
        (filas || []).forEach(function (fila, indice) {
            cuerpo.appendChild(construirFila(indice, fila));
        });
        totalInput.value = String((filas || []).length);
    }

    document.addEventListener("change", function (evento) {
        var select = evento.target.closest('[data-modo="crear"] select[name="categoria"]');
        if (!select) {
            return;
        }
        var panel = select.closest("[data-modo]");
        if (panel) {
            repoblar(panel, select.value);
        }
    });

    /* ------------------------- Arrastrar para reordenar ------------------------- */

    function filasDe(contenedor) {
        return Array.prototype.slice.call(contenedor.children).filter(function (el) {
            return el.hasAttribute("data-variante-fila");
        });
    }

    function filaEstaVacia(fila) {
        // La fila "extra" en blanco del formset (para cargar una variante
        // nueva) no debe tocarse: si le reescribimos "orden" con un valor
        // distinto al inicial, Django la considera "modificada" y exige
        // sus demás campos obligatorios (cantidad, precio), rompiendo el
        // guardado aunque el usuario no haya cargado nada ahí.
        var id = fila.querySelector('input[name$="-id"]');
        var nombre = fila.querySelector('input[name$="-nombre"]');
        var precio = fila.querySelector('input[name$="-precio"]');
        var tieneId = id && id.value;
        var tieneNombre = nombre && nombre.value.trim();
        var tienePrecio = precio && precio.value.trim();
        return !tieneId && !tieneNombre && !tienePrecio;
    }

    function actualizarOrden(contenedor) {
        var indice = 0;
        filasDe(contenedor).forEach(function (fila) {
            if (filaEstaVacia(fila)) {
                return;
            }
            var ordenInput = fila.querySelector('input[name$="-orden"]');
            if (ordenInput) {
                ordenInput.value = String(indice);
            }
            indice += 1;
        });
    }

    var filaActiva = null;
    var contenedorActivo = null;

    document.addEventListener("pointerdown", function (evento) {
        var handle = evento.target.closest("[data-arrastrar]");
        if (!handle) {
            return;
        }
        var fila = handle.closest("[data-variante-fila]");
        if (!fila || !fila.parentElement) {
            return;
        }
        filaActiva = fila;
        contenedorActivo = fila.parentElement;
        fila.classList.add("admin-variante-fila--arrastrando");
        try {
            handle.setPointerCapture(evento.pointerId);
        } catch (err) { /* no-op: algunos navegadores viejos no soportan pointer capture */ }
        evento.preventDefault();
    });

    document.addEventListener("pointermove", function (evento) {
        if (!filaActiva || !contenedorActivo) {
            return;
        }
        var y = evento.clientY;
        var hermanas = filasDe(contenedorActivo).filter(function (f) { return f !== filaActiva; });
        for (var i = 0; i < hermanas.length; i++) {
            var hermana = hermanas[i];
            var rect = hermana.getBoundingClientRect();
            var medio = rect.top + rect.height / 2;
            var posicion = filaActiva.compareDocumentPosition(hermana);
            var hermanaEstaDespues = !!(posicion & Node.DOCUMENT_POSITION_FOLLOWING);
            if (hermanaEstaDespues && y > medio) {
                contenedorActivo.insertBefore(filaActiva, hermana.nextSibling);
                break;
            }
            if (!hermanaEstaDespues && y < medio) {
                contenedorActivo.insertBefore(filaActiva, hermana);
                break;
            }
        }
    });

    function soltar() {
        if (!filaActiva || !contenedorActivo) {
            return;
        }
        filaActiva.classList.remove("admin-variante-fila--arrastrando");
        actualizarOrden(contenedorActivo);
        filaActiva = null;
        contenedorActivo = null;
    }

    document.addEventListener("pointerup", soltar);
    document.addEventListener("pointercancel", soltar);
})();
