"""Formulario con validaciones de backend para Client."""
from django import forms

from .models import Client


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ["first_name", "last_name", "company", "email", "phone", "status"]
        widgets = {
            "first_name": forms.TextInput(attrs={"placeholder": "Juan", "autocomplete": "given-name"}),
            "last_name": forms.TextInput(attrs={"placeholder": "Pérez", "autocomplete": "family-name"}),
            "company": forms.TextInput(attrs={"placeholder": "Empresa XYZ", "autocomplete": "organization"}),
            "email": forms.EmailInput(attrs={"placeholder": "juan@email.com", "autocomplete": "email"}),
            "phone": forms.TextInput(attrs={"placeholder": "0999999999", "autocomplete": "tel", "inputmode": "tel"}),
        }

    @staticmethod
    def _clean_person_name(value, label):
        # Quita espacios sobrantes: "  Juan   Carlos " -> "Juan Carlos"
        value = " ".join(value.split())
        if len(value) < 2:
            raise forms.ValidationError(f"El {label} debe tener al menos 2 caracteres.")
        return value

    def clean_first_name(self):
        return self._clean_person_name(self.cleaned_data["first_name"], "nombre")

    def clean_last_name(self):
        return self._clean_person_name(self.cleaned_data["last_name"], "apellido")

    def clean_email(self):
        # Se normaliza a minúsculas para que la validación de unicidad sea consistente.
        return self.cleaned_data["email"].strip().lower()