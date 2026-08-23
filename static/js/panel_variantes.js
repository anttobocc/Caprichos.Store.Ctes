/* Prellena las variantes de un producto NUEVO según su categoría (Empanadas:
 * cantidad x modalidad; Alfajores/Tartas: solo cantidad; otras categorías:
 * sin plantilla, formset vacío como hasta ahora). Solo actúa sobre paneles
 * marcados data-modo="crear": al editar un producto existente nunca se
 * tocan sus variantes ya guardadas por este script. Depende de
 * window.CAPRICHO_PLANTILLAS_VARIANTES (JSON embebido por la vista, clave =
 * id de categoría, valor = lista de {nombre, modalidad, modalidad_label}). */
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

    function celda(hijo) {
        var td = document.createElement("td");
        td.appendChild(hijo);
        return td;
    }

    function construirFila(indice, fila) {
        var tr = document.createElement("tr");

        var nombre = crearCampo("input", {
            type: "text", name: "variantes-" + indice + "-nombre", value: fila.nombre,
        });
        tr.appendChild(celda(nombre));

        var modalidadTd = document.createElement("td");
        if (fila.modalidad) {
            var etiqueta = document.createElement("span");
            etiqueta.textContent = fila.modalidad_label || fila.modalidad;
            modalidadTd.appendChild(etiqueta);
        }
        var modalidadOculto = crearCampo("input", {
            type: "hidden", name: "variantes-" + indice + "-modalidad", value: fila.modalidad || "",
        });
        modalidadTd.appendChild(modalidadOculto);
        tr.appendChild(modalidadTd);

        var precio = crearCampo("input", {
            type: "number", step: "0.01", min: "0", name: "variantes-" + indice + "-precio",
        });
        tr.appendChild(celda(precio));

        var orden = crearCampo("input", {
            type: "number", name: "variantes-" + indice + "-orden", value: String(indice),
        });
        tr.appendChild(celda(orden));

        var activo = crearCampo("input", { type: "checkbox", name: "variantes-" + indice + "-activo" });
        activo.checked = true;
        tr.appendChild(celda(activo));

        tr.appendChild(document.createElement("td"));

        return tr;
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
})();
