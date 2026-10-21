"""Registro del modelo Client en Django Admin."""
from django.contrib import admin

from .models import Client

admin.site.site_header = "Mini CRM · CEO Marketing"
admin.site.site_title = "Mini CRM"
admin.site.index_title = "Administración de clientes"


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("name", "company", "email", "phone", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("name", "company", "email")
    readonly_fields = ("created_at", "updated_at")
    list_per_page = 20