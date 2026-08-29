from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    descripcion = models.TextField(blank=True)
    orden = models.PositiveIntegerField(default=0)
    activo = models.BooleanField(default=True)
    mostrar_en_productos = models.BooleanField(
        default=True,
        verbose_name="mostrar en productos",
        help_text="Si está desactivado, la categoría no aparece en la sección Productos ni en sus filtros.",
    )
    mostrar_en_inicio = models.BooleanField(
        default=True,
        verbose_name="mostrar en inicio",
        help_text="Si está desactivado, la categoría no aparece en la sección de categorías del Inicio.",
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    imagen_categoria = models.ImageField(
        verbose_name="imagen de portada",
        upload_to="categorias/",
        blank=True,
        null=True,
        help_text="Imagen mostrada en la tarjeta de esta categoría en la página de inicio.",
    )
    imagen_pos_x = models.PositiveSmallIntegerField(
        verbose_name="posición horizontal (X)",
        default=50,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Posición horizontal en % (0 = izquierda, 50 = centro, 100 = derecha).",
    )
    imagen_pos_y = models.PositiveSmallIntegerField(
        verbose_name="posición vertical (Y)",
        default=50,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Posición vertical en % (0 = arriba, 50 = centro, 100 = abajo).",
    )
    imagen_tamano = models.PositiveIntegerField(
        verbose_name="tamaño",
        default=260,
        validators=[MinValueValidator(50), MaxValueValidator(5000)],
        help_text="Alto de la imagen en px (el ancho se ajusta proporcionalmente).",
    )
    # Ajuste independiente del de arriba: la tarjeta de categoría en mobile
    # (.m-card, ver catalogo/home.html y catalogo.css) es un diseño propio,
    # no una versión reducida de la tarjeta desktop, así que necesita su
    # propia posición/escala de imagen en vez de heredar imagen_pos_x/y/
    # imagen_tamano. A diferencia de los campos de arriba (0-100, recorte
    # dentro de una caja fija), acá la imagen es una capa libre sobre TODA
    # la tarjeta (.m-card, no .m-card__imagen): X/Y pueden salir de 0-100
    # (con SmallIntegerField, no Positive) para poder arrastrarla bien
    # afuera de la tarjeta hacia cualquier lado, y el tamaño no tiene techo
    # atado al recuadro. Mismo prefijo "imagen_mobile" para que
    # panel/views.py::preview_guardar_imagen los siga tratando con la
    # misma lógica genérica (modo "flotante-movil").
    imagen_mobile_pos_x = models.SmallIntegerField(
        verbose_name="posición horizontal mobile (X)",
        default=50,
        validators=[MinValueValidator(-100), MaxValueValidator(200)],
        help_text="Posición horizontal en % relativo a toda la tarjeta mobile (50 = centro; puede salir de 0-100 para mover la imagen bien hacia los costados).",
    )
    imagen_mobile_pos_y = models.SmallIntegerField(
        verbose_name="posición vertical mobile (Y)",
        default=50,
        validators=[MinValueValidator(-100), MaxValueValidator(200)],
        help_text="Posición vertical en % relativo a toda la tarjeta mobile (50 = centro; puede salir de 0-100 para mover la imagen bien hacia arriba/abajo).",
    )
    imagen_mobile_tamano = models.PositiveSmallIntegerField(
        verbose_name="tamaño mobile",
        default=100,
        validators=[MinValueValidator(20), MaxValueValidator(400)],
        help_text="Escala de la imagen dentro de la tarjeta mobile, en % (100 = tamaño base, sin recortar).",
    )

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
        on_delete=models.CASCADE,
        related_name="productos",
    )
    nombre = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    descripcion = models.TextField(blank=True)
    descripcion_corta = models.CharField(max_length=255, blank=True)
    imagen = models.ImageField(upload_to="productos/", blank=True, null=True)
    imagen_pos_x = models.PositiveSmallIntegerField(
        verbose_name="posición horizontal (X)",
        default=50,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Posición horizontal en % (0 = izquierda, 50 = centro, 100 = derecha).",
    )
    imagen_pos_y = models.PositiveSmallIntegerField(
        verbose_name="posición vertical (Y)",
        default=50,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Posición vertical en % (0 = arriba, 50 = centro, 100 = abajo).",
    )
    imagen_zoom = models.PositiveSmallIntegerField(
        verbose_name="zoom",
        default=100,
        validators=[MinValueValidator(100), MaxValueValidator(200)],
        help_text="Escala de la imagen dentro de su recuadro, en % (100 = ajuste normal).",
    )
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

    @property
    def tiene_modalidad(self):
        # True para productos con eje "cantidad x modalidad" (hoy: Empanadas).
        return self.variantes.filter(activo=True).exclude(modalidad="").exists()


class VarianteProducto(models.Model):
    class Modalidad(models.TextChoices):
        COCINADA = "cocinada", "Cocinadas"
        CONGELADA = "congelada", "Congeladas"

    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name="variantes",
    )
    # Representa la cantidad/presentación (Unidad, Media docena, Docena,
    # Pequeña/Mediana/Grande, etc.). Para productos con dos ejes de compra
    # (hoy: Empanadas) se combina con "modalidad" para formar cada
    # combinación cantidad+modalidad como una fila propia, sin que eso
    # implique variantes visibles como productos independientes: la interfaz
    # pública sigue mostrando dos selectores (cantidad y modalidad).
    nombre = models.CharField(max_length=100)
    modalidad = models.CharField(
        max_length=10,
        choices=Modalidad.choices,
        blank=True,
        help_text="Solo se usa en productos con dos formas de compra (ej. Empanadas: cocinadas/congeladas).",
    )
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    orden = models.PositiveIntegerField(default=0)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "variante de producto"
        verbose_name_plural = "variantes de producto"
        ordering = ["orden", "modalidad", "nombre"]
        constraints = [
            models.UniqueConstraint(fields=["producto", "nombre", "modalidad"], name="variante_unica_por_producto"),
        ]

    def __str__(self):
        return f"{self.producto} - {self.nombre_completo}"

    @property
    def nombre_completo(self):
        if self.modalidad:
            return f"{self.nombre} — {self.get_modalidad_display()}"
        return self.nombre


class Combo(models.Model):
    nombre = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    descripcion = models.TextField(blank=True)
    imagen = models.ImageField(upload_to="combos/", blank=True, null=True)
    imagen_pos_x = models.PositiveSmallIntegerField(
        verbose_name="posición horizontal (X)",
        default=50,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Posición horizontal en % (0 = izquierda, 50 = centro, 100 = derecha).",
    )
    imagen_pos_y = models.PositiveSmallIntegerField(
        verbose_name="posición vertical (Y)",
        default=50,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Posición vertical en % (0 = arriba, 50 = centro, 100 = abajo).",
    )
    imagen_zoom = models.PositiveSmallIntegerField(
        verbose_name="zoom",
        default=100,
        validators=[MinValueValidator(100), MaxValueValidator(200)],
        help_text="Escala de la imagen dentro de su recuadro, en % (100 = ajuste normal).",
    )
    precio_promocional = models.DecimalField(max_digits=10, decimal_places=2)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "combo"
        verbose_name_plural = "combos"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre

    @property
    def precio_individual_total(self):
        total = None
        for item in self.items.select_related("producto"):
            precio_item = item.producto.precio
            if precio_item is None:
                variante = item.producto.variante_mas_barata
                precio_item = variante.precio if variante else None
            if precio_item is None:
                continue
            aporte = precio_item * item.cantidad
            total = aporte if total is None else total + aporte
        return total


class ComboItem(models.Model):
    combo = models.ForeignKey(Combo, on_delete=models.CASCADE, related_name="items")
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name="combos")
    cantidad = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = "producto del combo"
        verbose_name_plural = "productos del combo"
        constraints = [
            models.UniqueConstraint(fields=["combo", "producto"], name="producto_unico_por_combo"),
        ]

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre} ({self.combo.nombre})"
