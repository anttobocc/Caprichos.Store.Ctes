from django.test import TestCase
from django.urls import reverse

from .models import Categoria, Producto, VarianteProducto


def crear_categoria(**kwargs):
    datos = {"nombre": "Categoría Test", "slug": "categoria-test", "activo": True}
    datos.update(kwargs)
    return Categoria.objects.create(**datos)


def crear_producto(categoria, **kwargs):
    datos = {
        "categoria": categoria,
        "nombre": "Producto Test",
        "slug": "producto-test",
        "unidad_venta": "unidad",
        "precio": 1000,
        "activo": True,
        "disponible": True,
    }
    datos.update(kwargs)
    return Producto.objects.create(**datos)


class CatalogoPublicoTests(TestCase):
    def test_home_carga(self):
        respuesta = self.client.get(reverse("catalogo:home"))
        self.assertEqual(respuesta.status_code, 200)

    def test_categoria_activa_aparece_en_home(self):
        crear_categoria(nombre="Dulces Test", slug="dulces-test")
        respuesta = self.client.get(reverse("catalogo:home"))
        self.assertContains(respuesta, "Dulces Test")

    def test_categoria_inactiva_no_aparece_en_home(self):
        crear_categoria(nombre="Oculta Test", slug="oculta-test", activo=False)
        respuesta = self.client.get(reverse("catalogo:home"))
        self.assertNotContains(respuesta, "Oculta Test")

    def test_categoria_inactiva_da_404_por_url_directa(self):
        crear_categoria(nombre="Oculta Test 2", slug="oculta-test-2", activo=False)
        respuesta = self.client.get(reverse("catalogo:categoria_detalle", args=["oculta-test-2"]))
        self.assertEqual(respuesta.status_code, 404)

    def test_categoria_inexistente_da_404(self):
        respuesta = self.client.get(reverse("catalogo:categoria_detalle", args=["no-existe"]))
        self.assertEqual(respuesta.status_code, 404)

    def test_producto_activo_disponible_aparece_en_listado(self):
        categoria = crear_categoria()
        crear_producto(categoria, nombre="Visible Test", slug="visible-test")
        respuesta = self.client.get(reverse("catalogo:productos"))
        self.assertContains(respuesta, "Visible Test")

    def test_producto_inactivo_no_aparece_en_listado(self):
        categoria = crear_categoria()
        crear_producto(categoria, nombre="Invisible Test", slug="invisible-test", activo=False)
        respuesta = self.client.get(reverse("catalogo:productos"))
        self.assertNotContains(respuesta, "Invisible Test")

    def test_producto_inactivo_da_404_en_detalle(self):
        categoria = crear_categoria()
        crear_producto(categoria, nombre="Invisible Test 2", slug="invisible-test-2", activo=False)
        respuesta = self.client.get(reverse("catalogo:producto_detalle", args=["invisible-test-2"]))
        self.assertEqual(respuesta.status_code, 404)

    def test_producto_no_disponible_se_marca_como_no_disponible(self):
        categoria = crear_categoria()
        crear_producto(categoria, nombre="Sin Stock Test", slug="sin-stock-test", disponible=False)
        respuesta = self.client.get(reverse("catalogo:producto_detalle", args=["sin-stock-test"]))
        self.assertContains(respuesta, "No disponible")

    def test_detalle_producto_sin_variantes_muestra_precio(self):
        categoria = crear_categoria()
        crear_producto(categoria, nombre="Sin Variantes Test", slug="sin-variantes-test", precio=1234)
        respuesta = self.client.get(reverse("catalogo:producto_detalle", args=["sin-variantes-test"]))
        self.assertContains(respuesta, "1234")

    def test_detalle_producto_con_variantes_muestra_cada_variante_activa(self):
        categoria = crear_categoria()
        producto = crear_producto(categoria, nombre="Con Variantes Test", slug="con-variantes-test", precio=None)
        VarianteProducto.objects.create(producto=producto, nombre="Cocinadas Test", precio=100)
        VarianteProducto.objects.create(producto=producto, nombre="Congeladas Test", precio=90)
        respuesta = self.client.get(reverse("catalogo:producto_detalle", args=["con-variantes-test"]))
        self.assertContains(respuesta, "Cocinadas Test")
        self.assertContains(respuesta, "Congeladas Test")

    def test_variante_inactiva_no_aparece_en_catalogo_publico(self):
        categoria = crear_categoria()
        producto = crear_producto(categoria, nombre="Producto Mixto", slug="producto-mixto", precio=None)
        VarianteProducto.objects.create(producto=producto, nombre="Variante Visible", precio=100)
        VarianteProducto.objects.create(producto=producto, nombre="Variante Descontinuada", precio=90, activo=False)
        respuesta = self.client.get(reverse("catalogo:producto_detalle", args=["producto-mixto"]))
        self.assertContains(respuesta, "Variante Visible")
        self.assertNotContains(respuesta, "Variante Descontinuada")

    def test_filtro_por_categoria_en_listado(self):
        categoria1 = crear_categoria(nombre="Cat Uno", slug="cat-uno")
        categoria2 = crear_categoria(nombre="Cat Dos", slug="cat-dos")
        crear_producto(categoria1, nombre="Producto Uno Test", slug="producto-uno-test")
        crear_producto(categoria2, nombre="Producto Dos Test", slug="producto-dos-test")
        respuesta = self.client.get(reverse("catalogo:productos"), {"categoria": "cat-uno"})
        self.assertContains(respuesta, "Producto Uno Test")
        self.assertNotContains(respuesta, "Producto Dos Test")

    def test_producto_destacado_aparece_en_home(self):
        categoria = crear_categoria()
        crear_producto(categoria, nombre="Destacado Test", slug="destacado-test", destacado=True)
        respuesta = self.client.get(reverse("catalogo:home"))
        self.assertContains(respuesta, "Destacado Test")

    def test_destacados_no_muestran_productos_inactivos(self):
        categoria = crear_categoria()
        crear_producto(categoria, nombre="Destacado Inactivo Test", slug="destacado-inactivo-test", destacado=True, activo=False)
        respuesta = self.client.get(reverse("catalogo:home"))
        self.assertNotContains(respuesta, "Destacado Inactivo Test")

    def test_categoria_inactiva_no_aparece_en_filtro_de_listado(self):
        crear_categoria(nombre="Categoria Filtro Oculta Test", slug="categoria-filtro-oculta-test", activo=False)
        respuesta = self.client.get(reverse("catalogo:productos"))
        self.assertNotContains(respuesta, "Categoria Filtro Oculta Test")

    def test_producto_no_disponible_aparece_en_listado_marcado(self):
        categoria = crear_categoria()
        crear_producto(categoria, nombre="No Disponible Listado Test", slug="no-disponible-listado-test", disponible=False)
        respuesta = self.client.get(reverse("catalogo:productos"))
        self.assertContains(respuesta, "No Disponible Listado Test")
        self.assertContains(respuesta, "No disponible")

    def test_desde_precio_usa_el_minimo_entre_variantes_activas(self):
        categoria = crear_categoria()
        producto = crear_producto(categoria, nombre="Precio Minimo Test", slug="precio-minimo-test", precio=None)
        VarianteProducto.objects.create(producto=producto, nombre="Cara", precio=500)
        VarianteProducto.objects.create(producto=producto, nombre="Barata", precio=100)
        VarianteProducto.objects.create(producto=producto, nombre="Mas barata pero inactiva", precio=1, activo=False)
        respuesta = self.client.get(reverse("catalogo:productos"))
        self.assertContains(respuesta, "Desde $100")
        self.assertNotContains(respuesta, "Desde $1.00")


class ProductoModeloTests(TestCase):
    def test_tiene_variantes_ignora_variantes_inactivas(self):
        categoria = crear_categoria()
        producto = crear_producto(categoria, precio=None)
        VarianteProducto.objects.create(producto=producto, nombre="Inactiva", precio=100, activo=False)
        self.assertFalse(producto.tiene_variantes)

    def test_tiene_variantes_true_con_al_menos_una_activa(self):
        categoria = crear_categoria()
        producto = crear_producto(categoria, precio=None)
        VarianteProducto.objects.create(producto=producto, nombre="Activa", precio=100, activo=True)
        self.assertTrue(producto.tiene_variantes)
