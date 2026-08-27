from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.forms import inlineformset_factory
from django.utils.text import slugify

from catalogo.models import Categoria, Combo, ComboItem, Producto, VarianteProducto
from pedidos.models import Pedido
from usuarios.models import Perfil

from .models import ConfiguracionNegocio


class ImagenPortadaWidget(forms.ClearableFileInput):
    """ClearableFileInput con una plantilla propia (botón + nombre de
    archivo + "Eliminar imagen" en una fila), en vez del markup por
    defecto de Django ("Currently:"/"Change:"). Usado por la imagen de
    portada de categorías y por la imagen de la tarjeta "Pedidos"."""

    template_name = "panel/includes/_widget_imagen_portada.html"


def _slug_unico(model, nombre, slug_ingresado, instance_pk=None):
    """Genera un slug a partir de `nombre` si no se ingresó uno, agregando un
    sufijo numérico ante colisión (excluyendo el propio registro al editar)."""
    slug_base = slug_ingresado or slugify(nombre)
    slug = slug_base
    queryset = model.objects.all()
    if instance_pk:
        queryset = queryset.exclude(pk=instance_pk)
    contador = 2
    while queryset.filter(slug=slug).exists():
        slug = f"{slug_base}-{contador}"
        contador += 1
    return slug


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = [
            "nombre", "slug", "descripcion", "orden",
            "imagen_categoria", "imagen_pos_x", "imagen_pos_y", "imagen_tamano",
        ]
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 2}),
            "slug": forms.HiddenInput(),
            "imagen_categoria": ImagenPortadaWidget(),
            "imagen_pos_x": forms.NumberInput(attrs={"step": 1, "min": 0, "max": 100}),
            "imagen_pos_y": forms.NumberInput(attrs={"step": 1, "min": 0, "max": 100}),
            "imagen_tamano": forms.NumberInput(attrs={"step": 1, "min": 50, "max": 5000}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["slug"].required = False
        # Estos tres campos los completa/actualiza el editor visual de
        # imagen (arrastrar, botones −/+/↑/↓ y los campos numéricos) vía JS;
        # si llegan vacíos (por ejemplo un POST manual) se usa el default
        # del modelo en lugar de exigirlos en el formulario.
        self.fields["imagen_pos_x"].required = False
        self.fields["imagen_pos_y"].required = False
        self.fields["imagen_tamano"].required = False

    def clean(self):
        cleaned = super().clean()
        nombre = cleaned.get("nombre")
        if nombre:
            cleaned["slug"] = _slug_unico(Categoria, nombre, cleaned.get("slug"), self.instance.pk)
        if cleaned.get("imagen_pos_x") in (None, ""):
            cleaned["imagen_pos_x"] = 50
        if cleaned.get("imagen_pos_y") in (None, ""):
            cleaned["imagen_pos_y"] = 50
        if cleaned.get("imagen_tamano") in (None, ""):
            cleaned["imagen_tamano"] = 260
        return cleaned


class PedidosImagenForm(forms.ModelForm):
    """Imagen y posición/tamaño de la tarjeta "Pedidos" de la portada. No es
    una categoría (vive en ConfiguracionNegocio), pero se edita desde el
    mismo listado de Categorías del panel, con el mismo editor visual."""

    class Meta:
        model = ConfiguracionNegocio
        fields = [
            "pedidos_imagen", "pedidos_imagen_pos_x", "pedidos_imagen_pos_y", "pedidos_imagen_tamano",
        ]
        widgets = {
            "pedidos_imagen": ImagenPortadaWidget(),
            "pedidos_imagen_pos_x": forms.NumberInput(attrs={"step": 1, "min": 0, "max": 100}),
            "pedidos_imagen_pos_y": forms.NumberInput(attrs={"step": 1, "min": 0, "max": 100}),
            "pedidos_imagen_tamano": forms.NumberInput(attrs={"step": 1, "min": 50, "max": 5000}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["pedidos_imagen_pos_x"].required = False
        self.fields["pedidos_imagen_pos_y"].required = False
        self.fields["pedidos_imagen_tamano"].required = False

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("pedidos_imagen_pos_x") in (None, ""):
            cleaned["pedidos_imagen_pos_x"] = 50
        if cleaned.get("pedidos_imagen_pos_y") in (None, ""):
            cleaned["pedidos_imagen_pos_y"] = 50
        if cleaned.get("pedidos_imagen_tamano") in (None, ""):
            cleaned["pedidos_imagen_tamano"] = 260
        return cleaned


class PortadaImagenForm(forms.ModelForm):
    """Imagen principal del hero (portada) + su posición/zoom. Igual patrón
    que PedidosImagenForm, pero en modo "recorte" (object-position % + zoom),
    ya que la foto del hero es una imagen recortada dentro de una caja de
    aspect-ratio fijo, no una decoración flotante como categorías/pedidos."""

    class Meta:
        model = ConfiguracionNegocio
        fields = [
            "portada_imagen", "portada_imagen_pos_x", "portada_imagen_pos_y", "portada_imagen_zoom",
        ]
        widgets = {
            "portada_imagen": ImagenPortadaWidget(),
            "portada_imagen_pos_x": forms.NumberInput(attrs={"step": 1, "min": 0, "max": 100}),
            "portada_imagen_pos_y": forms.NumberInput(attrs={"step": 1, "min": 0, "max": 100}),
            "portada_imagen_zoom": forms.NumberInput(attrs={"step": 1, "min": 100, "max": 200}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["portada_imagen_pos_x"].required = False
        self.fields["portada_imagen_pos_y"].required = False
        self.fields["portada_imagen_zoom"].required = False

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("portada_imagen_pos_x") in (None, ""):
            cleaned["portada_imagen_pos_x"] = 50
        if cleaned.get("portada_imagen_pos_y") in (None, ""):
            cleaned["portada_imagen_pos_y"] = 32
        if cleaned.get("portada_imagen_zoom") in (None, ""):
            cleaned["portada_imagen_zoom"] = 100
        return cleaned


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = [
            "categoria",
            "nombre",
            "slug",
            "descripcion_corta",
            "descripcion",
            "imagen",
            "imagen_pos_x",
            "imagen_pos_y",
            "imagen_zoom",
            "precio",
            "unidad_venta",
            "destacado",
        ]
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 3}),
            "imagen": ImagenPortadaWidget(),
            "imagen_pos_x": forms.NumberInput(attrs={"step": 1, "min": 0, "max": 100}),
            "imagen_pos_y": forms.NumberInput(attrs={"step": 1, "min": 0, "max": 100}),
            "imagen_zoom": forms.NumberInput(attrs={"step": 1, "min": 100, "max": 200}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["slug"].required = False
        self.fields["precio"].required = False
        # Los completa/actualiza el editor visual de imagen (mismo mecanismo
        # que Categoria); si llegan vacíos se usa el default del modelo.
        self.fields["imagen_pos_x"].required = False
        self.fields["imagen_pos_y"].required = False
        self.fields["imagen_zoom"].required = False

    def clean(self):
        cleaned = super().clean()
        nombre = cleaned.get("nombre")
        if nombre:
            cleaned["slug"] = _slug_unico(Producto, nombre, cleaned.get("slug"), self.instance.pk)
        if cleaned.get("imagen_pos_x") in (None, ""):
            cleaned["imagen_pos_x"] = 50
        if cleaned.get("imagen_pos_y") in (None, ""):
            cleaned["imagen_pos_y"] = 50
        if cleaned.get("imagen_zoom") in (None, ""):
            cleaned["imagen_zoom"] = 100
        return cleaned


VarianteProductoFormSet = inlineformset_factory(
    Producto,
    VarianteProducto,
    fields=["nombre", "modalidad", "precio", "orden", "activo"],
    extra=1,
    can_delete=True,
)


class ComboForm(forms.ModelForm):
    class Meta:
        model = Combo
        fields = [
            "nombre", "slug", "descripcion", "imagen",
            "imagen_pos_x", "imagen_pos_y", "imagen_zoom", "precio_promocional",
        ]
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 3}),
            "imagen": ImagenPortadaWidget(),
            "imagen_pos_x": forms.NumberInput(attrs={"step": 1, "min": 0, "max": 100}),
            "imagen_pos_y": forms.NumberInput(attrs={"step": 1, "min": 0, "max": 100}),
            "imagen_zoom": forms.NumberInput(attrs={"step": 1, "min": 100, "max": 200}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["slug"].required = False
        self.fields["imagen_pos_x"].required = False
        self.fields["imagen_pos_y"].required = False
        self.fields["imagen_zoom"].required = False

    def clean(self):
        cleaned = super().clean()
        nombre = cleaned.get("nombre")
        if nombre:
            cleaned["slug"] = _slug_unico(Combo, nombre, cleaned.get("slug"), self.instance.pk)
        if cleaned.get("imagen_pos_x") in (None, ""):
            cleaned["imagen_pos_x"] = 50
        if cleaned.get("imagen_pos_y") in (None, ""):
            cleaned["imagen_pos_y"] = 50
        if cleaned.get("imagen_zoom") in (None, ""):
            cleaned["imagen_zoom"] = 100
        return cleaned


ComboItemFormSet = inlineformset_factory(
    Combo,
    ComboItem,
    fields=["producto", "cantidad"],
    extra=1,
    can_delete=True,
)


class UsuarioCrearForm(UserCreationForm):
    """Crea un usuario desde el panel. A diferencia del registro público,
    acá el administrador SÍ puede marcar "permisos administrativos"
    (is_staff) explícitamente."""

    is_staff = forms.BooleanField(required=False, label="Permisos administrativos")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ["username", "first_name", "last_name", "email"]

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.is_staff = self.cleaned_data["is_staff"]
        usuario.is_active = True
        if commit:
            usuario.save()
        return usuario


class UsuarioEditarForm(forms.ModelForm):
    """Edita un usuario existente. Nunca incluye password (eso va por
    SetPasswordForm en una vista aparte)."""

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "is_staff"]


class ConfiguracionNegocioForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionNegocio
        fields = [
            "nombre_negocio",
            "eslogan",
            "whatsapp_numero",
            "direccion",
            "instagram",
            "dias_anticipacion_pedido",
            "envio_habilitado",
            "costo_envio",
            "envio_gratis_desde",
        ]


class PerfilAdminForm(forms.ModelForm):
    """Edición administrativa del perfil de CUALQUIER usuario: mismos datos
    (User + Perfil combinados) que usa el propio cliente en
    usuarios.forms.PerfilForm, pero accesible desde el panel para un admin."""

    first_name = forms.CharField(max_length=150, required=False, label="Nombre")
    last_name = forms.CharField(max_length=150, required=False, label="Apellido")
    email = forms.EmailField(required=False, label="Email")

    class Meta:
        model = Perfil
        fields = ["telefono", "direccion"]

    def __init__(self, *args, usuario=None, **kwargs):
        self.usuario = usuario
        super().__init__(*args, **kwargs)
        if usuario is not None:
            self.fields["first_name"].initial = usuario.first_name
            self.fields["last_name"].initial = usuario.last_name
            self.fields["email"].initial = usuario.email

    def save(self, commit=True):
        perfil = super().save(commit=False)
        if self.usuario is not None:
            self.usuario.first_name = self.cleaned_data["first_name"]
            self.usuario.last_name = self.cleaned_data["last_name"]
            self.usuario.email = self.cleaned_data["email"]
        if commit:
            perfil.save()
            if self.usuario is not None:
                self.usuario.save(update_fields=["first_name", "last_name", "email"])
        return perfil


class PedidoEstadoForm(forms.ModelForm):
    """Cambia únicamente el estado del pedido. No toca ningún otro campo:
    ni los datos del cliente ni los ItemPedido (snapshots históricos)."""

    class Meta:
        model = Pedido
        fields = ["estado"]
