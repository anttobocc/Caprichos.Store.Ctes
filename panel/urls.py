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
    path("usuarios/<int:pk>/activo/", views.usuario_toggle_activo, name="usuario_toggle_activo"),
    path("usuarios/<int:pk>/eliminar/", views.usuario_eliminar, name="usuario_eliminar"),
    path("categorias/", views.categorias_lista, name="categorias"),
    path("categorias/nueva/", views.categoria_crear, name="categoria_crear"),
    path("categorias/<int:pk>/editar/", views.categoria_editar, name="categoria_editar"),
    path("categorias/<int:pk>/activo/", views.categoria_toggle_activo, name="categoria_toggle_activo"),
    path("categorias/<int:pk>/eliminar/", views.categoria_eliminar, name="categoria_eliminar"),
    path("productos/", views.productos_lista, name="productos"),
    path("productos/nuevo/", views.producto_crear, name="producto_crear"),
    path("productos/<int:pk>/editar/", views.producto_editar, name="producto_editar"),
    path("productos/<int:pk>/activo/", views.producto_toggle_activo, name="producto_toggle_activo"),
    path("productos/<int:pk>/disponible/", views.producto_toggle_disponible, name="producto_toggle_disponible"),
    path("productos/<int:pk>/destacado/", views.producto_toggle_destacado, name="producto_toggle_destacado"),
    path("productos/<int:pk>/eliminar/", views.producto_eliminar, name="producto_eliminar"),
    path("pedidos/", views.pedidos_lista, name="pedidos"),
    path("pedidos/<int:pk>/", views.pedido_detalle, name="pedido_detalle"),
    path("pedidos/<int:pk>/estado/", views.pedido_cambiar_estado, name="pedido_cambiar_estado"),
    path("configuracion/", views.configuracion, name="configuracion"),
    path("perfiles/", views.perfiles_lista, name="perfiles"),
    path("perfiles/<int:pk>/editar/", views.perfil_editar, name="perfil_editar"),
    path("combos/", views.combos_lista, name="combos"),
    path("combos/nuevo/", views.combo_crear, name="combo_crear"),
    path("combos/<int:pk>/editar/", views.combo_editar, name="combo_editar"),
    path("combos/<int:pk>/activo/", views.combo_toggle_activo, name="combo_toggle_activo"),
    path("combos/<int:pk>/eliminar/", views.combo_eliminar, name="combo_eliminar"),
]
