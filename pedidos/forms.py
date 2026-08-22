from datetime import timedelta

from django import forms
from django.utils import timezone

from panel.models import ConfiguracionNegocio

from .models import Pedido


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Pedido
        fields = [
            "nombre",
            "apellido",
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
        self.config = ConfiguracionNegocio.get_solo()
        self.fecha_minima = timezone.localdate() + timedelta(days=self.config.dias_anticipacion_pedido)
        self.fields["fecha_pedido"].widget.attrs["min"] = self.fecha_minima.isoformat()
        if not self.config.envio_habilitado:
            self.fields["tipo_entrega"].choices = [
                choice for choice in Pedido.TipoEntrega.choices if choice[0] != Pedido.TipoEntrega.ENVIO
            ]

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
