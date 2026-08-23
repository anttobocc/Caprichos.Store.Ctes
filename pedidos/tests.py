from datetime import date, timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from catalogo.models import Categoria, Producto, VarianteProducto
from panel.models import ConfiguracionNegocio

from . import whatsapp
from .models import ItemPedido, Pedido


def crear_usuario(username="cliente"):
    return User.objects.create_user(username=username, password="clave-valida-123")


def crear_categoria(**kwargs):
    datos = {"nombre": "Categoria Pedidos Test", "slug": "categoria-pedidos-test"}
    datos.update(kwargs)
    return Categoria.objects.create(**datos)


def crear_producto(categoria, **kwargs):
    datos = {
        "categoria": categoria,
        "nombre": "Producto Pedidos Test",
        "slug": "producto-pedidos-test",
        "unidad_venta": "unidad",
        "precio": 1000,
        "activo": True,
        "disponible": True,
    }
    datos.update(kwargs)
    return Producto.objects.create(**datos)


def fecha_valida(dias_extra=0):
    config = ConfiguracionNegocio.get_solo()
    return (date.today() + timedelta(days=config.dias_anticipacion_pedido + dias_extra)).isoformat()


class CarritoTests(TestCase):
    def setUp(self):
        self.usuario = crear_usuario()
        self.client.login(username="cliente", password="clave-valida-123")
        self.categoria = crear_categoria()

    def test_agregar_producto_sin_variante(self):
        producto = crear_producto(self.categoria)
        respuesta = self.client.post(reverse("pedidos:carrito_agregar", args=[producto.pk]), {"cantidad": 2})
        self.assertRedirects(respuesta, reverse("pedidos:carrito"))
        respuesta = self.client.get(reverse("pedidos:carrito"))
        self.assertEqual(len(respuesta.context["lineas"]), 1)
        self.assertEqual(respuesta.context["lineas"][0].cantidad, 2)

    def test_agregar_producto_con_variante(self):
        producto = crear_producto(self.categoria, slug="producto-variante-test", precio=None)
        variante = VarianteProducto.objects.create(producto=producto, nombre="Chica", precio=500)
        respuesta = self.client.post(
            reverse("pedidos:carrito_agregar", args=[producto.pk]), {"variante_id": variante.pk, "cantidad": 1}
        )
        self.assertRedirects(respuesta, reverse("pedidos:carrito"))
        respuesta = self.client.get(reverse("pedidos:carrito"))
        linea = respuesta.context["lineas"][0]
        self.assertEqual(linea.variante, variante)
        self.assertEqual(linea.precio_unitario, 500)

    def test_producto_con_variantes_requiere_variante(self):
        producto = crear_producto(self.categoria, slug="sin-variante-elegida-test", precio=None)
        VarianteProducto.objects.create(producto=producto, nombre="Chica", precio=500)
        respuesta = self.client.post(reverse("pedidos:carrito_agregar", args=[producto.pk]), {"cantidad": 1})
        respuesta = self.client.get(reverse("pedidos:carrito"))
        self.assertEqual(len(respuesta.context["lineas"]), 0)

    def test_variante_de_otro_producto_no_se_acepta(self):
        producto1 = crear_producto(self.categoria, slug="producto-uno-var-test", precio=None)
        producto2 = crear_producto(self.categoria, slug="producto-dos-var-test", precio=None)
        variante_ajena = VarianteProducto.objects.create(producto=producto2, nombre="Chica", precio=500)
        self.client.post(
            reverse("pedidos:carrito_agregar", args=[producto1.pk]), {"variante_id": variante_ajena.pk, "cantidad": 1}
        )
        respuesta = self.client.get(reverse("pedidos:carrito"))
        self.assertEqual(len(respuesta.context["lineas"]), 0)

    def test_aumentar_cantidad(self):
        producto = crear_producto(self.categoria)
        self.client.post(reverse("pedidos:carrito_agregar", args=[producto.pk]), {"cantidad": 1})
        respuesta = self.client.get(reverse("pedidos:carrito"))
        clave = respuesta.context["lineas"][0].clave
        self.client.post(reverse("pedidos:carrito_actualizar", args=[clave]), {"cantidad": 5})
        respuesta = self.client.get(reverse("pedidos:carrito"))
        self.assertEqual(respuesta.context["lineas"][0].cantidad, 5)

    def test_disminuir_cantidad(self):
        producto = crear_producto(self.categoria)
        self.client.post(reverse("pedidos:carrito_agregar", args=[producto.pk]), {"cantidad": 5})
        respuesta = self.client.get(reverse("pedidos:carrito"))
        clave = respuesta.context["lineas"][0].clave
        self.client.post(reverse("pedidos:carrito_actualizar", args=[clave]), {"cantidad": 2})
        respuesta = self.client.get(reverse("pedidos:carrito"))
        self.assertEqual(respuesta.context["lineas"][0].cantidad, 2)

    def test_eliminar_linea(self):
        producto = crear_producto(self.categoria)
        self.client.post(reverse("pedidos:carrito_agregar", args=[producto.pk]), {"cantidad": 1})
        respuesta = self.client.get(reverse("pedidos:carrito"))
        clave = respuesta.context["lineas"][0].clave
        self.client.post(reverse("pedidos:carrito_eliminar", args=[clave]))
        respuesta = self.client.get(reverse("pedidos:carrito"))
        self.assertEqual(len(respuesta.context["lineas"]), 0)

    def test_vaciar_carrito(self):
        producto = crear_producto(self.categoria)
        self.client.post(reverse("pedidos:carrito_agregar", args=[producto.pk]), {"cantidad": 3})
        self.client.post(reverse("pedidos:carrito_vaciar"))
        respuesta = self.client.get(reverse("pedidos:carrito"))
        self.assertEqual(len(respuesta.context["lineas"]), 0)

    def test_cantidad_invalida_no_modifica_carrito(self):
        producto = crear_producto(self.categoria)
        respuesta = self.client.post(reverse("pedidos:carrito_agregar", args=[producto.pk]), {"cantidad": "abc"})
        respuesta = self.client.get(reverse("pedidos:carrito"))
        self.assertEqual(len(respuesta.context["lineas"]), 0)

    def test_cantidad_cero_no_modifica_carrito(self):
        producto = crear_producto(self.categoria)
        self.client.post(reverse("pedidos:carrito_agregar", args=[producto.pk]), {"cantidad": 0})
        respuesta = self.client.get(reverse("pedidos:carrito"))
        self.assertEqual(len(respuesta.context["lineas"]), 0)

    def test_producto_inactivo_no_se_puede_agregar(self):
        producto = crear_producto(self.categoria, slug="inactivo-agregar-test", activo=False)
        self.client.post(reverse("pedidos:carrito_agregar", args=[producto.pk]), {"cantidad": 1})
        respuesta = self.client.get(reverse("pedidos:carrito"))
        self.assertEqual(len(respuesta.context["lineas"]), 0)

    def test_variante_inactiva_no_se_puede_agregar(self):
        producto = crear_producto(self.categoria, slug="var-inactiva-agregar-test", precio=None)
        variante = VarianteProducto.objects.create(producto=producto, nombre="Vieja", precio=500, activo=False)
        self.client.post(
            reverse("pedidos:carrito_agregar", args=[producto.pk]), {"variante_id": variante.pk, "cantidad": 1}
        )
        respuesta = self.client.get(reverse("pedidos:carrito"))
        self.assertEqual(len(respuesta.context["lineas"]), 0)

    def test_producto_inactivo_se_elimina_del_carrito_si_ya_estaba(self):
        producto = crear_producto(self.categoria, slug="se-desactiva-test")
        self.client.post(reverse("pedidos:carrito_agregar", args=[producto.pk]), {"cantidad": 1})
        producto.activo = False
        producto.save(update_fields=["activo"])
        respuesta = self.client.get(reverse("pedidos:carrito"))
        self.assertEqual(len(respuesta.context["lineas"]), 0)

    def test_variante_inactiva_se_elimina_del_carrito_si_ya_estaba(self):
        producto = crear_producto(self.categoria, slug="var-se-desactiva-test", precio=None)
        variante = VarianteProducto.objects.create(producto=producto, nombre="Chica", precio=500)
        self.client.post(
            reverse("pedidos:carrito_agregar", args=[producto.pk]), {"variante_id": variante.pk, "cantidad": 1}
        )
        variante.activo = False
        variante.save(update_fields=["activo"])
        respuesta = self.client.get(reverse("pedidos:carrito"))
        self.assertEqual(len(respuesta.context["lineas"]), 0)

    def test_producto_no_disponible_aparece_marcado(self):
        producto = crear_producto(self.categoria, slug="no-disponible-carrito-test")
        self.client.post(reverse("pedidos:carrito_agregar", args=[producto.pk]), {"cantidad": 1})
        producto.disponible = False
        producto.save(update_fields=["disponible"])
        respuesta = self.client.get(reverse("pedidos:carrito"))
        self.assertEqual(len(respuesta.context["lineas"]), 1)
        self.assertTrue(respuesta.context["hay_no_disponibles"])
        self.assertContains(respuesta, "No disponible")

    def test_producto_no_disponible_bloquea_checkout(self):
        producto = crear_producto(self.categoria, slug="no-disponible-checkout-test")
        self.client.post(reverse("pedidos:carrito_agregar", args=[producto.pk]), {"cantidad": 1})
        producto.disponible = False
        producto.save(update_fields=["disponible"])
        respuesta = self.client.get(reverse("pedidos:checkout"))
        self.assertRedirects(respuesta, reverse("pedidos:carrito"))
        self.assertEqual(Pedido.objects.count(), 0)

    def test_precio_sin_variante_coincide_con_producto(self):
        producto = crear_producto(self.categoria, precio=1234)
        self.client.post(reverse("pedidos:carrito_agregar", args=[producto.pk]), {"cantidad": 1})
        respuesta = self.client.get(reverse("pedidos:carrito"))
        self.assertEqual(respuesta.context["lineas"][0].precio_unitario, producto.precio)

    def test_precio_con_variante_coincide_con_variante(self):
        producto = crear_producto(self.categoria, slug="precio-variante-test", precio=None)
        variante = VarianteProducto.objects.create(producto=producto, nombre="Grande", precio=777)
        self.client.post(
            reverse("pedidos:carrito_agregar", args=[producto.pk]), {"variante_id": variante.pk, "cantidad": 1}
        )
        respuesta = self.client.get(reverse("pedidos:carrito"))
        self.assertEqual(respuesta.context["lineas"][0].precio_unitario, variante.precio)

    def test_precio_manipulado_por_post_no_afecta_precio_real(self):
        producto = crear_producto(self.categoria, precio=1000)
        # El form de agregar no acepta un campo "precio": aunque se lo mande, se ignora.
        self.client.post(
            reverse("pedidos:carrito_agregar", args=[producto.pk]), {"cantidad": 1, "precio": "1"}
        )
        respuesta = self.client.get(reverse("pedidos:carrito"))
        self.assertEqual(respuesta.context["lineas"][0].precio_unitario, 1000)


class CheckoutTests(TestCase):
    def setUp(self):
        self.usuario = crear_usuario()
        self.client.login(username="cliente", password="clave-valida-123")
        self.categoria = crear_categoria()

    def _agregar_producto(self, **kwargs):
        producto = crear_producto(self.categoria, **kwargs)
        self.client.post(reverse("pedidos:carrito_agregar", args=[producto.pk]), {"cantidad": 1})
        return producto

    def _datos_checkout(self, **overrides):
        datos = {
            "nombre": "Ana",
            "apellido": "Test",
            "telefono": "111222333",
            "tipo_entrega": "retiro",
            "direccion_envio": "",
            "fecha_pedido": fecha_valida(),
            "observaciones": "",
        }
        datos.update(overrides)
        return datos

    def test_carrito_vacio_redirige(self):
        respuesta = self.client.get(reverse("pedidos:checkout"))
        self.assertRedirects(respuesta, reverse("pedidos:carrito"))

    def test_anonimo_puede_acceder_al_checkout(self):
        self.client.logout()
        self._agregar_producto()
        respuesta = self.client.get(reverse("pedidos:checkout"))
        self.assertEqual(respuesta.status_code, 200)

    def test_anonimo_completa_pedido_y_puede_verlo(self):
        self.client.logout()
        self._agregar_producto()
        datos = self._datos_checkout()
        respuesta = self.client.post(reverse("pedidos:checkout"), datos)
        pedido = Pedido.objects.get()
        self.assertIsNone(pedido.usuario)
        self.assertRedirects(respuesta, reverse("pedidos:pedido_detalle", args=[pedido.pk]))
        respuesta_detalle = self.client.get(reverse("pedidos:pedido_detalle", args=[pedido.pk]))
        self.assertEqual(respuesta_detalle.status_code, 200)

    def test_fecha_inferior_al_minimo_da_error(self):
        self._agregar_producto()
        datos = self._datos_checkout(fecha_pedido=date.today().isoformat())
        respuesta = self.client.post(reverse("pedidos:checkout"), datos)
        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(respuesta.context["form"].errors)
        self.assertEqual(Pedido.objects.count(), 0)

    def test_fecha_valida_permite_continuar(self):
        self._agregar_producto()
        datos = self._datos_checkout()
        respuesta = self.client.post(reverse("pedidos:checkout"), datos)
        self.assertEqual(Pedido.objects.count(), 1)
        self.assertRedirects(respuesta, reverse("pedidos:pedido_detalle", args=[Pedido.objects.first().pk]))

    def test_envio_sin_direccion_da_error(self):
        self._agregar_producto()
        datos = self._datos_checkout(tipo_entrega="envio", direccion_envio="")
        respuesta = self.client.post(reverse("pedidos:checkout"), datos)
        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(respuesta.context["form"].errors)
        self.assertEqual(Pedido.objects.count(), 0)

    def test_retiro_sin_direccion_funciona(self):
        self._agregar_producto()
        datos = self._datos_checkout(tipo_entrega="retiro", direccion_envio="")
        respuesta = self.client.post(reverse("pedidos:checkout"), datos)
        self.assertEqual(Pedido.objects.count(), 1)

    def test_envio_usa_costo_de_envio_correctamente(self):
        config = ConfiguracionNegocio.get_solo()
        config.envio_habilitado = True
        config.costo_envio = 500
        config.envio_gratis_desde = None
        config.save()
        producto = self._agregar_producto(precio=1000)
        datos = self._datos_checkout(tipo_entrega="envio", direccion_envio="Calle Falsa 123")
        self.client.post(reverse("pedidos:checkout"), datos)
        pedido = Pedido.objects.get()
        self.assertEqual(pedido.total, 1500)

    def test_envio_gratis_sobre_el_umbral(self):
        config = ConfiguracionNegocio.get_solo()
        config.envio_habilitado = True
        config.costo_envio = 500
        config.envio_gratis_desde = 900
        config.save()
        self._agregar_producto(precio=1000)
        datos = self._datos_checkout(tipo_entrega="envio", direccion_envio="Calle Falsa 123")
        self.client.post(reverse("pedidos:checkout"), datos)
        pedido = Pedido.objects.get()
        self.assertEqual(pedido.total, 1000)

    def test_sin_umbral_de_envio_gratis_no_aplica_descuento(self):
        config = ConfiguracionNegocio.get_solo()
        config.envio_habilitado = True
        config.costo_envio = 500
        config.envio_gratis_desde = None
        config.save()
        self._agregar_producto(precio=10000)
        datos = self._datos_checkout(tipo_entrega="envio", direccion_envio="Calle Falsa 123")
        self.client.post(reverse("pedidos:checkout"), datos)
        pedido = Pedido.objects.get()
        self.assertEqual(pedido.total, 10500)

    def test_envio_deshabilitado_no_permite_seleccionarse(self):
        config = ConfiguracionNegocio.get_solo()
        config.envio_habilitado = False
        config.save()
        self._agregar_producto()
        respuesta = self.client.get(reverse("pedidos:checkout"))
        opciones = [valor for valor, _ in respuesta.context["form"].fields["tipo_entrega"].choices]
        self.assertNotIn("envio", opciones)


class CreacionPedidoTests(TestCase):
    def setUp(self):
        self.usuario = crear_usuario()
        self.client.login(username="cliente", password="clave-valida-123")
        self.categoria = crear_categoria()

    def test_crea_pedido_e_item_con_datos_correctos(self):
        producto = crear_producto(self.categoria, precio=1500)
        self.client.post(reverse("pedidos:carrito_agregar", args=[producto.pk]), {"cantidad": 3})
        datos = {
            "nombre": "Ana", "apellido": "Test", "telefono": "111222333",
            "tipo_entrega": "retiro", "direccion_envio": "", "fecha_pedido": fecha_valida(), "observaciones": "obs",
        }
        self.client.post(reverse("pedidos:checkout"), datos)

        pedido = Pedido.objects.get()
        self.assertEqual(pedido.usuario, self.usuario)
        self.assertEqual(pedido.estado, Pedido.Estado.PENDIENTE)
        self.assertEqual(pedido.total, 4500)

        item = ItemPedido.objects.get(pedido=pedido)
        self.assertEqual(item.producto, producto)
        self.assertEqual(item.cantidad, 3)
        self.assertEqual(item.precio_unitario, 1500)
        self.assertEqual(item.nombre_producto, "Producto Pedidos Test")
        self.assertEqual(item.nombre_variante, "")
        self.assertEqual(item.subtotal, 4500)

    def test_carrito_se_vacia_despues_de_confirmar(self):
        producto = crear_producto(self.categoria)
        self.client.post(reverse("pedidos:carrito_agregar", args=[producto.pk]), {"cantidad": 1})
        datos = {
            "nombre": "Ana", "apellido": "Test", "telefono": "111222333",
            "tipo_entrega": "retiro", "direccion_envio": "", "fecha_pedido": fecha_valida(), "observaciones": "",
        }
        self.client.post(reverse("pedidos:checkout"), datos)
        respuesta = self.client.get(reverse("pedidos:carrito"))
        self.assertEqual(len(respuesta.context["lineas"]), 0)

    def test_snapshot_de_nombre_y_precio_no_cambia_si_se_edita_el_producto_despues(self):
        producto = crear_producto(self.categoria, nombre="Nombre Original", precio=1000)
        self.client.post(reverse("pedidos:carrito_agregar", args=[producto.pk]), {"cantidad": 1})
        datos = {
            "nombre": "Ana", "apellido": "Test", "telefono": "111222333",
            "tipo_entrega": "retiro", "direccion_envio": "", "fecha_pedido": fecha_valida(), "observaciones": "",
        }
        self.client.post(reverse("pedidos:checkout"), datos)
        item = ItemPedido.objects.get()

        producto.nombre = "Nombre Cambiado"
        producto.precio = 9999
        producto.save()

        item.refresh_from_db()
        self.assertEqual(item.nombre_producto, "Nombre Original")
        self.assertEqual(item.precio_unitario, 1000)

    def test_snapshot_de_variante_no_cambia_si_se_edita_despues(self):
        producto = crear_producto(self.categoria, slug="snapshot-variante-test", precio=None)
        variante = VarianteProducto.objects.create(producto=producto, nombre="Cocinadas", precio=500)
        self.client.post(
            reverse("pedidos:carrito_agregar", args=[producto.pk]), {"variante_id": variante.pk, "cantidad": 1}
        )
        datos = {
            "nombre": "Ana", "apellido": "Test", "telefono": "111222333",
            "tipo_entrega": "retiro", "direccion_envio": "", "fecha_pedido": fecha_valida(), "observaciones": "",
        }
        self.client.post(reverse("pedidos:checkout"), datos)
        item = ItemPedido.objects.get()

        variante.nombre = "Nombre Cambiado"
        variante.precio = 8888
        variante.save()

        item.refresh_from_db()
        self.assertEqual(item.nombre_variante, "Cocinadas")
        self.assertEqual(item.precio_unitario, 500)

    def test_no_crea_pedido_si_hay_producto_no_disponible(self):
        producto = crear_producto(self.categoria)
        self.client.post(reverse("pedidos:carrito_agregar", args=[producto.pk]), {"cantidad": 1})
        producto.disponible = False
        producto.save(update_fields=["disponible"])
        datos = {
            "nombre": "Ana", "apellido": "Test", "telefono": "111222333",
            "tipo_entrega": "retiro", "direccion_envio": "", "fecha_pedido": fecha_valida(), "observaciones": "",
        }
        self.client.post(reverse("pedidos:checkout"), datos)
        self.assertEqual(Pedido.objects.count(), 0)


class MisPedidosTests(TestCase):
    def setUp(self):
        self.usuario = crear_usuario("cliente_a")
        self.otro_usuario = crear_usuario("cliente_b")
        self.categoria = crear_categoria()

    def _crear_pedido_para(self, usuario):
        return Pedido.objects.create(
            usuario=usuario, nombre="Test", apellido="Test", telefono="123",
            tipo_entrega=Pedido.TipoEntrega.RETIRO, fecha_pedido=date.today() + timedelta(days=1),
            estado=Pedido.Estado.PENDIENTE, total=1000,
        )

    def test_usuario_ve_solamente_sus_pedidos(self):
        propio = self._crear_pedido_para(self.usuario)
        self._crear_pedido_para(self.otro_usuario)
        self.client.login(username="cliente_a", password="clave-valida-123")
        respuesta = self.client.get(reverse("pedidos:mis_pedidos"))
        pedidos_mostrados = list(respuesta.context["pedidos"])
        self.assertEqual(pedidos_mostrados, [propio])

    def test_usuario_puede_abrir_su_pedido(self):
        pedido = self._crear_pedido_para(self.usuario)
        self.client.login(username="cliente_a", password="clave-valida-123")
        respuesta = self.client.get(reverse("pedidos:pedido_detalle", args=[pedido.pk]))
        self.assertEqual(respuesta.status_code, 200)

    def test_usuario_no_puede_abrir_pedido_de_otro(self):
        pedido_ajeno = self._crear_pedido_para(self.otro_usuario)
        self.client.login(username="cliente_a", password="clave-valida-123")
        respuesta = self.client.get(reverse("pedidos:pedido_detalle", args=[pedido_ajeno.pk]))
        self.assertEqual(respuesta.status_code, 404)

    def test_anonimo_redirige_al_login_en_mis_pedidos(self):
        respuesta = self.client.get(reverse("pedidos:mis_pedidos"))
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn(reverse("usuarios:login"), respuesta.url)

    def test_anonimo_no_puede_ver_pedido_ajeno_por_pk(self):
        pedido = self._crear_pedido_para(self.usuario)
        respuesta = self.client.get(reverse("pedidos:pedido_detalle", args=[pedido.pk]))
        self.assertEqual(respuesta.status_code, 404)


class WhatsAppTests(TestCase):
    def setUp(self):
        self.usuario = crear_usuario()
        self.client.login(username="cliente", password="clave-valida-123")
        self.categoria = crear_categoria()
        self.config = ConfiguracionNegocio.get_solo()
        self.config.whatsapp_numero = "5493790001234"
        self.config.save()

    def _crear_pedido_con_item(self, **kwargs):
        producto = crear_producto(self.categoria, **kwargs)
        pedido = Pedido.objects.create(
            usuario=self.usuario, nombre="Ana", apellido="Test", telefono="111222333",
            tipo_entrega=Pedido.TipoEntrega.RETIRO, fecha_pedido=date.today() + timedelta(days=1),
            estado=Pedido.Estado.PENDIENTE, total=producto.precio * 2,
        )
        ItemPedido.objects.create(
            pedido=pedido, producto=producto, nombre_producto=producto.nombre,
            cantidad=2, precio_unitario=producto.precio,
        )
        return pedido, producto

    def test_detalle_de_pedido_incluye_enlace_de_whatsapp(self):
        pedido, _ = self._crear_pedido_con_item()
        respuesta = self.client.get(reverse("pedidos:pedido_detalle", args=[pedido.pk]))
        self.assertContains(respuesta, "wa.me/5493790001234")

    def test_enlace_usa_el_numero_configurado(self):
        self.config.whatsapp_numero = "5493795559999"
        self.config.save()
        pedido, _ = self._crear_pedido_con_item()
        respuesta = self.client.get(reverse("pedidos:pedido_detalle", args=[pedido.pk]))
        self.assertContains(respuesta, "wa.me/5493795559999")

    def test_mensaje_incluye_nombre_producto_y_cantidad(self):
        pedido, producto = self._crear_pedido_con_item(nombre="Producto WhatsApp Test")
        mensaje = whatsapp.construir_mensaje(pedido)
        self.assertIn("Producto WhatsApp Test", mensaje)
        self.assertIn("2 x", mensaje)

    def test_mensaje_incluye_variante_cuando_corresponde(self):
        producto = crear_producto(self.categoria, slug="whatsapp-variante-test", precio=None)
        variante = VarianteProducto.objects.create(producto=producto, nombre="Cocinadas", precio=200)
        pedido = Pedido.objects.create(
            usuario=self.usuario, nombre="Ana", apellido="Test", telefono="111",
            tipo_entrega=Pedido.TipoEntrega.RETIRO, fecha_pedido=date.today() + timedelta(days=1),
            estado=Pedido.Estado.PENDIENTE, total=200,
        )
        ItemPedido.objects.create(
            pedido=pedido, producto=producto, variante=variante,
            nombre_producto=producto.nombre, nombre_variante=variante.nombre,
            cantidad=1, precio_unitario=variante.precio,
        )
        mensaje = whatsapp.construir_mensaje(pedido)
        self.assertIn("Cocinadas", mensaje)

    def test_mensaje_incluye_total_y_numero_de_pedido(self):
        pedido, _ = self._crear_pedido_con_item()
        mensaje = whatsapp.construir_mensaje(pedido)
        self.assertIn(f"Pedido #{pedido.pk}", mensaje)
        self.assertIn(str(pedido.total), mensaje)

    def test_mensaje_incluye_direccion_solo_si_hay_envio(self):
        producto = crear_producto(self.categoria, slug="whatsapp-envio-test")
        pedido = Pedido.objects.create(
            usuario=self.usuario, nombre="Ana", apellido="Test", telefono="111",
            tipo_entrega=Pedido.TipoEntrega.ENVIO, direccion_envio="Calle Falsa 123",
            fecha_pedido=date.today() + timedelta(days=1),
            estado=Pedido.Estado.PENDIENTE, total=producto.precio,
        )
        ItemPedido.objects.create(
            pedido=pedido, producto=producto, nombre_producto=producto.nombre,
            cantidad=1, precio_unitario=producto.precio,
        )
        mensaje = whatsapp.construir_mensaje(pedido)
        self.assertIn("Calle Falsa 123", mensaje)

    def test_url_esta_correctamente_codificada(self):
        pedido, _ = self._crear_pedido_con_item()
        url = whatsapp.construir_url(pedido)
        self.assertTrue(url.startswith("https://wa.me/5493790001234?text="))
        self.assertNotIn(" ", url)
        self.assertNotIn("\n", url)

    def test_otro_usuario_no_puede_ver_el_enlace_de_un_pedido_ajeno(self):
        pedido, _ = self._crear_pedido_con_item()
        self.client.logout()
        crear_usuario("otro_cliente_whatsapp")
        self.client.login(username="otro_cliente_whatsapp", password="clave-valida-123")
        respuesta = self.client.get(reverse("pedidos:pedido_detalle", args=[pedido.pk]))
        self.assertEqual(respuesta.status_code, 404)
