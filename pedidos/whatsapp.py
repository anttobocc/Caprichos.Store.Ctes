"""Genera el mensaje de WhatsApp para un pedido ya confirmado.

El pedido NO se procesa como pago online: el cliente arma su pedido, lo
confirma en el sitio y el sistema le arma un mensaje con el detalle
completo para que lo envíe por WhatsApp al negocio. El número siempre se
lee de ConfiguracionNegocio.get_solo() (única fuente de verdad, ya definida
desde la Etapa 2), nunca hardcodeado.
"""
from urllib.parse import quote

from panel.models import ConfiguracionNegocio


def construir_mensaje(pedido):
    lineas = [
        "Hola! Quiero confirmar el siguiente pedido en Capricho:",
        "",
        f"Pedido #{pedido.pk}",
        f"Nombre: {pedido.nombre} {pedido.apellido}",
        f"Fecha del pedido: {pedido.fecha_pedido.strftime('%d/%m/%Y')}",
        f"Entrega: {pedido.get_tipo_entrega_display()}",
    ]
    if pedido.direccion_envio:
        lineas.append(f"Dirección: {pedido.direccion_envio}")
    lineas.append("")
    lineas.append("Productos:")
    for item in pedido.items.all():
        nombre = item.nombre_producto
        if item.nombre_variante:
            nombre += f" ({item.nombre_variante})"
        lineas.append(f"- {item.cantidad} x {nombre} — ${item.precio_unitario} c/u")
    lineas.append("")
    lineas.append(f"Total: ${pedido.total}")
    if pedido.observaciones:
        lineas.append("")
        lineas.append(f"Observaciones: {pedido.observaciones}")
    return "\n".join(lineas)


def construir_url(pedido):
    config = ConfiguracionNegocio.get_solo()
    numero = config.whatsapp_numero.lstrip("+")
    return f"https://wa.me/{numero}?text={quote(construir_mensaje(pedido))}"
