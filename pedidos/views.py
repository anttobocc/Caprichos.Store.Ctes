from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from catalogo.models import Producto, VarianteProducto
from panel.models import ConfiguracionNegocio

from . import whatsapp
from .carrito import Carrito
from .forms import CheckoutForm
from .models import ItemPedido, Pedido

LOGIN_URL_CLIENTE = "usuarios:login"
SESSION_KEY_ULTIMO_PEDIDO = "ultimo_pedido_id"


def _costo_envio(config, tipo_entrega, subtotal):
    """Servidor calcula el costo de envío, nunca se confía en el frontend."""
    if tipo_entrega != Pedido.TipoEntrega.ENVIO:
        return Decimal("0")
    if not config.envio_habilitado:
        return Decimal("0")
    if config.envio_gratis_desde is not None and subtotal >= config.envio_gratis_desde:
        return Decimal("0")
    return config.costo_envio or Decimal("0")


def _cantidad_valida(valor):
    try:
        cantidad = int(valor)
    except (TypeError, ValueError):
        return None
    if cantidad < 1:
        return None
    return cantidad


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

    variante = None
    variante_id = request.POST.get("variante_id")
    if producto.tiene_variantes:
        if not variante_id:
            messages.error(request, "Elegí una opción antes de agregar este producto.")
            return redirect("catalogo:producto_detalle", slug=producto.slug)
        variante = VarianteProducto.objects.filter(pk=variante_id, producto=producto, activo=True).first()
        if variante is None:
            messages.error(request, "La opción elegida ya no está disponible.")
            return redirect("catalogo:producto_detalle", slug=producto.slug)
    elif variante_id:
        # El producto no tiene variantes activas: cualquier variante_id enviado se ignora/rechaza.
        messages.error(request, "Este producto no tiene opciones para elegir.")
        return redirect("catalogo:producto_detalle", slug=producto.slug)

    cantidad = _cantidad_valida(request.POST.get("cantidad", 1))
    if cantidad is None:
        messages.error(request, "La cantidad debe ser un número entero mayor o igual a 1.")
        return redirect("catalogo:producto_detalle", slug=producto.slug)

    Carrito(request).agregar(producto, variante, cantidad)
    messages.success(request, f'"{producto.nombre}" se agregó al carrito.')
    return redirect("pedidos:carrito")


@require_POST
def carrito_actualizar(request, clave):
    cantidad = _cantidad_valida(request.POST.get("cantidad"))
    if cantidad is None:
        messages.error(request, "La cantidad debe ser un número entero mayor o igual a 1.")
        return redirect("pedidos:carrito")
    Carrito(request).actualizar_cantidad(clave, cantidad)
    return redirect("pedidos:carrito")


@require_POST
def carrito_eliminar(request, clave):
    Carrito(request).eliminar(clave)
    return redirect("pedidos:carrito")


@require_POST
def carrito_vaciar(request):
    Carrito(request).vaciar()
    return redirect("pedidos:carrito")


def checkout(request):
    carrito = Carrito(request)
    lineas = carrito.items()

    if not lineas:
        messages.warning(request, "Tu carrito está vacío.")
        return redirect("pedidos:carrito")

    if carrito.hay_no_disponibles():
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
                messages.warning(request, "Tu carrito está vacío.")
                return redirect("pedidos:carrito")
            if carrito.hay_no_disponibles():
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
                    ItemPedido.objects.create(
                        pedido=pedido,
                        producto=linea.producto,
                        variante=linea.variante,
                        nombre_producto=linea.producto.nombre,
                        nombre_variante=linea.variante.nombre if linea.variante else "",
                        cantidad=linea.cantidad,
                        precio_unitario=linea.precio_unitario,
                    )

            carrito.vaciar()
            request.session[SESSION_KEY_ULTIMO_PEDIDO] = pedido.pk
            messages.success(request, "¡Tu pedido fue confirmado!")
            return redirect("pedidos:pedido_detalle", pk=pedido.pk)
    else:
        perfil = getattr(usuario, "perfil", None) if usuario else None
        initial = {
            "nombre": usuario.first_name if usuario else "",
            "apellido": usuario.last_name if usuario else "",
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
