from django.contrib import admin

from .models import Categoria, Producto, VarianteProducto


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ["nombre", "orden", "activo", "fecha_creacion"]
    list_filter = ["activo"]
    search_fields = ["nombre"]
    list_editable = ["orden", "activo"]
    prepopulated_fields = {"slug": ("nombre",)}
    ordering = ["orden", "nombre"]


class VarianteProductoInline(admin.TabularInline):
    model = VarianteProducto
    extra = 1
    fields = ["nombre", "precio", "orden", "activo"]


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = [
        "nombre",
        "categoria",
        "precio",
        "unidad_venta",
        "disponible",
        "destacado",
        "activo",
    ]
    list_filter = ["categoria", "unidad_venta", "activo", "destacado", "disponible"]
    search_fields = ["nombre", "descripcion"]
    list_editable = ["disponible", "destacado", "activo"]
    list_select_related = ["categoria"]
    prepopulated_fields = {"slug": ("nombre",)}
    inlines = [VarianteProductoInline]
    fieldsets = (
        (None, {"fields": ("categoria", "nombre", "slug", "unidad_venta")}),
        ("Descripción e imagen", {"fields": ("descripcion_corta", "descripcion", "imagen")}),
        (
            "Precio y estado",
            {
                "fields": ("precio", "disponible", "destacado", "activo"),
                "description": (
                    "El precio solo se usa si el producto NO tiene variantes. "
                    "Si agregás variantes abajo, el precio de cada variante es el que se cobra."
                ),
            },
        ),
    )
