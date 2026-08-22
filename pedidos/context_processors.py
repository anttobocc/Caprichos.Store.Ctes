from .carrito import SESSION_KEY


def carrito_cantidad(request):
    """Cantidad total de unidades en el carrito, para mostrar en la nav
    ("Carrito (N)") sin tener que resolver cada producto/variante contra la
    base en cada request de cualquier página."""
    datos = request.session.get(SESSION_KEY, {})
    return {"carrito_cantidad": sum(datos.values())}
