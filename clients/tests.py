"""Pruebas automatizadas del Mini CRM: modelo, formulario, vistas CRUD y admin."""
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from .forms import ClientForm
from .models import Client


def make_client(**overrides):
    """Crea un cliente en la base de datos de pruebas con valores por defecto."""
    data = {
        "first_name": "Juan",
        "last_name": "Pérez",
        "company": "Empresa XYZ",
        "email": "juan@email.com",
        "phone": "0999999999",
        "status": Client.Status.PROSPECT,
    }
    data.update(overrides)
    return Client.objects.create(**data)


def payload(**overrides):
    """Datos válidos de formulario (lo que enviaría el navegador por POST)."""
    data = {
        "first_name": "Ana",
        "last_name": "Gómez",
        "company": "Acme S.A.",
        "email": "ana@email.com",
        "phone": "0988888888",
        "status": "cliente",
    }
    data.update(overrides)
    return data


class ClientModelTests(TestCase):
    def test_full_name_joins_first_and_last_name(self):
        client = make_client()
        self.assertEqual(client.full_name, "Juan Pérez")

    def test_str_includes_company_when_present(self):
        self.assertEqual(str(make_client()), "Juan Pérez (Empresa XYZ)")

    def test_str_without_company(self):
        client = make_client(company="")
        self.assertEqual(str(client), "Juan Pérez")

    def test_default_status_is_prospect(self):
        client = Client.objects.create(first_name="Ana", last_name="Gómez", email="ana@email.com")
        self.assertEqual(client.status, Client.Status.PROSPECT)

    def test_email_must_be_unique(self):
        make_client()
        with self.assertRaises(IntegrityError), transaction.atomic():
            make_client(first_name="Otro")

    def test_invalid_phone_is_rejected(self):
        client = Client(first_name="Ana", last_name="Gómez", email="ana@email.com", phone="12ab")
        with self.assertRaises(ValidationError) as context:
            client.full_clean()
        self.assertIn("phone", context.exception.message_dict)

    def test_timestamps_are_set_automatically(self):
        client = make_client()
        self.assertIsNotNone(client.created_at)
        self.assertIsNotNone(client.updated_at)


class ClientFormTests(TestCase):
    def test_valid_data_is_accepted(self):
        self.assertTrue(ClientForm(data=payload()).is_valid())

    def test_short_first_name_is_rejected(self):
        form = ClientForm(data=payload(first_name="A"))
        self.assertFalse(form.is_valid())
        self.assertIn("first_name", form.errors)

    def test_last_name_is_required(self):
        form = ClientForm(data=payload(last_name=""))
        self.assertFalse(form.is_valid())
        self.assertIn("last_name", form.errors)

    def test_invalid_phone_is_rejected(self):
        form = ClientForm(data=payload(phone="abc123"))
        self.assertFalse(form.is_valid())
        self.assertIn("phone", form.errors)

    def test_company_and_phone_are_optional(self):
        form = ClientForm(data=payload(company="", phone=""))
        self.assertTrue(form.is_valid())

    def test_email_is_normalized_to_lowercase(self):
        form = ClientForm(data=payload(email="ANA@Email.COM"))
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["email"], "ana@email.com")

    def test_extra_spaces_in_names_are_collapsed(self):
        form = ClientForm(data=payload(first_name="  Juan   Carlos ", last_name=" Pérez  "))
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["first_name"], "Juan Carlos")
        self.assertEqual(form.cleaned_data["last_name"], "Pérez")

    def test_duplicate_email_is_rejected(self):
        make_client(email="ana@email.com")
        form = ClientForm(data=payload())
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_duplicate_email_ignores_letter_case(self):
        make_client(email="ana@email.com")
        form = ClientForm(data=payload(email="ANA@email.com"))
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)


class ClientListViewTests(TestCase):
    def setUp(self):
        self.url = reverse("clients:list")
        make_client()  # Juan Pérez · Empresa XYZ · prospecto
        make_client(
            first_name="María", last_name="López", company="Acme S.A.",
            email="maria@email.com", status=Client.Status.CLIENT,
        )
        make_client(
            first_name="Carlos", last_name="Ruiz", company="Acme S.A.",
            email="carlos@email.com", status=Client.Status.INACTIVE,
        )

    def names(self, response):
        """Nombres de los clientes que la vista envió a la plantilla."""
        return {client.first_name for client in response.context["clients"]}

    def test_dashboard_loads_with_template(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "clients/client_list.html")

    def test_dashboard_shows_all_clients_and_stats(self):
        response = self.client.get(self.url)
        self.assertEqual(self.names(response), {"Juan", "María", "Carlos"})
        self.assertEqual(
            response.context["stats"],
            {"total": 3, "prospects": 1, "customers": 1, "inactive": 1},
        )

    def test_rows_expose_data_attributes_for_javascript(self):
        response = self.client.get(self.url)
        self.assertContains(response, 'data-full-name="Juan Pérez"')
        self.assertContains(response, 'data-first-name="María"')

    def test_search_by_first_name(self):
        response = self.client.get(self.url, {"q": "juan"})
        self.assertEqual(self.names(response), {"Juan"})

    def test_search_by_last_name(self):
        response = self.client.get(self.url, {"q": "ruiz"})
        self.assertEqual(self.names(response), {"Carlos"})

    def test_search_by_company(self):
        response = self.client.get(self.url, {"q": "acme"})
        self.assertEqual(self.names(response), {"María", "Carlos"})

    def test_search_by_full_name(self):
        response = self.client.get(self.url, {"q": "juan pérez"})
        self.assertEqual(self.names(response), {"Juan"})

    def test_search_ignores_letter_case(self):
        response = self.client.get(self.url, {"q": "JUAN"})
        self.assertEqual(self.names(response), {"Juan"})

    def test_search_without_results(self):
        response = self.client.get(self.url, {"q": "zzz"})
        self.assertEqual(self.names(response), set())

    def test_filter_by_status(self):
        response = self.client.get(self.url, {"status": "cliente"})
        self.assertEqual(self.names(response), {"María"})

    def test_invalid_status_is_ignored(self):
        response = self.client.get(self.url, {"status": "inventado"})
        self.assertEqual(len(self.names(response)), 3)

    def test_search_and_status_can_be_combined(self):
        response = self.client.get(self.url, {"q": "acme", "status": "inactivo"})
        self.assertEqual(self.names(response), {"Carlos"})

    def test_list_rejects_post(self):
        self.assertEqual(self.client.post(self.url).status_code, 405)


class ClientCrudTests(TestCase):
    # --- Crear ---
    def test_create_valid_client(self):
        response = self.client.post(reverse("clients:create"), payload())
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertTrue(data["ok"])
        self.assertEqual(data["client"]["full_name"], "Ana Gómez")
        self.assertEqual(Client.objects.count(), 1)

        sent = [str(message) for message in get_messages(response.wsgi_request)]
        self.assertEqual(len(sent), 1)
        self.assertIn("registrado correctamente", sent[0])

    def test_create_with_invalid_data_returns_errors(self):
        response = self.client.post(
            reverse("clients:create"), payload(first_name="", email="no-es-correo")
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data["ok"])
        self.assertIn("first_name", data["errors"])
        self.assertIn("email", data["errors"])
        self.assertEqual(Client.objects.count(), 0)

    def test_create_with_duplicate_email_returns_error(self):
        make_client(email="ana@email.com")
        response = self.client.post(reverse("clients:create"), payload())
        self.assertEqual(response.status_code, 400)
        self.assertIn("Ya existe un cliente", response.json()["errors"]["email"][0])
        self.assertEqual(Client.objects.count(), 1)

    def test_create_rejects_get(self):
        self.assertEqual(self.client.get(reverse("clients:create")).status_code, 405)

    # --- Consultar ---
    def test_detail_returns_client_data(self):
        client = make_client()
        response = self.client.get(reverse("clients:detail", args=[client.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["client"]["email"], "juan@email.com")

    def test_detail_of_missing_client_is_404(self):
        response = self.client.get(reverse("clients:detail", args=[999]))
        self.assertEqual(response.status_code, 404)

    # --- Editar ---
    def test_update_changes_client(self):
        client = make_client()
        response = self.client.post(
            reverse("clients:update", args=[client.pk]),
            payload(first_name="Juana", email="juana@email.com", status="inactivo"),
        )
        self.assertEqual(response.status_code, 200)
        client.refresh_from_db()
        self.assertEqual(client.first_name, "Juana")
        self.assertEqual(client.status, Client.Status.INACTIVE)

    def test_update_can_keep_own_email(self):
        client = make_client()
        response = self.client.post(
            reverse("clients:update", args=[client.pk]), payload(email="juan@email.com")
        )
        self.assertEqual(response.status_code, 200)

    def test_update_with_email_of_another_client_fails(self):
        make_client(first_name="Otro", last_name="Cliente", email="otro@email.com")
        client = make_client()
        response = self.client.post(
            reverse("clients:update", args=[client.pk]), payload(email="otro@email.com")
        )
        self.assertEqual(response.status_code, 400)
        client.refresh_from_db()
        self.assertEqual(client.email, "juan@email.com")

    def test_update_of_missing_client_is_404(self):
        response = self.client.post(reverse("clients:update", args=[999]), payload())
        self.assertEqual(response.status_code, 404)

    # --- Eliminar ---
    def test_delete_removes_client(self):
        client = make_client()
        response = self.client.post(reverse("clients:delete", args=[client.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["ok"])
        self.assertFalse(Client.objects.filter(pk=client.pk).exists())

    def test_delete_of_missing_client_is_404(self):
        response = self.client.post(reverse("clients:delete", args=[999]))
        self.assertEqual(response.status_code, 404)

    def test_delete_rejects_get(self):
        client = make_client()
        response = self.client.get(reverse("clients:delete", args=[client.pk]))
        self.assertEqual(response.status_code, 405)
        self.assertTrue(Client.objects.filter(pk=client.pk).exists())


class ClientAdminTests(TestCase):
    def test_model_is_registered_in_admin(self):
        self.assertIn(Client, admin.site._registry)

    def test_changelist_lists_clients_for_superuser(self):
        make_client()
        user = get_user_model().objects.create_superuser("admin", "admin@email.com", "clave-segura-123")
        self.client.force_login(user)
        response = self.client.get(reverse("admin:clients_client_changelist"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Juan Pérez")