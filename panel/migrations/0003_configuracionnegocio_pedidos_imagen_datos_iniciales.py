from django.db import migrations

NOMBRE_ARCHIVO = "productos/categoria-pedidos.png"


def cargar_imagen_inicial(apps, schema_editor):
    ConfiguracionNegocio = apps.get_model("panel", "ConfiguracionNegocio")
    ConfiguracionNegocio.objects.filter(pk=1).update(pedidos_imagen=NOMBRE_ARCHIVO)


def revertir_imagen_inicial(apps, schema_editor):
    ConfiguracionNegocio = apps.get_model("panel", "ConfiguracionNegocio")
    ConfiguracionNegocio.objects.filter(pk=1).update(pedidos_imagen=None)


class Migration(migrations.Migration):

    dependencies = [
        ("panel", "0002_configuracionnegocio_pedidos_imagen_and_more"),
    ]

    operations = [
        migrations.RunPython(cargar_imagen_inicial, revertir_imagen_inicial),
    ]
