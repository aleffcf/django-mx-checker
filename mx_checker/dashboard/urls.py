
from django.urls import path
from . import views

urlpatterns = [
    path("mx-dashboard/", views.mx_dashboard, name="mx_dashboard"),
    path(
        "mx-dashboard/data/",
        views.mx_dashboard_data,
        name="mx_dashboard_data",
    ),
]
