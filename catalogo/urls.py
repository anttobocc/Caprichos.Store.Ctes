from django.urls import path

from . import views

app_name = "catalogo"

urlpatterns = [
    path("", views.home, name="home"),
    path("productos/", views.lista_productos, name="productos"),
    path("categoria/<slug:slug>/", views.categoria_detalle, name="categoria_detalle"),
    path("producto/<slug:slug>/", views.producto_detalle, name="producto_detalle"),
    path("combos/", views.combos_publico, name="combos"),
    path("combo/<slug:slug>/", views.combo_detalle, name="combo_detalle"),
]
