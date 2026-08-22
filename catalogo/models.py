from django.db import models


class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    descripcion = models.TextField(blank=True)
    orden = models.PositiveIntegerField(default=0)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "categoría"
        verbose_name_plural = "categorías"
        ordering = ["orden", "nombre"]

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    class UnidadVenta(models.TextChoices):
        UNIDAD = "unidad", "Unidad"
        DOCENA = "docena", "Docena"
        PORCION = "porcion", "Porción"
        OTRO = "otro", "Otro"

    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name="productos",
    )
    nombre = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    descripcion = models.TextField(blank=True)
    descripcion_corta = models.CharField(max_length=255, blank=True)
    imagen = models.ImageField(upload_to="productos/", blank=True, null=True)
    # Solo se usa cuando el producto NO tiene variantes; si tiene variantes,
    # el precio real lo determina cada VarianteProducto. Esta regla se
    # valida en los formularios/servicios del panel y del checkout, no acá.
    precio = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    unidad_venta = models.CharField(max_length=10, choices=UnidadVenta.choices)
    disponible = models.BooleanField(default=True)
    destacado = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "producto"
        verbose_name_plural = "productos"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre

    @property
    def tiene_variantes(self):
        # Una variante desactivada no cuenta: un producto solo "usa variantes"
        # si tiene al menos una activa (ver validación en panel.forms).
        return self.variantes.filter(activo=True).exists()

    @property
    def variante_mas_barata(self):
        return self.variantes.filter(activo=True).order_by("precio").first()


class VarianteProducto(models.Model):
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name="variantes",
    )
    nombre = models.CharField(max_length=100)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    orden = models.PositiveIntegerField(default=0)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "variante de producto"
        verbose_name_plural = "variantes de producto"
        ordering = ["orden", "nombre"]
        constraints = [
            models.UniqueConstraint(fields=["producto", "nombre"], name="variante_unica_por_producto"),
        ]

    def __str__(self):
        return f"{self.producto} - {self.nombre}"
