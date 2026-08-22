from django.urls import path

from . import views

app_name = "panel"

urlpatterns = [
    path("login/", views.PanelLoginView.as_view(), name="login"),
    path("logout/", views.PanelLogoutView.as_view(), name="logout"),
    path("", views.dashboard, name="dashboard"),
    path("usuarios/", views.usuarios_lista, name="usuarios"),
    path("usuarios/nuevo/", views.usuario_crear, name="usuario_crear"),
    path("usuarios/<int:pk>/editar/", views.usuario_editar, name="usuario_editar"),
    path("usuarios/<int:pk>/password/", views.usuario_password, name="usuario_password"),
    path("productos/", views.productos_lista, name="productos"),
    path("categorias/", views.categorias_lista, name="categorias"),
    path("pedidos/", views.pedidos_lista, name="pedidos"),
    path("configuracion/", views.configuracion, name="configuracion"),
]
