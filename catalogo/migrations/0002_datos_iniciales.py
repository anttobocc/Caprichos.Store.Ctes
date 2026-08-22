from django.db import migrations

CATEGORIAS = [
    {"nombre": "Dulces", "slug": "dulces", "orden": 1},
    {"nombre": "Budines", "slug": "budines", "orden": 2},
    {"nombre": "Empanadas", "slug": "empanadas", "orden": 3},
]

# (categoria_slug, nombre, slug, unidad_venta, precio, descripcion_corta, variantes)
PRODUCTOS = [
    ("dulces", "Alfajores de maicena", "alfajores-de-maicena", "docena", 5000, "", []),
    ("dulces", "Tarta de frutilla", "tarta-de-frutilla", "unidad", 35000, "27 cm", []),
    ("dulces", "Tarta de durazno", "tarta-de-durazno", "unidad", 25000, "27 cm", []),
    ("dulces", "Tarta de coco", "tarta-de-coco", "unidad", 25000, "27 cm", []),
    ("budines", "Marmolado", "budin-marmolado", "unidad", 5000, "", []),
    ("budines", "Chocolate", "budin-chocolate", "unidad", 5000, "", []),
    ("budines", "Vainilla", "budin-vainilla", "unidad", 5000, "", []),
    ("budines", "Vainilla con chips", "budin-vainilla-con-chips", "unidad", 6000, "", []),
    (
        "empanadas",
        "Empanadas de carne molida",
        "empanadas-de-carne-molida",
        "docena",
        None,
        "",
        [("Cocinadas", 19500), ("Congeladas", 18000)],
    ),
    (
        "empanadas",
        "Empanadas de jamón y queso",
        "empanadas-de-jamon-y-queso",
        "docena",
        None,
        "",
        [("Cocinadas", 16000), ("Congeladas", 14500)],
    ),
    (
        "empanadas",
        "Empanadas de pollo",
        "empanadas-de-pollo",
        "docena",
        None,
        "",
        [("Cocinadas", 16000), ("Congeladas", 14500)],
    ),
    (
        "empanadas",
        "Empanadas de pizza de muzzarella",
        "empanadas-de-pizza-de-muzzarella",
        "docena",
        None,
        "",
        [("Cocinadas", 10000), ("Congeladas", 9000)],
    ),
]


def cargar_datos_iniciales(apps, schema_editor):
    Categoria = apps.get_model("catalogo", "Categoria")
    Producto = apps.get_model("catalogo", "Producto")
    VarianteProducto = apps.get_model("catalogo", "VarianteProducto")

    categorias_por_slug = {}
    for datos in CATEGORIAS:
        categoria, _ = Categoria.objects.get_or_create(
            slug=datos["slug"],
            defaults={"nombre": datos["nombre"], "orden": datos["orden"]},
        )
        categorias_por_slug[datos["slug"]] = categoria

    for categoria_slug, nombre, slug, unidad_venta, precio, descripcion_corta, variantes in PRODUCTOS:
        producto, _ = Producto.objects.get_or_create(
            slug=slug,
            defaults={
                "categoria": categorias_por_slug[categoria_slug],
                "nombre": nombre,
                "unidad_venta": unidad_venta,
                "precio": precio,
                "descripcion_corta": descripcion_corta,
            },
        )
        for orden, (nombre_variante, precio_variante) in enumerate(variantes):
            VarianteProducto.objects.get_or_create(
                producto=producto,
                nombre=nombre_variante,
                defaults={"precio": precio_variante, "orden": orden},
            )


def eliminar_datos_iniciales(apps, schema_editor):
    Categoria = apps.get_model("catalogo", "Categoria")
    Producto = apps.get_model("catalogo", "Producto")
    Producto.objects.filter(slug__in=[p[2] for p in PRODUCTOS]).delete()
    Categoria.objects.filter(slug__in=[c["slug"] for c in CATEGORIAS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("catalogo", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(cargar_datos_iniciales, eliminar_datos_iniciales),
    ]
