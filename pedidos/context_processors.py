from .carrito import SESSION_KEY, Carrito
from .forms import CheckoutForm


def carrito_cantidad(request):
    """Cantidad total de unidades en el carrito, para mostrar en la nav
    ("Carrito (N)") sin tener que resolver cada producto/variante contra la
    base en cada request de cualquier página."""
    datos = request.session.get(SESSION_KEY, {})
    return {"carrito_cantidad": sum(datos.values())}


def carrito_resumen(request):
    """Contenido resuelto del carrito (líneas + total) más el formulario de
    checkout (sin bind), para poder pintar el panel lateral del carrito
    -incluyendo los datos del cliente para finalizar el pedido- en
    cualquier página sin depender de un fetch previo. Usado únicamente por
    el drawer (ver pedidos/_carrito_drawer.html); no reemplaza a
    carrito_cantidad."""
    carrito = Carrito(request)
    lineas = carrito.items()

    initial = {}
    if request.user.is_authenticated:
        perfil = getattr(request.user, "perfil", None)
        initial = {
            "nombre_completo": f"{request.user.first_name} {request.user.last_name}".strip(),
            "telefono": perfil.telefono if perfil else "",
        }
    checkout_form = CheckoutForm(initial=initial)

    return {
        "carrito_lineas": lineas,
        "carrito_total": carrito.total(),
        "carrito_hay_no_disponibles": carrito.hay_no_disponibles(),
        "carrito_checkout_form": checkout_form,
    }
