from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST

from catalogo.models import Combo, Producto, VarianteProducto
from panel.models import ConfiguracionNegocio

from . import whatsapp
from .carrito import Carrito
from .envio import costo_envio as _costo_envio
from .forms import CheckoutForm
from .models import ItemPedido, Pedido

LOGIN_URL_CLIENTE = "usuarios:login"
SESSION_KEY_ULTIMO_PEDIDO = "ultimo_pedido_id"


def _cantidad_valida(valor):
    try:
        cantidad = int(valor)
    except (TypeError, ValueError):
        return None
    if cantidad < 1:
        return None
    return cantidad


def _es_ajax(request):
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


def _respuesta_drawer_json(request, error=None):
    """Arma la respuesta JSON que usa el panel lateral del carrito
    (static/js/carrito_drawer.js) para refrescarse sin recargar la página:
    el HTML ya renderizado del drawer + la cantidad total de unidades."""
    if error:
        return JsonResponse({"ok": False, "error": error}, status=400)
    carrito = Carrito(request)
    lineas = carrito.items()
    html = render_to_string("pedidos/_carrito_drawer.html", {
        "carrito_lineas": lineas,
        "carrito_total": carrito.total(),
        "carrito_hay_no_disponibles": carrito.hay_no_disponibles(),
    }, request=request)
    return JsonResponse({"ok": True, "cantidad": sum(l.cantidad for l in lineas), "html": html})


def carrito_ver(request):
    carrito = Carrito(request)
    avisos = []
    lineas = carrito.items(mensajes=avisos)
    for aviso in avisos:
        messages.warning(request, aviso)
    return render(request, "pedidos/carrito.html", {
        "lineas": lineas,
        "total": carrito.total(),
        "hay_no_disponibles": carrito.hay_no_disponibles(),
    })


@require_POST
def carrito_agregar(request, producto_id):
    producto = get_object_or_404(Producto, pk=producto_id, activo=True)
    es_ajax = _es_ajax(request)

    variante = None
    variante_id = request.POST.get("variante_id")
    if producto.tiene_variantes:
        if not variante_id:
            if es_ajax:
                return _respuesta_drawer_json(request, error="Elegí una opción antes de agregar este producto.")
            messages.error(request, "Elegí una opción antes de agregar este producto.")
            return redirect("catalogo:producto_detalle", slug=producto.slug)
        variante = VarianteProducto.objects.filter(pk=variante_id, producto=producto, activo=True).first()
        if variante is None:
            if es_ajax:
                return _respuesta_drawer_json(request, error="La opción elegida ya no está disponible.")
            messages.error(request, "La opción elegida ya no está disponible.")
            return redirect("catalogo:producto_detalle", slug=producto.slug)
    elif variante_id:
        # El producto no tiene variantes activas: cualquier variante_id enviado se ignora/rechaza.
        if es_ajax:
            return _respuesta_drawer_json(request, error="Este producto no tiene opciones para elegir.")
        messages.error(request, "Este producto no tiene opciones para elegir.")
        return redirect("catalogo:producto_detalle", slug=producto.slug)

    cantidad = _cantidad_valida(request.POST.get("cantidad", 1))
    if cantidad is None:
        if es_ajax:
            return _respuesta_drawer_json(request, error="La cantidad debe ser un número entero mayor o igual a 1.")
        messages.error(request, "La cantidad debe ser un número entero mayor o igual a 1.")
        return redirect("catalogo:producto_detalle", slug=producto.slug)

    Carrito(request).agregar(producto, variante, cantidad)
    if es_ajax:
        return _respuesta_drawer_json(request)
    messages.success(request, f'"{producto.nombre}" se agregó al carrito.')
    return redirect("pedidos:carrito")


@require_POST
def carrito_agregar_combo(request, combo_id):
    combo = get_object_or_404(Combo, pk=combo_id, activo=True)
    es_ajax = _es_ajax(request)

    cantidad = _cantidad_valida(request.POST.get("cantidad", 1))
    if cantidad is None:
        if es_ajax:
            return _respuesta_drawer_json(request, error="La cantidad debe ser un número entero mayor o igual a 1.")
        messages.error(request, "La cantidad debe ser un número entero mayor o igual a 1.")
        return redirect("catalogo:combo_detalle", slug=combo.slug)

    Carrito(request).agregar_combo(combo, cantidad)
    if es_ajax:
        return _respuesta_drawer_json(request)
    messages.success(request, f'"{combo.nombre}" se agregó al carrito.')
    return redirect("pedidos:carrito")


@require_POST
def carrito_actualizar(request, clave):
    cantidad = _cantidad_valida(request.POST.get("cantidad"))
    if cantidad is None:
        if _es_ajax(request):
            return _respuesta_drawer_json(request, error="La cantidad debe ser un número entero mayor o igual a 1.")
        messages.error(request, "La cantidad debe ser un número entero mayor o igual a 1.")
        return redirect("pedidos:carrito")
    Carrito(request).actualizar_cantidad(clave, cantidad)
    if _es_ajax(request):
        return _respuesta_drawer_json(request)
    return redirect("pedidos:carrito")


@require_POST
def carrito_eliminar(request, clave):
    Carrito(request).eliminar(clave)
    if _es_ajax(request):
        return _respuesta_drawer_json(request)
    return redirect("pedidos:carrito")


@require_POST
def carrito_vaciar(request):
    Carrito(request).vaciar()
    return redirect("pedidos:carrito")


def checkout(request):
    carrito = Carrito(request)
    lineas = carrito.items()
    es_ajax = _es_ajax(request)

    if not lineas:
        if es_ajax:
            return JsonResponse({"ok": False, "error": "Tu carrito está vacío."}, status=400)
        messages.warning(request, "Tu carrito está vacío.")
        return redirect("pedidos:carrito")

    if carrito.hay_no_disponibles():
        if es_ajax:
            return JsonResponse(
                {"ok": False, "error": "Hay productos no disponibles en tu carrito. Quitalos para poder continuar."},
                status=400,
            )
        messages.error(request, "Hay productos no disponibles en tu carrito. Quitalos para poder continuar.")
        return redirect("pedidos:carrito")

    subtotal = carrito.total()
    config = ConfiguracionNegocio.get_solo()

    usuario = request.user if request.user.is_authenticated else None

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            # Revalidación completa justo antes de confirmar: entre mostrar
            # el carrito y este POST pudo haber cambiado algo (Etapa 5,
            # punto 12): se vuelve a resolver todo desde la base, nunca se
            # confía en lo que se mostró antes.
            lineas = carrito.items()
            if not lineas:
                if es_ajax:
                    return JsonResponse({"ok": False, "error": "Tu carrito está vacío."}, status=400)
                messages.warning(request, "Tu carrito está vacío.")
                return redirect("pedidos:carrito")
            if carrito.hay_no_disponibles():
                if es_ajax:
                    return JsonResponse({
                        "ok": False,
                        "error": "Hay productos no disponibles en tu carrito. Quitalos para poder continuar.",
                    }, status=400)
                messages.error(request, "Hay productos no disponibles en tu carrito. Quitalos para poder continuar.")
                return redirect("pedidos:carrito")

            subtotal = carrito.total()
            tipo_entrega = form.cleaned_data["tipo_entrega"]
            costo_envio = _costo_envio(config, tipo_entrega, subtotal)
            total = subtotal + costo_envio

            with transaction.atomic():
                pedido = form.save(commit=False)
                pedido.usuario = usuario
                pedido.estado = Pedido.Estado.PENDIENTE
                pedido.total = total
                pedido.save()

                for linea in lineas:
                    es_combo = linea.producto is None
                    ItemPedido.objects.create(
                        pedido=pedido,
                        producto=linea.producto,
                        variante=linea.variante,
                        combo=linea.combo if es_combo else None,
                        nombre_producto=linea.nombre,
                        nombre_variante=linea.variante.nombre if linea.variante else "",
                        cantidad=linea.cantidad,
                        precio_unitario=linea.precio_unitario,
                    )

            carrito.vaciar()
            request.session[SESSION_KEY_ULTIMO_PEDIDO] = pedido.pk
            if es_ajax:
                whatsapp_url = whatsapp.construir_url(pedido)
                return JsonResponse({
                    "ok": True,
                    "pedido_id": pedido.pk,
                    "whatsapp_url": whatsapp_url,
                    "html": render_to_string(
                        "pedidos/_carrito_confirmacion.html",
                        {"pedido": pedido, "whatsapp_url": whatsapp_url},
                        request=request,
                    ),
                })
            messages.success(request, "¡Tu pedido fue confirmado!")
            return redirect("pedidos:pedido_detalle", pk=pedido.pk)
        elif es_ajax:
            errores = {campo: list(map(str, lista)) for campo, lista in form.errors.items()}
            return JsonResponse({"ok": False, "errors": errores}, status=400)
    else:
        perfil = getattr(usuario, "perfil", None) if usuario else None
        initial = {
            "nombre_completo": f"{usuario.first_name} {usuario.last_name}".strip() if usuario else "",
            "telefono": perfil.telefono if perfil else "",
        }
        form = CheckoutForm(initial=initial)

    costo_envio_actual = _costo_envio(config, Pedido.TipoEntrega.ENVIO, subtotal)
    return render(request, "pedidos/checkout.html", {
        "form": form,
        "lineas": lineas,
        "subtotal": subtotal,
        "costo_envio_estimado_con_envio": costo_envio_actual,
        "config": config,
    })


@login_required(login_url=LOGIN_URL_CLIENTE)
def mis_pedidos(request):
    pedidos = Pedido.objects.filter(usuario=request.user).order_by("-fecha_creacion")
    return render(request, "pedidos/mis_pedidos.html", {"pedidos": pedidos})


def pedido_detalle(request, pk):
    pedido = get_object_or_404(Pedido.objects.prefetch_related("items"), pk=pk)

    es_dueno = request.user.is_authenticated and pedido.usuario_id == request.user.id
    es_pedido_recien_confirmado = request.session.get(SESSION_KEY_ULTIMO_PEDIDO) == pedido.pk
    if not (es_dueno or es_pedido_recien_confirmado):
        raise Http404

    return render(request, "pedidos/pedido_detalle.html", {
        "pedido": pedido,
        "whatsapp_url": whatsapp.construir_url(pedido),
    })
