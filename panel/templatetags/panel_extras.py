import os

from django import template
from django.conf import settings
from django.templatetags.static import static

register = template.Library()


@register.simple_tag
def static_v(path):
    """Igual que {% static %}, pero agrega "?v=<mtime del archivo>" al final.

    Solo se usa en templates del panel (base_panel.html, login.html) para
    panel.css/panel.js: sin esto, un navegador que ya visitó el panel antes
    de un cambio en esos archivos puede seguir usando su copia vieja en
    caché indefinidamente (el dev server no manda cache-busting fuerte), lo
    que renderiza el HTML nuevo con CSS/JS viejo — exactamente el bug de
    header/nav duplicado en mobile que este tag evita: al cambiar el
    archivo, cambia el mtime, cambia la URL, y el navegador lo trata como
    un recurso distinto en vez de reusar el caché."""
    url = static(path)
    try:
        ruta_absoluta = os.path.join(settings.BASE_DIR, "static", path)
        version = int(os.path.getmtime(ruta_absoluta))
    except OSError:
        version = 0
    return f"{url}?v={version}"
