from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from catalogo.models import Categoria, Producto, VarianteProducto


def crear_cliente(username="cliente"):
    return User.objects.create_user(username=username, password="clave-valida-123")


def crear_admin(username="admin"):
    return User.objects.create_user(username=username, password="clave-valida-123", is_staff=True)


class ProteccionDelPanelTests(TestCase):
    def test_anonimo_es_redirigido_al_login_del_panel(self):
        respuesta = self.client.get(reverse("panel:dashboard"))
        self.assertRedirects(respuesta, f"{reverse('panel:login')}?next={reverse('panel:dashboard')}")

    def test_cliente_autenticado_no_staff_recibe_403(self):
        crear_cliente()
        self.client.login(username="cliente", password="clave-valida-123")
        respuesta = self.client.get(reverse("panel:dashboard"))
        self.assertEqual(respuesta.status_code, 403)

    def test_usuario_staff_inactivo_no_accede(self):
        usuario = crear_admin("staff_inactivo")
        usuario.is_active = False
        usuario.save()
        # No puede ni loguearse (backend de Django ya bloquea usuarios inactivos).
        logueado = self.client.login(username="staff_inactivo", password="clave-valida-123")
        self.assertFalse(logueado)

    def test_administrador_accede_al_dashboard(self):
        crear_admin()
        self.client.login(username="admin", password="clave-valida-123")
        respuesta = self.client.get(reverse("panel:dashboard"))
        self.assertEqual(respuesta.status_code, 200)

    def test_cliente_no_accede_a_gestion_de_usuarios(self):
        crear_cliente()
        self.client.login(username="cliente", password="clave-valida-123")
        respuesta = self.client.get(reverse("panel:usuarios"))
        self.assertEqual(respuesta.status_code, 403)

    def test_cliente_no_accede_a_configuracion(self):
        crear_cliente()
        self.client.login(username="cliente", password="clave-valida-123")
        respuesta = self.client.get(reverse("panel:configuracion"))
        self.assertEqual(respuesta.status_code, 403)


class DashboardTests(TestCase):
    def test_dashboard_muestra_conteos_correctos(self):
        from catalogo.models import Categoria, Producto

        productos_antes = Producto.objects.count()
        categorias_antes = Categoria.objects.count()
        categoria = Categoria.objects.create(nombre="Test", slug="test")
        Producto.objects.create(
            categoria=categoria, nombre="Producto Test", slug="producto-test",
            unidad_venta="unidad", precio=1000,
        )
        crear_admin()
        self.client.login(username="admin", password="clave-valida-123")
        respuesta = self.client.get(reverse("panel:dashboard"))
        self.assertEqual(respuesta.context["total_productos"], productos_antes + 1)
        self.assertEqual(respuesta.context["total_categorias"], categorias_antes + 1)


class GestionUsuariosTests(TestCase):
    def setUp(self):
        self.admin = crear_admin()
        self.client.login(username="admin", password="clave-valida-123")

    def test_administrador_crea_usuario(self):
        respuesta = self.client.post(reverse("panel:usuario_crear"), {
            "username": "nuevo_usuario",
            "first_name": "Nuevo",
            "last_name": "Usuario",
            "email": "nuevo@example.com",
            "is_staff": True,
            "password1": "una-clave-segura-123",
            "password2": "una-clave-segura-123",
        })
        self.assertRedirects(respuesta, reverse("panel:usuarios"))
        creado = User.objects.get(username="nuevo_usuario")
        self.assertTrue(creado.is_staff)
        self.assertNotEqual(creado.password, "una-clave-segura-123")

    def test_administrador_edita_usuario(self):
        otro = crear_cliente("otro_usuario")
        respuesta = self.client.post(reverse("panel:usuario_editar", args=[otro.pk]), {
            "username": "otro_usuario",
            "first_name": "Editado",
            "last_name": "Apellido",
            "email": "editado@example.com",
            "is_active": True,
            "is_staff": True,
        })
        self.assertRedirects(respuesta, reverse("panel:usuarios"))
        otro.refresh_from_db()
        self.assertEqual(otro.first_name, "Editado")
        self.assertTrue(otro.is_staff)

    def test_administrador_desactiva_usuario(self):
        otro = crear_cliente("otro_usuario2")
        respuesta = self.client.post(reverse("panel:usuario_editar", args=[otro.pk]), {
            "username": "otro_usuario2",
            "first_name": "",
            "last_name": "",
            "email": "",
            "is_active": False,
            "is_staff": False,
        })
        self.assertRedirects(respuesta, reverse("panel:usuarios"))
        otro.refresh_from_db()
        self.assertFalse(otro.is_active)

    def test_administrador_cambia_password_de_usuario(self):
        otro = crear_cliente("otro_usuario3")
        respuesta = self.client.post(reverse("panel:usuario_password", args=[otro.pk]), {
            "new_password1": "otra-clave-segura-456",
            "new_password2": "otra-clave-segura-456",
        })
        self.assertRedirects(respuesta, reverse("panel:usuarios"))
        otro.refresh_from_db()
        self.assertTrue(otro.check_password("otra-clave-segura-456"))

    def test_administrador_no_puede_quitarse_permisos_a_si_mismo(self):
        respuesta = self.client.post(reverse("panel:usuario_editar", args=[self.admin.pk]), {
            "username": "admin",
            "first_name": "",
            "last_name": "",
            "email": "",
            "is_active": True,
            "is_staff": False,
        })
        self.assertEqual(respuesta.status_code, 200)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_staff)

    def test_administrador_no_puede_desactivarse_a_si_mismo(self):
        respuesta = self.client.post(reverse("panel:usuario_editar", args=[self.admin.pk]), {
            "username": "admin",
            "first_name": "",
            "last_name": "",
            "email": "",
            "is_active": False,
            "is_staff": True,
        })
        self.assertEqual(respuesta.status_code, 200)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)

    def test_cliente_no_puede_crear_usuarios(self):
        self.client.logout()
        crear_cliente("cliente_normal")
        self.client.login(username="cliente_normal", password="clave-valida-123")
        respuesta = self.client.get(reverse("panel:usuario_crear"))
        self.assertEqual(respuesta.status_code, 403)


class ConfiguracionNegocioPanelTests(TestCase):
    def test_administrador_edita_configuracion(self):
        crear_admin()
        self.client.login(username="admin", password="clave-valida-123")
        respuesta = self.client.post(reverse("panel:configuracion"), {
            "nombre_negocio": "Capricho",
            "eslogan": "Boutique Empanadas & Bakery",
            "whatsapp_numero": "5493790001111",
            "direccion": "",
            "instagram": "",
            "dias_anticipacion_pedido": 1,
            "envio_habilitado": True,
            "costo_envio": "",
            "envio_gratis_desde": "",
        })
        self.assertRedirects(respuesta, reverse("panel:configuracion"))
        from panel.models import ConfiguracionNegocio
        config = ConfiguracionNegocio.get_solo()
        self.assertEqual(config.whatsapp_numero, "5493790001111")


def datos_formset_variantes(variantes=None, total_forms=None):
    """Arma los datos de management form + forms del inline de variantes
    (prefix "variantes"). `variantes` es una lista de dicts con nombre/precio/
    orden/activo; si viene vacia, se manda TOTAL_FORMS=0 (sin formularios) en
    vez de un form "extra" sin completar: un form extra recién instanciado
    trae valores iniciales de los defaults del modelo (activo=True, orden=0),
    y compararlos contra un POST vacío hace que Django lo considere
    "modificado" y dispare validación de campos obligatorios."""
    variantes = variantes or []
    if total_forms is None:
        total_forms = len(variantes)
    datos = {
        "variantes-TOTAL_FORMS": str(max(total_forms, len(variantes))),
        "variantes-INITIAL_FORMS": "0",
        "variantes-MIN_NUM_FORMS": "0",
        "variantes-MAX_NUM_FORMS": "1000",
    }
    for i, variante in enumerate(variantes):
        datos[f"variantes-{i}-nombre"] = variante.get("nombre", "")
        datos[f"variantes-{i}-precio"] = str(variante.get("precio", ""))
        datos[f"variantes-{i}-orden"] = str(variante.get("orden", 0))
        if variante.get("activo", True):
            datos[f"variantes-{i}-activo"] = "on"
        datos[f"variantes-{i}-id"] = str(variante.get("id", ""))
    return datos


def crear_categoria_test(**kwargs):
    datos = {"nombre": "Categoria Panel Test", "slug": "categoria-panel-test"}
    datos.update(kwargs)
    return Categoria.objects.create(**datos)


class CategoriaCRUDPanelTests(TestCase):
    def setUp(self):
        crear_admin()
        self.client.login(username="admin", password="clave-valida-123")

    def test_anonimo_no_accede_al_crud_de_categorias(self):
        self.client.logout()
        respuesta = self.client.get(reverse("panel:categorias"))
        self.assertEqual(respuesta.status_code, 302)

    def test_cliente_no_accede_al_crud_de_categorias(self):
        self.client.logout()
        crear_cliente("cliente_cat")
        self.client.login(username="cliente_cat", password="clave-valida-123")
        respuesta = self.client.get(reverse("panel:categoria_crear"))
        self.assertEqual(respuesta.status_code, 403)

    def test_admin_crea_categoria(self):
        respuesta = self.client.post(reverse("panel:categoria_crear"), {
            "nombre": "Nueva Categoria Test", "slug": "", "descripcion": "", "orden": 0, "activo": True,
        })
        self.assertRedirects(respuesta, reverse("panel:categorias"))
        categoria = Categoria.objects.get(nombre="Nueva Categoria Test")
        self.assertEqual(categoria.slug, "nueva-categoria-test")

    def test_admin_edita_categoria(self):
        categoria = crear_categoria_test()
        respuesta = self.client.post(reverse("panel:categoria_editar", args=[categoria.pk]), {
            "nombre": "Categoria Editada Test", "slug": "categoria-panel-test", "descripcion": "", "orden": 1, "activo": True,
        })
        self.assertRedirects(respuesta, reverse("panel:categorias"))
        categoria.refresh_from_db()
        self.assertEqual(categoria.nombre, "Categoria Editada Test")

    def test_admin_desactiva_categoria(self):
        categoria = crear_categoria_test()
        respuesta = self.client.post(reverse("panel:categoria_toggle_activo", args=[categoria.pk]), {"activo": ""})
        self.assertRedirects(respuesta, reverse("panel:categorias"))
        categoria.refresh_from_db()
        self.assertFalse(categoria.activo)


class ProductoCRUDPanelTests(TestCase):
    def setUp(self):
        crear_admin()
        self.client.login(username="admin", password="clave-valida-123")
        self.categoria = crear_categoria_test()

    def _datos_producto(self, **overrides):
        datos = {
            "categoria": self.categoria.pk,
            "nombre": "Producto Panel Test",
            "slug": "",
            "descripcion_corta": "",
            "descripcion": "",
            "precio": "1000",
            "unidad_venta": "unidad",
            "disponible": True,
            "destacado": False,
            "activo": True,
        }
        datos.update(overrides)
        return datos

    def test_cliente_no_accede_al_crud_de_productos(self):
        self.client.logout()
        crear_cliente("cliente_prod")
        self.client.login(username="cliente_prod", password="clave-valida-123")
        respuesta = self.client.get(reverse("panel:producto_crear"))
        self.assertEqual(respuesta.status_code, 403)

    def test_a_producto_sin_variantes_con_precio_valido_guarda(self):
        datos = self._datos_producto()
        datos.update(datos_formset_variantes([]))
        respuesta = self.client.post(reverse("panel:producto_crear"), datos)
        self.assertRedirects(respuesta, reverse("panel:productos"))
        producto = Producto.objects.get(nombre="Producto Panel Test")
        self.assertEqual(producto.precio, 1000)
        self.assertFalse(producto.tiene_variantes)

    def test_b_producto_sin_variantes_precio_vacio_da_error_y_no_guarda(self):
        datos = self._datos_producto(precio="")
        datos.update(datos_formset_variantes([]))
        respuesta = self.client.post(reverse("panel:producto_crear"), datos)
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Un producto sin variantes debe tener un precio.")
        self.assertFalse(Producto.objects.filter(nombre="Producto Panel Test").exists())

    def test_c_producto_con_variantes_activas_precio_vacio_guarda(self):
        datos = self._datos_producto(precio="")
        datos.update(datos_formset_variantes([
            {"nombre": "Cocinadas", "precio": 100, "orden": 0, "activo": True},
        ]))
        respuesta = self.client.post(reverse("panel:producto_crear"), datos)
        self.assertRedirects(respuesta, reverse("panel:productos"))
        producto = Producto.objects.get(nombre="Producto Panel Test")
        self.assertIsNone(producto.precio)
        self.assertTrue(producto.tiene_variantes)
        self.assertEqual(producto.variantes.get().nombre, "Cocinadas")

    def test_d_producto_con_variantes_activas_y_precio_propio_da_error_y_no_guarda(self):
        datos = self._datos_producto(precio="1000")
        datos.update(datos_formset_variantes([
            {"nombre": "Cocinadas", "precio": 100, "orden": 0, "activo": True},
        ]))
        respuesta = self.client.post(reverse("panel:producto_crear"), datos)
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Un producto con variantes debe tener el precio del producto vacío.")
        self.assertFalse(Producto.objects.filter(nombre="Producto Panel Test").exists())

    def test_e_producto_con_solo_variantes_inactivas_y_precio_se_comporta_como_sin_variantes(self):
        datos = self._datos_producto(precio="1000")
        datos.update(datos_formset_variantes([
            {"nombre": "Vieja", "precio": 100, "orden": 0, "activo": False},
        ]))
        respuesta = self.client.post(reverse("panel:producto_crear"), datos)
        self.assertRedirects(respuesta, reverse("panel:productos"))
        producto = Producto.objects.get(nombre="Producto Panel Test")
        self.assertEqual(producto.precio, 1000)
        self.assertFalse(producto.tiene_variantes)

    def test_admin_edita_producto(self):
        producto = Producto.objects.create(
            categoria=self.categoria, nombre="Producto Editar Test", slug="producto-editar-test",
            unidad_venta="unidad", precio=500,
        )
        datos = self._datos_producto(nombre="Producto Editado Test", slug="producto-editar-test", precio="750")
        datos.update(datos_formset_variantes([]))
        respuesta = self.client.post(reverse("panel:producto_editar", args=[producto.pk]), datos)
        self.assertRedirects(respuesta, reverse("panel:productos"))
        producto.refresh_from_db()
        self.assertEqual(producto.nombre, "Producto Editado Test")
        self.assertEqual(producto.precio, 750)

    def test_admin_cambia_categoria_de_producto(self):
        otra_categoria = Categoria.objects.create(nombre="Otra Categoria Test", slug="otra-categoria-test")
        producto = Producto.objects.create(
            categoria=self.categoria, nombre="Producto Cambia Categoria Test", slug="producto-cambia-categoria-test",
            unidad_venta="unidad", precio=500,
        )
        datos = self._datos_producto(
            nombre="Producto Cambia Categoria Test", slug="producto-cambia-categoria-test",
            categoria=otra_categoria.pk,
        )
        datos.update(datos_formset_variantes([]))
        respuesta = self.client.post(reverse("panel:producto_editar", args=[producto.pk]), datos)
        self.assertRedirects(respuesta, reverse("panel:productos"))
        producto.refresh_from_db()
        self.assertEqual(producto.categoria_id, otra_categoria.pk)

    def test_admin_desactiva_variante_desde_el_inline(self):
        producto = Producto.objects.create(
            categoria=self.categoria, nombre="Producto Desactivar Variante Test", slug="producto-desactivar-variante-test",
            unidad_venta="docena", precio=None,
        )
        variante = VarianteProducto.objects.create(producto=producto, nombre="Cocinadas", precio=100)
        datos = self._datos_producto(
            nombre="Producto Desactivar Variante Test", slug="producto-desactivar-variante-test", precio="900",
        )
        datos.update(datos_formset_variantes([
            {"id": variante.pk, "nombre": "Cocinadas", "precio": 100, "orden": 0, "activo": False},
        ]))
        datos["variantes-INITIAL_FORMS"] = "1"
        respuesta = self.client.post(reverse("panel:producto_editar", args=[producto.pk]), datos)
        self.assertRedirects(respuesta, reverse("panel:productos"))
        variante.refresh_from_db()
        producto.refresh_from_db()
        self.assertFalse(variante.activo)
        self.assertFalse(producto.tiene_variantes)
        self.assertEqual(producto.precio, 900)

    def test_admin_edita_variantes_desde_el_inline(self):
        producto = Producto.objects.create(
            categoria=self.categoria, nombre="Producto Variantes Test", slug="producto-variantes-test",
            unidad_venta="docena", precio=None,
        )
        variante = VarianteProducto.objects.create(producto=producto, nombre="Cocinadas", precio=100)
        datos = self._datos_producto(nombre="Producto Variantes Test", slug="producto-variantes-test", precio="")
        datos.update(datos_formset_variantes([
            {"id": variante.pk, "nombre": "Cocinadas", "precio": 150, "orden": 1, "activo": True},
        ]))
        datos["variantes-INITIAL_FORMS"] = "1"
        respuesta = self.client.post(reverse("panel:producto_editar", args=[producto.pk]), datos)
        self.assertRedirects(respuesta, reverse("panel:productos"))
        variante.refresh_from_db()
        self.assertEqual(variante.precio, 150)
        self.assertEqual(variante.orden, 1)

    def test_admin_activa_desactiva_producto(self):
        producto = Producto.objects.create(
            categoria=self.categoria, nombre="Producto Toggle Test", slug="producto-toggle-test",
            unidad_venta="unidad", precio=500,
        )
        respuesta = self.client.post(reverse("panel:producto_toggle_activo", args=[producto.pk]), {"activo": ""})
        self.assertRedirects(respuesta, reverse("panel:productos"))
        producto.refresh_from_db()
        self.assertFalse(producto.activo)

    def test_admin_marca_y_desmarca_destacado(self):
        producto = Producto.objects.create(
            categoria=self.categoria, nombre="Producto Destacado Test", slug="producto-destacado-test",
            unidad_venta="unidad", precio=500,
        )
        respuesta = self.client.post(reverse("panel:producto_toggle_destacado", args=[producto.pk]), {"destacado": "on"})
        self.assertRedirects(respuesta, reverse("panel:productos"))
        producto.refresh_from_db()
        self.assertTrue(producto.destacado)


class ImagenProductoTests(TestCase):
    def setUp(self):
        crear_admin()
        self.client.login(username="admin", password="clave-valida-123")
        self.categoria = crear_categoria_test()

    def test_subida_de_imagen_al_crear_producto(self):
        contenido_gif = (
            b"GIF87a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff,"
            b"\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
        )
        imagen = SimpleUploadedFile("test.gif", contenido_gif, content_type="image/gif")
        datos = {
            "categoria": self.categoria.pk,
            "nombre": "Producto Con Imagen Test",
            "slug": "",
            "descripcion_corta": "",
            "descripcion": "",
            "imagen": imagen,
            "precio": "1000",
            "unidad_venta": "unidad",
            "disponible": True,
            "destacado": False,
            "activo": True,
        }
        datos.update(datos_formset_variantes([]))
        respuesta = self.client.post(reverse("panel:producto_crear"), datos)
        self.assertRedirects(respuesta, reverse("panel:productos"))
        producto = Producto.objects.get(nombre="Producto Con Imagen Test")
        self.assertTrue(producto.imagen)
        self.assertIn("productos/", producto.imagen.name)
        producto.imagen.delete(save=True)

    def test_template_de_detalle_usa_la_url_de_la_imagen(self):
        contenido_gif = (
            b"GIF87a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff,"
            b"\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
        )
        imagen = SimpleUploadedFile("test2.gif", contenido_gif, content_type="image/gif")
        producto = Producto.objects.create(
            categoria=self.categoria, nombre="Producto Imagen Detalle Test", slug="producto-imagen-detalle-test",
            unidad_venta="unidad", precio=500, imagen=imagen,
        )
        respuesta = self.client.get(reverse("catalogo:producto_detalle", args=["producto-imagen-detalle-test"]))
        self.assertContains(respuesta, producto.imagen.url)
        producto.imagen.delete(save=True)
