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
    fieldsets = (
        (None, {"fields": ("nombre", "slug", "descripcion", "orden", "activo")}),
        (
            "Imagen en la portada (desktop)",
            {
                "fields": ("imagen_categoria", "imagen_pos_x", "imagen_pos_y", "imagen_tamano"),
                "description": (
                    "Usá estos valores para ajustar manualmente la posición de la imagen dentro "
                    "de la tarjeta de esta categoría en la portada de escritorio. No reemplazan "
                    "el diseño base de la tarjeta, solo lo desplazan/escalan."
                ),
            },
        ),
        (
            "Imagen en la portada (mobile)",
            {
                "fields": ("imagen_mobile_pos_x", "imagen_mobile_pos_y", "imagen_mobile_tamano"),
                "description": (
                    "Posición/escala independientes de las de desktop, para la misma imagen "
                    "dentro de la tarjeta de esta categoría en la portada mobile (grilla 2×2). "
                    "Editable también con el selector Desktop/Mobile del editor visual del panel."
                ),
            },
        ),
    )


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
