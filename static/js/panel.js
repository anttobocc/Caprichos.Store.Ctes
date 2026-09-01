/* Componentes reutilizables del panel de Capricho.
 *
 * Modal (confirmaciones): cualquier botón con data-modal-target="#id-del-dialog"
 * abre ese <dialog>. data-modal-close cierra el <dialog> más cercano.
 *
 * Panel de formulario (alta/edición, integrado en el layout de la página, no
 * es un drawer/overlay): cualquier botón con data-panel-target="#id-del-panel"
 * muestra ese panel dentro de su contenedor ".admin-lista-con-formulario" y
 * oculta los demás paneles del mismo contenedor. data-panel-close lo oculta. */
(function () {
    "use strict";

    function abrirPanel(panel, categoriaPreseleccionada) {
        const contenedor = panel.closest(".admin-lista-con-formulario");
        if (contenedor) {
            contenedor.querySelectorAll(".admin-panel-form").forEach(function (otro) {
                if (otro !== panel) {
                    otro.hidden = true;
                }
            });
            contenedor.classList.add("tiene-formulario-abierto");
        }
        if (categoriaPreseleccionada) {
            const selectCategoria = panel.querySelector('select[name="categoria"]');
            if (selectCategoria) {
                selectCategoria.value = categoriaPreseleccionada;
            }
        }
        panel.hidden = false;
        panel.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }

    function cerrarPanel(panel) {
        panel.hidden = true;
        const contenedor = panel.closest(".admin-lista-con-formulario");
        if (contenedor && !contenedor.querySelector(".admin-panel-form:not([hidden])")) {
            contenedor.classList.remove("tiene-formulario-abierto");
        }
    }

    /* Nav off-canvas mobile (header ☰, ver base_panel.html/panel.css): no depende
     * del ancho de pantalla acá, solo de que exista el marcado (en escritorio
     * .panel-header-movil/.panel-nav-movil están display:none, así que el botón
     * que abre esto ni se ve). */
    function abrirNavMovil() {
        const nav = document.querySelector(".panel-nav-movil");
        const backdrop = document.querySelector(".panel-nav-backdrop");
        const boton = document.querySelector("[data-panel-nav-abrir]");
        if (!nav) return;
        nav.classList.add("panel-nav-movil--abierta");
        nav.setAttribute("aria-hidden", "false");
        if (backdrop) backdrop.hidden = false;
        if (boton) boton.setAttribute("aria-expanded", "true");
        document.body.classList.add("panel-nav-movil-abierto");
    }

    function cerrarNavMovil() {
        const nav = document.querySelector(".panel-nav-movil");
        const backdrop = document.querySelector(".panel-nav-backdrop");
        const boton = document.querySelector("[data-panel-nav-abrir]");
        if (!nav) return;
        nav.classList.remove("panel-nav-movil--abierta");
        nav.setAttribute("aria-hidden", "true");
        if (backdrop) backdrop.hidden = true;
        if (boton) boton.setAttribute("aria-expanded", "false");
        document.body.classList.remove("panel-nav-movil-abierto");
    }

    document.addEventListener("keydown", function (evento) {
        if (evento.key === "Escape") {
            cerrarNavMovil();
        }
    });

    document.addEventListener("click", function (evento) {
        const abridorNav = evento.target.closest("[data-panel-nav-abrir]");
        if (abridorNav) {
            abrirNavMovil();
            return;
        }

        const cerradorNav = evento.target.closest("[data-panel-nav-cerrar]");
        if (cerradorNav) {
            cerrarNavMovil();
            return;
        }

        const abridorModal = evento.target.closest("[data-modal-target]");
        if (abridorModal) {
            const dialogo = document.querySelector(abridorModal.getAttribute("data-modal-target"));
            if (dialogo && typeof dialogo.showModal === "function") {
                dialogo.showModal();
            }
            return;
        }

        const abridorPanel = evento.target.closest("[data-panel-target]");
        if (abridorPanel) {
            const panel = document.querySelector(abridorPanel.getAttribute("data-panel-target"));
            if (panel) {
                abrirPanel(panel, abridorPanel.getAttribute("data-panel-preset-categoria"));
            }
            return;
        }

        const cerradorModal = evento.target.closest("[data-modal-close]");
        if (cerradorModal) {
            const dialogo = cerradorModal.closest("dialog");
            if (dialogo) {
                dialogo.close();
                return;
            }
        }

        const cerradorPanel = evento.target.closest("[data-panel-close]");
        if (cerradorPanel) {
            const panel = cerradorPanel.closest(".admin-panel-form");
            if (panel) {
                cerrarPanel(panel);
            }
            return;
        }

        const cerradorToast = evento.target.closest("[data-toast-close]");
        if (cerradorToast) {
            quitarToast(cerradorToast.closest(".admin-toast"));
        }
    });

    /* Toasts: no bloquean la pantalla ni requieren "Aceptar" (a diferencia
     * del modal de confirmación de eliminar). Se quitan solos a los pocos
     * segundos o al hacer clic en la X. */
    function quitarToast(toast) {
        if (!toast || toast.dataset.saliendo) {
            return;
        }
        toast.dataset.saliendo = "1";
        toast.classList.add("admin-toast--saliendo");
        toast.addEventListener("animationend", function () {
            toast.remove();
        });
        setTimeout(function () {
            toast.remove();
        }, 400);
    }

    document.addEventListener("DOMContentLoaded", function () {
        document.querySelectorAll(".admin-toast").forEach(function (toast) {
            setTimeout(function () {
                quitarToast(toast);
            }, 4500);
        });
    });
})();
