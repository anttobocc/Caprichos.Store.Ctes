from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


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
