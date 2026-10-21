"""Vistas del Mini CRM: dashboard y operaciones CRUD (respuestas JSON)."""
from django.contrib import messages
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET, require_POST

from .forms import ClientForm
from .models import Client


def _serialize(client):
    """Convierte un cliente a diccionario para respuestas JSON."""
    return {
        "id": client.pk,
        "first_name": client.first_name,
        "last_name": client.last_name,
        "full_name": client.full_name,
        "company": client.company,
        "email": client.email,
        "phone": client.phone,
        "status": client.status,
        "status_display": client.get_status_display(),
    }


def _form_errors(form):
    """Devuelve los errores del formulario como {campo: [mensajes]}."""
    return {
        field: [error["message"] for error in errors]
        for field, errors in form.errors.get_json_data().items()
    }


@require_GET
def client_list(request):
    """Dashboard: resumen, tabla de clientes y filtros (también funcionan por GET sin JS)."""
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()

    clients = Client.objects.all()
    # Cada palabra debe aparecer en nombre, apellido o empresa.
    # Así "juan perez" encuentra a Juan Pérez aunque estén en campos distintos.
    for term in query.split():
        clients = clients.filter(
            Q(first_name__icontains=term) | Q(last_name__icontains=term) | Q(company__icontains=term)
        )
    if status in Client.Status.values:
        clients = clients.filter(status=status)

    stats = Client.objects.aggregate(
        total=Count("id"),
        prospects=Count("id", filter=Q(status=Client.Status.PROSPECT)),
        customers=Count("id", filter=Q(status=Client.Status.CLIENT)),
        inactive=Count("id", filter=Q(status=Client.Status.INACTIVE)),
    )

    context = {
        "clients": clients,
        "stats": stats,
        "form": ClientForm(),
        "statuses": Client.Status.choices,
        "query": query,
        "selected_status": status,
    }
    return render(request, "clients/client_list.html", context)


@require_GET
def client_detail(request, pk):
    """Consulta un cliente (usado para precargar el modal de edición)."""
    client = get_object_or_404(Client, pk=pk)
    return JsonResponse({"ok": True, "client": _serialize(client)})


@require_POST
def client_create(request):
    form = ClientForm(request.POST)
    if form.is_valid():
        client = form.save()
        message = f"Cliente {client.full_name} registrado correctamente."
        messages.success(request, message)
        return JsonResponse({"ok": True, "message": message, "client": _serialize(client)}, status=201)
    return JsonResponse(
        {"ok": False, "message": "Revisa los campos marcados.", "errors": _form_errors(form)}, status=400
    )


@require_POST
def client_update(request, pk):
    client = get_object_or_404(Client, pk=pk)
    form = ClientForm(request.POST, instance=client)
    if form.is_valid():
        client = form.save()
        message = f"Cliente {client.full_name} actualizado correctamente."
        messages.success(request, message)
        return JsonResponse({"ok": True, "message": message, "client": _serialize(client)})
    return JsonResponse(
        {"ok": False, "message": "Revisa los campos marcados.", "errors": _form_errors(form)}, status=400
    )


@require_POST
def client_delete(request, pk):
    client = get_object_or_404(Client, pk=pk)
    full_name = client.full_name
    client.delete()
    message = f"Cliente {full_name} eliminado correctamente."
    messages.success(request, message)
    return JsonResponse({"ok": True, "message": message})