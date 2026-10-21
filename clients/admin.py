"""Registro del modelo Client en Django Admin."""
from django.contrib import admin
from django.utils.html import format_html

from .models import Client

admin.site.site_header = "Mini CRM · CEO Marketing"
admin.site.site_title = "Mini CRM"
admin.site.index_title = "Administración de clientes"


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("full_name", "company", "email", "phone", "status_badge", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("first_name", "last_name", "company", "email")
    readonly_fields = ("created_at", "updated_at")
    list_per_page = 20

    @admin.display(description="Cliente", ordering="first_name")
    def full_name(self, obj):
        return obj.full_name

    @admin.display(description="Estado", ordering="status")
    def status_badge(self, obj):
        # Insignia de color, igual a la del sitio (estilos en static/css/admin.css)
        return format_html(
            '<span class="crm-badge crm-badge--{}">{}</span>', obj.status, obj.get_status_display()
        )