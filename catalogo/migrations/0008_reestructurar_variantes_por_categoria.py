"""Adapta los datos existentes al nuevo esquema de variantes por categoría:

- Empanadas: reemplaza las variantes "Cocinadas"/"Congeladas" (un solo
  precio por docena) por 6 combinaciones cantidad x modalidad (Unidad,
  Media docena, Docena) x (Cocinadas, Congeladas). Los precios de
  Unidad/Media docena se ESTIMAN proporcionalmente a partir del precio
  actual por docena (docena/12 y docena/2, redondeado a la centena): son
  un punto de partida, no un precio definitivo, hay que revisarlos en el
  panel.
- Alfajores: se crea como categoría propia (antes era un producto dentro
  de "Tartas"). Se le agregan variantes Media docena / Docena, estimadas
  a partir del precio unitario actual ($/u x 6 y x 12).
- Tartas: a cada tarta existente (precio único) se le agregan 3 variantes
  de tamaño (Pequeña/Mediana/Grande), estimadas como 0.7x/1x/1.3x del
  precio actual.

Ninguna de estas cifras es definitiva: son valores de partida derivados
de los datos reales para no dejar precios en $0, pensados para que el
administrador los ajuste desde el panel.
"""
from django.db import migrations


def _redondear_100(valor):
    return max(round(float(valor) / 100) * 100, 100)


def _redondear_500(valor):
    return max(round(float(valor) / 500) * 500, 500)


def migrar_datos(apps, schema_editor):
    Categoria = apps.get_model("catalogo", "Categoria")
    Producto = apps.get_model("catalogo", "Producto")
    VarianteProducto = apps.get_model("catalogo", "VarianteProducto")

    # --- Empanadas: Cocinadas/Congeladas -> Unidad/Media docena/Docena x modalidad ---
    try:
        categoria_empanadas = Categoria.objects.get(slug="empanadas")
    except Categoria.DoesNotExist:
        categoria_empanadas = None

    if categoria_empanadas is not None:
        for producto in Producto.objects.filter(categoria=categoria_empanadas):
            variantes_actuales = {v.nombre: v.precio for v in producto.variantes.all()}
            docena_cocinada = variantes_actuales.get("Cocinadas")
            docena_congelada = variantes_actuales.get("Congeladas")
            producto.variantes.all().delete()

            orden = 0
            for cantidad_nombre, divisor in (("Unidad", 12), ("Media docena", 2), ("Docena", 1)):
                for modalidad, precio_docena in (
                    ("cocinada", docena_cocinada),
                    ("congelada", docena_congelada),
                ):
                    if precio_docena is None:
                        continue
                    precio = _redondear_100(float(precio_docena) / divisor)
                    VarianteProducto.objects.create(
                        producto=producto,
                        nombre=cantidad_nombre,
                        modalidad=modalidad,
                        precio=precio,
                        orden=orden,
                        activo=True,
                    )
                    orden += 1
            producto.precio = None
            producto.save(update_fields=["precio"])

    # --- Alfajores: crear categoría propia y mover el producto ---
    try:
        categoria_tartas = Categoria.objects.get(slug="dulces")
    except Categoria.DoesNotExist:
        categoria_tartas = None

    if categoria_tartas is not None:
        producto_alfajores = Producto.objects.filter(
            categoria=categoria_tartas, slug="alfajores-de-maicena"
        ).first()
        if producto_alfajores is not None:
            categoria_alfajores, _ = Categoria.objects.get_or_create(
                slug="alfajores",
                defaults={"nombre": "Alfajores", "orden": 4, "activo": True},
            )
            precio_unidad = producto_alfajores.precio
            producto_alfajores.categoria = categoria_alfajores
            producto_alfajores.precio = None
            producto_alfajores.save(update_fields=["categoria", "precio"])
            producto_alfajores.variantes.all().delete()
            if precio_unidad is not None:
                VarianteProducto.objects.create(
                    producto=producto_alfajores, nombre="Media docena", modalidad="",
                    precio=_redondear_100(float(precio_unidad) * 6), orden=0, activo=True,
                )
                VarianteProducto.objects.create(
                    producto=producto_alfajores, nombre="Docena", modalidad="",
                    precio=_redondear_100(float(precio_unidad) * 12), orden=1, activo=True,
                )

        # --- Tartas restantes: agregar variantes de tamaño ---
        for producto in Producto.objects.filter(categoria=categoria_tartas):
            if producto.variantes.exists() or producto.precio is None:
                continue
            base = float(producto.precio)
            VarianteProducto.objects.create(
                producto=producto, nombre="Pequeña", modalidad="",
                precio=_redondear_500(base * 0.7), orden=0, activo=True,
            )
            VarianteProducto.objects.create(
                producto=producto, nombre="Mediana", modalidad="",
                precio=_redondear_500(base), orden=1, activo=True,
            )
            VarianteProducto.objects.create(
                producto=producto, nombre="Grande", modalidad="",
                precio=_redondear_500(base * 1.3), orden=2, activo=True,
            )
            producto.precio = None
            producto.save(update_fields=["precio"])


def revertir_datos(apps, schema_editor):
    # No se intenta reconstruir el estado anterior exacto (los precios
    # nuevos son estimaciones); revertir solo deja las variantes nuevas
    # en pie, lo cual es seguro (no rompe integridad referencial).
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("catalogo", "0007_combo_comboitem_alter_varianteproducto_options_and_more"),
    ]

    operations = [
        migrations.RunPython(migrar_datos, revertir_datos),
    ]
