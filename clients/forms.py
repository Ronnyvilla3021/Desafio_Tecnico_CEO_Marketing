"""Formulario con validaciones de backend para Client."""
from django import forms

from .models import Client


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ["name", "company", "email", "phone", "status"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Juan Pérez", "autocomplete": "name"}),
            "company": forms.TextInput(attrs={"placeholder": "Empresa XYZ", "autocomplete": "organization"}),
            "email": forms.EmailInput(attrs={"placeholder": "juan@email.com", "autocomplete": "email"}),
            "phone": forms.TextInput(attrs={"placeholder": "0999999999", "autocomplete": "tel", "inputmode": "tel"}),
        }

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        if len(name) < 2:
            raise forms.ValidationError("El nombre debe tener al menos 2 caracteres.")
        return name

    def clean_email(self):
        # Se normaliza a minúsculas para que la validación de unicidad sea consistente.
        return self.cleaned_data["email"].strip().lower()