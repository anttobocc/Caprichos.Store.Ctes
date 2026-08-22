from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Perfil


class RegistroYPerfilTests(TestCase):
    def test_registro_crea_usuario_y_perfil_con_telefono(self):
        respuesta = self.client.post(reverse("usuarios:registro"), {
            "username": "cliente1",
            "first_name": "Ana",
            "last_name": "Pérez",
            "email": "ana@example.com",
            "telefono": "3790000000",
            "password1": "una-clave-segura-123",
            "password2": "una-clave-segura-123",
        })
        self.assertEqual(respuesta.status_code, 302)
        usuario = User.objects.get(username="cliente1")
        self.assertFalse(usuario.is_staff)
        self.assertTrue(Perfil.objects.filter(usuario=usuario).exists())
        self.assertEqual(usuario.perfil.telefono, "3790000000")

    def test_password_se_guarda_hasheada(self):
        self.client.post(reverse("usuarios:registro"), {
            "username": "cliente2",
            "first_name": "Luz",
            "last_name": "Gómez",
            "email": "",
            "telefono": "",
            "password1": "una-clave-segura-123",
            "password2": "una-clave-segura-123",
        })
        usuario = User.objects.get(username="cliente2")
        self.assertNotEqual(usuario.password, "una-clave-segura-123")
        self.assertTrue(usuario.password.startswith("pbkdf2_") or usuario.password.startswith("argon2"))

    def test_login_cliente_correcto(self):
        User.objects.create_user(username="cliente3", password="clave-valida-123")
        respuesta = self.client.post(reverse("usuarios:login"), {
            "username": "cliente3",
            "password": "clave-valida-123",
        })
        self.assertRedirects(respuesta, reverse("usuarios:perfil"))

    def test_usuario_inactivo_no_puede_iniciar_sesion(self):
        usuario = User.objects.create_user(username="cliente4", password="clave-valida-123")
        usuario.is_active = False
        usuario.save()
        respuesta = self.client.post(reverse("usuarios:login"), {
            "username": "cliente4",
            "password": "clave-valida-123",
        })
        self.assertEqual(respuesta.status_code, 200)  # vuelve al form, no autentica
        self.assertFalse(respuesta.wsgi_request.user.is_authenticated)

    def test_logout_cierra_sesion(self):
        User.objects.create_user(username="cliente5", password="clave-valida-123")
        self.client.login(username="cliente5", password="clave-valida-123")
        respuesta = self.client.post(reverse("usuarios:logout"))
        self.assertRedirects(respuesta, reverse("usuarios:login"))

    def test_editar_perfil_actualiza_user_y_perfil(self):
        usuario = User.objects.create_user(username="cliente6", password="clave-valida-123")
        self.client.login(username="cliente6", password="clave-valida-123")
        respuesta = self.client.post(reverse("usuarios:perfil_editar"), {
            "first_name": "Nuevo",
            "last_name": "Nombre",
            "email": "nuevo@example.com",
            "telefono": "3790001111",
            "direccion": "Calle Falsa 123",
        })
        self.assertRedirects(respuesta, reverse("usuarios:perfil"))
        usuario.refresh_from_db()
        self.assertEqual(usuario.first_name, "Nuevo")
        self.assertEqual(usuario.perfil.telefono, "3790001111")
        self.assertEqual(usuario.perfil.direccion, "Calle Falsa 123")

    def test_signal_crea_perfil_automaticamente(self):
        usuario = User.objects.create_user(username="cliente7", password="x")
        self.assertTrue(Perfil.objects.filter(usuario=usuario).exists())
