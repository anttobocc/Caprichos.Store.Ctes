from django.urls import path

from . import views

app_name = "pedidos"

urlpatterns = [
    path("carrito/", views.carrito_ver, name="carrito"),
    path("carrito/agregar/<int:producto_id>/", views.carrito_agregar, name="carrito_agregar"),
    path("carrito/agregar-combo/<int:combo_id>/", views.carrito_agregar_combo, name="carrito_agregar_combo"),
    path("carrito/actualizar/<str:clave>/", views.carrito_actualizar, name="carrito_actualizar"),
    path("carrito/eliminar/<str:clave>/", views.carrito_eliminar, name="carrito_eliminar"),
    path("carrito/vaciar/", views.carrito_vaciar, name="carrito_vaciar"),
    path("checkout/", views.checkout, name="checkout"),
    path("mis-pedidos/", views.mis_pedidos, name="mis_pedidos"),
    path("pedidos/<int:pk>/", views.pedido_detalle, name="pedido_detalle"),
]
