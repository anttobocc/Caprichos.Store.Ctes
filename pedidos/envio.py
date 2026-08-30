from decimal import Decimal

from .models import Pedido


def costo_envio(config, tipo_entrega, subtotal):
    """Servidor calcula el costo de envío, nunca se confía en el frontend.
    Compartido entre views.py (cálculo real al confirmar) y
    context_processors.py (estimación mostrada en el drawer antes de
    confirmar), para no duplicar esta regla en dos lugares."""
    if tipo_entrega != Pedido.TipoEntrega.ENVIO:
        return Decimal("0")
    if not config.envio_habilitado:
        return Decimal("0")
    if config.envio_gratis_desde is not None and subtotal >= config.envio_gratis_desde:
        return Decimal("0")
    return config.costo_envio or Decimal("0")
