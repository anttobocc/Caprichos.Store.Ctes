from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from catalogo.models import Producto, VarianteProducto


class Pedido(models.Model):
    class TipoEntrega(models.TextChoices):
        RETIRO = "retiro", "Retiro en el local"
        ENVIO = "envio", "Envío"

    class Estado(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        CONFIRMADO = "confirmado", "Confirmado"
        EN_PREPARACION = "en_preparacion", "En preparación"
        LISTO = "listo", "Listo"
        ENTREGADO = "entregado", "Entregado"
        CANCELADO = "cancelado", "Cancelado"

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pedidos",
    )
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    telefono = models.CharField(max_length=30)
    tipo_entrega = models.CharField(max_length=10, choices=TipoEntrega.choices, default=TipoEntrega.RETIRO)
    # Obligatorio solo si tipo_entrega == ENVIO; se valida en el form/servicio de checkout.
    direccion_envio = models.CharField(max_length=255, blank=True)
    fecha_pedido = models.DateField(help_text="Fecha deseada de entrega/retiro.")
    observaciones = models.TextField(blank=True)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PENDIENTE)
    # Snapshot: se calcula una vez al confirmar el pedido y no se recalcula después.
    total = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "pedido"
        verbose_name_plural = "pedidos"
        ordering = ["-fecha_creacion"]

    def __str__(self):
        return f"Pedido #{self.pk} - {self.nombre} {self.apellido}"


class ItemPedido(models.Model):
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name="items",
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.SET_NULL,
        null=True,
        related_name="items_pedido",
    )
    variante = models.ForeignKey(
        VarianteProducto,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="items_pedido",
    )
    # Snapshots: conservan el detalle del pedido aunque el producto/variante se elimine, cambie o se desactive después.
    nombre_producto = models.CharField(max_length=200)
    nombre_variante = models.CharField(max_length=100, blank=True)
    cantidad = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "ítem de pedido"
        verbose_name_plural = "ítems de pedido"

    def __str__(self):
        return f"{self.cantidad} x {self.nombre_producto}"

    def save(self, *args, **kwargs):
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)
