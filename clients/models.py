"""Modelo de datos del Mini CRM."""
from django.core.validators import MinLengthValidator, RegexValidator
from django.db import models

phone_validator = RegexValidator(
    regex=r"^\+?\d{7,15}$",
    message="Ingresa un teléfono válido: solo dígitos, entre 7 y 15 (puede iniciar con +).",
)


class Client(models.Model):
    """Cliente o prospecto registrado en el CRM."""

    class Status(models.TextChoices):
        PROSPECT = "prospecto", "Prospecto"
        CLIENT = "cliente", "Cliente"
        INACTIVE = "inactivo", "Inactivo"

    first_name = models.CharField(
        "nombre",
        max_length=60,
        validators=[MinLengthValidator(2, "El nombre debe tener al menos 2 caracteres.")],
    )
    last_name = models.CharField(
        "apellido",
        max_length=60,
        validators=[MinLengthValidator(2, "El apellido debe tener al menos 2 caracteres.")],
    )
    company = models.CharField("empresa", max_length=120, blank=True)
    email = models.EmailField(
        "correo electrónico",
        unique=True,
        error_messages={"unique": "Ya existe un cliente registrado con este correo."},
    )
    phone = models.CharField("teléfono", max_length=16, blank=True, validators=[phone_validator])
    status = models.CharField("estado", max_length=10, choices=Status.choices, default=Status.PROSPECT)
    created_at = models.DateTimeField("creado", auto_now_add=True)
    updated_at = models.DateTimeField("actualizado", auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "cliente"
        verbose_name_plural = "clientes"

    @property
    def full_name(self):
        """Nombre completo para mostrar en pantalla."""
        return f"{self.first_name} {self.last_name}".strip()

    def __str__(self):
        return f"{self.full_name} ({self.company})" if self.company else self.full_name