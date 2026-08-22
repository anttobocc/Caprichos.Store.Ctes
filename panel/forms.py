from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.forms import inlineformset_factory
from django.utils.text import slugify

from catalogo.models import Categoria, Producto, VarianteProducto
from pedidos.models import Pedido

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
        fields = ["nombre", "slug", "descripcion", "orden", "activo"]
        widgets = {"descripcion": forms.Textarea(attrs={"rows": 2})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["slug"].required = False

    def clean(self):
        cleaned = super().clean()
        nombre = cleaned.get("nombre")
        if nombre:
            cleaned["slug"] = _slug_unico(Categoria, nombre, cleaned.get("slug"), self.instance.pk)
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
            "disponible",
            "destacado",
            "activo",
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
    fields=["nombre", "precio", "orden", "activo"],
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
        fields = ["username", "first_name", "last_name", "email", "is_active", "is_staff"]


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


class PedidoEstadoForm(forms.ModelForm):
    """Cambia únicamente el estado del pedido. No toca ningún otro campo:
    ni los datos del cliente ni los ItemPedido (snapshots históricos)."""

    class Meta:
        model = Pedido
        fields = ["estado"]
