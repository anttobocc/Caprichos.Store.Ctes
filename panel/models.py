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
    pedidos_imagen_pos_x = models.PositiveSmallIntegerField(
        verbose_name="posición horizontal (X)",
        default=50,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Posición horizontal en % (0 = izquierda, 50 = centro, 100 = derecha).",
    )
    pedidos_imagen_pos_y = models.PositiveSmallIntegerField(
        verbose_name="posición vertical (Y)",
        default=50,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Posición vertical en % (0 = arriba, 50 = centro, 100 = abajo).",
    )
    pedidos_imagen_tamano = models.PositiveIntegerField(
        verbose_name="tamaño",
        default=260,
        validators=[MinValueValidator(50), MaxValueValidator(5000)],
        help_text="Alto de la imagen en px (el ancho se ajusta proporcionalmente).",
    )
    # Igual que Categoria.imagen_mobile_*: ajuste independiente para la
    # tarjeta "Pedidos" del grid mobile (.m-card--cta), que es un diseño
    # propio y no una copia reducida de la tarjeta desktop. La imagen es
    # una capa libre sobre TODA la tarjeta, por eso X/Y admiten valores
    # fuera de 0-100 (SmallIntegerField, no Positive) y el tamaño no tiene
    # techo atado a ningún recuadro fijo.
    pedidos_imagen_mobile_pos_x = models.SmallIntegerField(
        verbose_name="posición horizontal mobile (X)",
        default=50,
        validators=[MinValueValidator(-100), MaxValueValidator(200)],
        help_text="Posición horizontal en % relativo a toda la tarjeta mobile (50 = centro; puede salir de 0-100 para mover la imagen bien hacia los costados).",
    )
    pedidos_imagen_mobile_pos_y = models.SmallIntegerField(
        verbose_name="posición vertical mobile (Y)",
        default=50,
        validators=[MinValueValidator(-100), MaxValueValidator(200)],
        help_text="Posición vertical en % relativo a toda la tarjeta mobile (50 = centro; puede salir de 0-100 para mover la imagen bien hacia arriba/abajo).",
    )
    pedidos_imagen_mobile_tamano = models.PositiveSmallIntegerField(
        verbose_name="tamaño mobile",
        default=100,
        validators=[MinValueValidator(20), MaxValueValidator(400)],
        help_text="Escala de la imagen dentro de la tarjeta mobile, en % (100 = tamaño base, sin recortar).",
    )
    portada_imagen = models.ImageField(
        verbose_name="imagen principal de la portada",
        upload_to="productos/",
        blank=True,
        null=True,
        help_text="Foto principal del hero en la página de inicio. Si no se sube ninguna, se usa la imagen por defecto del sitio.",
    )
    portada_imagen_pos_x = models.PositiveSmallIntegerField(
        verbose_name="posición horizontal (X)",
        default=50,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Posición horizontal en % (0 = izquierda, 50 = centro, 100 = derecha).",
    )
    portada_imagen_pos_y = models.PositiveSmallIntegerField(
        verbose_name="posición vertical (Y)",
        default=32,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Posición vertical en % (0 = arriba, 50 = centro, 100 = abajo).",
    )
    portada_imagen_zoom = models.PositiveSmallIntegerField(
        verbose_name="zoom",
        default=100,
        validators=[MinValueValidator(100), MaxValueValidator(200)],
        help_text="Escala de la imagen dentro de su recuadro, en % (100 = ajuste normal).",
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
