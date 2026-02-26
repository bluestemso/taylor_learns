from django.urls import path

from . import views

app_name = "gadgets"

urlpatterns = [
    path("", views.index, name="index"),
    path("<slug:slug>/", views.detail, name="detail"),
    path("<slug:slug>/<path:asset_path>", views.asset, name="asset"),
]
