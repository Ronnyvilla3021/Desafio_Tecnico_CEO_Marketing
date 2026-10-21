"""Rutas de la app clients."""
from django.urls import path

from . import views

app_name = "clients"

urlpatterns = [
    path("", views.client_list, name="list"),
    path("clients/create/", views.client_create, name="create"),
    path("clients/<int:pk>/", views.client_detail, name="detail"),
    path("clients/<int:pk>/update/", views.client_update, name="update"),
    path("clients/<int:pk>/delete/", views.client_delete, name="delete"),
]