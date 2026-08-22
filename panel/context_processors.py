from .models import ConfiguracionNegocio


def configuracion_negocio(request):
    """Expone la configuración del negocio (WhatsApp, dirección, envíos,
    anticipación) a todos los templates públicos, para no hardcodear estos
    datos en el header/footer."""
    config = ConfiguracionNegocio.get_solo()
    return {
        "configuracion_negocio": config,
        "whatsapp_link_general": f"https://wa.me/{config.whatsapp_numero.lstrip('+')}",
    }
