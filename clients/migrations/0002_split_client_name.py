"""Separa el campo name en first_name y last_name conservando los datos existentes."""
from django.core.validators import MinLengthValidator
from django.db import migrations, models


def split_name(apps, schema_editor):
    """'Juan Carlos Pérez' -> nombre 'Juan', apellido 'Carlos Pérez'."""
    Client = apps.get_model("clients", "Client")
    for client in Client.objects.all():
        first, _, last = client.first_name.strip().partition(" ")
        client.first_name = first
        client.last_name = last.strip()
        client.save(update_fields=["first_name", "last_name"])


def join_name(apps, schema_editor):
    """Reversa: vuelve a juntar nombre y apellido en un solo campo."""
    Client = apps.get_model("clients", "Client")
    for client in Client.objects.all():
        client.first_name = f"{client.first_name} {client.last_name}".strip()
        client.save(update_fields=["first_name"])


class Migration(migrations.Migration):

    dependencies = [
        ("clients", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(model_name="client", old_name="name", new_name="first_name"),
        migrations.AlterField(
            model_name="client",
            name="first_name",
            field=models.CharField(
                "nombre",
                max_length=60,
                validators=[MinLengthValidator(2, "El nombre debe tener al menos 2 caracteres.")],
            ),
        ),
        migrations.AddField(
            model_name="client",
            name="last_name",
            field=models.CharField(
                "apellido",
                max_length=60,
                default="",
                validators=[MinLengthValidator(2, "El apellido debe tener al menos 2 caracteres.")],
            ),
            preserve_default=False,
        ),
        migrations.RunPython(split_name, join_name),
    ]