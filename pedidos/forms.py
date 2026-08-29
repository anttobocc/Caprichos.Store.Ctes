from datetime import timedelta

from django import forms
from django.utils import timezone

from panel.models import ConfiguracionNegocio

from .models import Pedido


class CheckoutForm(forms.ModelForm):
    # El modelo Pedido guarda nombre/apellido en columnas separadas, pero el
    # formulario pide un único campo "Nombre y apellido" (pedido explícito):
    # este campo NO es del modelo, se declara acá y se parte en save().
    nombre_completo = forms.CharField(label="Nombre y apellido", max_length=201)

    class Meta:
        model = Pedido
        fields = [
            "telefono",
            "tipo_entrega",
            "direccion_envio",
            "fecha_pedido",
            "observaciones",
        ]
        widgets = {
            "fecha_pedido": forms.DateInput(attrs={"type": "date"}),
            "observaciones": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get("instance")
        if instance is not None and instance.pk and "nombre_completo" not in (kwargs.get("initial") or {}):
            self.fields["nombre_completo"].initial = f"{instance.nombre} {instance.apellido}".strip()
        self.config = ConfiguracionNegocio.get_solo()
        self.fecha_minima = timezone.localdate() + timedelta(days=self.config.dias_anticipacion_pedido)
        self.fields["fecha_pedido"].widget.attrs["min"] = self.fecha_minima.isoformat()
        if not self.config.envio_habilitado:
            self.fields["tipo_entrega"].choices = [
                choice for choice in Pedido.TipoEntrega.choices if choice[0] != Pedido.TipoEntrega.ENVIO
            ]

    def clean_nombre_completo(self):
        valor = self.cleaned_data["nombre_completo"].strip()
        if not valor:
            raise forms.ValidationError("Ingresá tu nombre y apellido.")
        return valor

    def save(self, commit=True):
        pedido = super().save(commit=False)
        partes = self.cleaned_data["nombre_completo"].split(maxsplit=1)
        pedido.nombre = partes[0]
        pedido.apellido = partes[1] if len(partes) > 1 else ""
        if commit:
            pedido.save()
        return pedido

    def clean_fecha_pedido(self):
        fecha_pedido = self.cleaned_data["fecha_pedido"]
        if fecha_pedido < self.fecha_minima:
            raise forms.ValidationError(
                f"Los pedidos requieren al menos {self.config.dias_anticipacion_pedido} día(s) de anticipación. "
                f"La fecha más próxima disponible es {self.fecha_minima.strftime('%d/%m/%Y')}."
            )
        return fecha_pedido

    def clean(self):
        cleaned = super().clean()
        tipo_entrega = cleaned.get("tipo_entrega")
        if tipo_entrega == Pedido.TipoEntrega.ENVIO:
            if not self.config.envio_habilitado:
                self.add_error("tipo_entrega", "El envío no está disponible en este momento.")
            elif not cleaned.get("direccion_envio"):
                self.add_error("direccion_envio", "La dirección es obligatoria para pedidos con envío.")
        return cleaned
