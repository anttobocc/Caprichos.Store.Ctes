from django.contrib import admin
from django.shortcuts import redirect
from django.urls import reverse

from .models import ConfiguracionNegocio


@admin.register(ConfiguracionNegocio)
class ConfiguracionNegocioAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {"fields": ("nombre_negocio", "eslogan", "direccion", "instagram")}),
        ("WhatsApp y pedidos", {"fields": ("whatsapp_numero", "dias_anticipacion_pedido")}),
        ("Envíos (preparado para uso futuro)", {"fields": ("envio_habilitado", "costo_envio", "envio_gratis_desde")}),
        (
            "Imagen de pedidos en portada",
            {
                "fields": ("pedidos_imagen", "pedidos_imagen_pos_x", "pedidos_imagen_pos_y", "pedidos_imagen_tamano"),
                "description": (
                    "Usá estos valores para ajustar manualmente la posición de la imagen dentro "
                    "de la tarjeta 'Pedidos' de la portada."
                ),
            },
        ),
    )

    def has_add_permission(self, request):
        # Solo puede existir una fila (pk=1); si ya existe, no se permite crear otra.
        return not ConfiguracionNegocio.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        # Nunca mostrar el listado: ir directo a editar la única configuración.
        config = ConfiguracionNegocio.get_solo()
        url = reverse("admin:panel_configuracionnegocio_change", args=[config.pk])
        return redirect(url)
