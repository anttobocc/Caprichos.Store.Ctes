from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.forms import inlineformset_factory
from django.utils.text import slugify

from catalogo.models import Categoria, Combo, ComboItem, Producto, VarianteProducto
from pedidos.models import Pedido
from usuarios.models import Perfil

from .models import ConfiguracionNegocio


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
            "imagen_pos_x": forms.HiddenInput(),
            "imagen_pos_y": forms.HiddenInput(),
            "imagen_tamano": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["slug"].required = False
        # Los completa el editor visual de imagen (arrastrar/deslizador) vía
        # JS; si llegan vacíos (por ejemplo un POST manual) se usa el
        # default del modelo en lugar de exigirlos en el formulario.
        self.fields["imagen_pos_x"].required = False
        self.fields["imagen_pos_y"].required = False
        self.fields["imagen_tamano"].required = False

    def clean(self):
        cleaned = super().clean()
        nombre = cleaned.get("nombre")
        if nombre:
            cleaned["slug"] = _slug_unico(Categoria, nombre, cleaned.get("slug"), self.instance.pk)
        if cleaned.get("imagen_pos_x") in (None, ""):
            cleaned["imagen_pos_x"] = 0
        if cleaned.get("imagen_pos_y") in (None, ""):
            cleaned["imagen_pos_y"] = 0
        if cleaned.get("imagen_tamano") in (None, ""):
            cleaned["imagen_tamano"] = 260
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
            "precio",
            "unidad_venta",
            "destacado",
        ]
        widgets = {"descripcion": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["slug"].required = False
        self.fields["precio"].required = False

    def clean(self):
        cleaned = super().clean()
        nombre = cleaned.get("nombre")
        if nombre:
            cleaned["slug"] = _slug_unico(Producto, nombre, cleaned.get("slug"), self.instance.pk)
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
        fields = ["nombre", "slug", "descripcion", "imagen", "precio_promocional"]
        widgets = {"descripcion": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["slug"].required = False

    def clean(self):
        cleaned = super().clean()
        nombre = cleaned.get("nombre")
        if nombre:
            cleaned["slug"] = _slug_unico(Combo, nombre, cleaned.get("slug"), self.instance.pk)
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
