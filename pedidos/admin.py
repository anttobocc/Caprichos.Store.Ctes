from django.contrib import admin

from .models import ItemPedido, Pedido


class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 0
    fields = ["producto", "variante", "nombre_producto", "nombre_variante", "cantidad", "precio_unitario", "subtotal"]
    readonly_fields = ["subtotal"]
    autocomplete_fields = ["producto"]


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "nombre",
        "apellido",
        "telefono",
        "tipo_entrega",
        "estado",
        "total",
        "fecha_pedido",
        "fecha_creacion",
    ]
    list_filter = ["estado", "tipo_entrega", "fecha_pedido"]
    search_fields = ["nombre", "apellido", "telefono"]
    list_editable = ["estado"]
    date_hierarchy = "fecha_pedido"
    inlines = [ItemPedidoInline]
    fieldsets = (
        (None, {"fields": ("usuario", "nombre", "apellido", "telefono")}),
        ("Entrega", {"fields": ("tipo_entrega", "direccion_envio", "fecha_pedido", "observaciones")}),
        ("Estado y total", {"fields": ("estado", "total")}),
    )
