from .models import Combo


def navbar_combos(request):
    """Expone si hay al menos un combo activo, para que la navbar pública
    (base_catalogo.html) pueda mostrar/ocultar el link "Combos" en
    cualquier página del sitio, no solo en el home."""
    return {"hay_combos_activos": Combo.objects.filter(activo=True).exists()}
