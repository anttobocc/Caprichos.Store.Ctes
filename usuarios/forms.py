from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Perfil


class RegistroForm(UserCreationForm):
    """Alta de cliente. Nunca crea administradores: is_staff/is_superuser
    no son campos de este formulario, así que un POST manipulado no
    tiene ningún efecto sobre ellos."""

    email = forms.EmailField(required=False)
    telefono = forms.CharField(max_length=30, required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ["username", "first_name", "last_name", "email"]

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.is_staff = False
        usuario.is_superuser = False
        if commit:
            usuario.save()
            # El signal post_save ya creó el Perfil; solo completamos el teléfono.
            usuario.perfil.telefono = self.cleaned_data.get("telefono", "")
            usuario.perfil.save(update_fields=["telefono"])
        return usuario


class PerfilForm(forms.ModelForm):
    """Edición de los datos propios del cliente: los de User y los de Perfil
    combinados en un único formulario."""

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
