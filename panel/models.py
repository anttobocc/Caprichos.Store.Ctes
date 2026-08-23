from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models

whatsapp_validator = RegexValidator(
    regex=r"^\+?\d{8,15}$",
    message="Ingresá el número en formato internacional, solo dígitos y opcionalmente un '+' inicial.",
)


class ConfiguracionNegocio(models.Model):
    """Configuración única del negocio. Usar siempre ConfiguracionNegocio.get_solo()."""

    nombre_negocio = models.CharField(max_length=150, default="Capricho")
    eslogan = models.CharField(max_length=255, blank=True, default="Boutique Empanadas & Bakery")
    whatsapp_numero = models.CharField(max_length=30, validators=[whatsapp_validator])
    direccion = models.CharField(max_length=255, blank=True)
    instagram = models.URLField(blank=True)
    dias_anticipacion_pedido = models.PositiveIntegerField(
        default=getattr(settings, "MIN_ORDER_ADVANCE_DAYS", 1),
        help_text="Días mínimos de anticipación exigidos para un pedido. Única fuente de verdad de esta regla.",
    )
    envio_habilitado = models.BooleanField(default=True)
    # Preparados para una futura lógica de costos/zonas de envío; sin uso todavía.
    costo_envio = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    envio_gratis_desde = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    pedidos_imagen = models.ImageField(
        verbose_name="imagen de pedidos en portada",
        upload_to="categorias/",
        blank=True,
        null=True,
        help_text="Imagen de la tarjeta 'Pedidos' en la página de inicio.",
    )
    pedidos_imagen_pos_x = models.IntegerField(
        verbose_name="posición horizontal (X)",
        default=0,
        validators=[MinValueValidator(-1000), MaxValueValidator(1000)],
        help_text="Ajuste horizontal en px sobre la posición actual. Negativo = izquierda, positivo = derecha.",
    )
    pedidos_imagen_pos_y = models.IntegerField(
        verbose_name="posición vertical (Y)",
        default=0,
        validators=[MinValueValidator(-1000), MaxValueValidator(1000)],
        help_text="Ajuste vertical en px sobre la posición actual. Negativo = arriba, positivo = abajo.",
    )
    pedidos_imagen_tamano = models.PositiveIntegerField(
        verbose_name="tamaño",
        default=260,
        validators=[MinValueValidator(50), MaxValueValidator(600)],
        help_text="Alto de la imagen en px (el ancho se ajusta proporcionalmente).",
    )
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "configuración del negocio"
        verbose_name_plural = "configuración del negocio"

    def __str__(self):
        return self.nombre_negocio

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(
            pk=1,
            defaults={"whatsapp_numero": "5493790000000"},
        )
        return obj
