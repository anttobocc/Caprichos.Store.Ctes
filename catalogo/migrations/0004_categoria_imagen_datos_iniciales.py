from django.db import migrations

# (slug, nombre_de_archivo_relativo_a_MEDIA_ROOT, alto_actual_en_px)
IMAGENES_POR_SLUG = {
    "empanadas": ("productos/categoria-empanadas.png", 260),
    "budines": ("productos/categoria-budines.png", 260),
    "dulces": ("productos/categoria-tartas.png", 290),
}


def cargar_imagenes_iniciales(apps, schema_editor):
    Categoria = apps.get_model("catalogo", "Categoria")
    for slug, (nombre_archivo, alto) in IMAGENES_POR_SLUG.items():
        Categoria.objects.filter(slug=slug).update(imagen_categoria=nombre_archivo, imagen_tamano=alto)


def revertir_imagenes_iniciales(apps, schema_editor):
    Categoria = apps.get_model("catalogo", "Categoria")
    Categoria.objects.filter(slug__in=IMAGENES_POR_SLUG.keys()).update(imagen_categoria=None, imagen_tamano=260)


class Migration(migrations.Migration):

    dependencies = [
        ("catalogo", "0003_categoria_imagen_categoria_categoria_imagen_pos_x_and_more"),
    ]

    operations = [
        migrations.RunPython(cargar_imagenes_iniciales, revertir_imagenes_iniciales),
    ]
