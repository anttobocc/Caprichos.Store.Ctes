from django.urls import path

from . import views

app_name = "usuarios"

urlpatterns = [
    path("registro/", views.registro, name="registro"),
    path("login/", views.ClienteLoginView.as_view(), name="login"),
    path("logout/", views.ClienteLogoutView.as_view(), name="logout"),
    path("perfil/", views.perfil, name="perfil"),
    path("perfil/editar/", views.perfil_editar, name="perfil_editar"),
    path("perfil/password/", views.ClientePasswordChangeView.as_view(), name="password_change"),
    path("perfil/password/hecho/", views.password_change_done, name="password_change_done"),
]
