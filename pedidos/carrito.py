"""Carrito de compras basado en sesión de Django.

La sesión guarda únicamente identificadores y cantidades:

    {"<producto_id>:<variante_id o vacío>": cantidad}

El precio NUNCA se guarda en la sesión: Carrito.items() y Carrito.total()
siempre vuelven a consultar Producto/VarianteProducto en la base para
resolver el precio vigente. Esto es intencional (ver Etapa 4 y Etapa 5):
producto sin variantes -> Producto.precio; producto con variantes activas
-> VarianteProducto.precio; nunca una tercera fuente.

"activo" y "disponible" son conceptos distintos: un producto/variante
inactivo no puede permanecer en el carrito (se quita solo); un producto
"no disponible" sí permanece visible, pero bloquea el checkout.
"""
from catalogo.models import Producto, VarianteProducto

SESSION_KEY = "carrito"


def _clave(producto_id, variante_id):
    return f"{producto_id}:{variante_id or ''}"


class LineaCarrito:
    def __init__(self, clave, producto, variante, cantidad):
        self.clave = clave
        self.producto = producto
        self.variante = variante
        self.cantidad = cantidad

    @property
    def precio_unitario(self):
        return self.variante.precio if self.variante else self.producto.precio

    @property
    def subtotal(self):
        return self.precio_unitario * self.cantidad

    @property
    def disponible(self):
        return self.producto.disponible


class Carrito:
    def __init__(self, request):
        self.session = request.session

    def _datos(self):
        return self.session.setdefault(SESSION_KEY, {})

    def _guardar(self):
        self.session.modified = True

    def agregar(self, producto, variante=None, cantidad=1):
        """Agrega `cantidad` unidades de `producto`/`variante` al carrito.
        No valida activo/disponible: eso es responsabilidad de la vista,
        que ya tuvo que resolver `producto`/`variante` desde la base antes
        de llamar acá."""
        datos = self._datos()
        clave = _clave(producto.pk, variante.pk if variante else None)
        datos[clave] = datos.get(clave, 0) + cantidad
        self._guardar()

    def actualizar_cantidad(self, clave, cantidad):
        datos = self._datos()
        if clave not in datos:
            return
        if cantidad < 1:
            del datos[clave]
        else:
            datos[clave] = cantidad
        self._guardar()

    def eliminar(self, clave):
        datos = self._datos()
        if clave in datos:
            del datos[clave]
            self._guardar()

    def vaciar(self):
        self.session[SESSION_KEY] = {}
        self._guardar()

    def esta_vacio(self):
        return len(self._datos()) == 0

    def items(self, mensajes=None):
        """Devuelve la lista de LineaCarrito vigentes, resolviendo cada
        producto/variante contra la base de datos. Si un producto o su
        variante ya no existen o quedaron inactivos, se eliminan
        silenciosamente de la sesión (opcionalmente se agrega un aviso a
        `mensajes`, una lista donde la vista puede acumular textos para
        mostrar con el framework de mensajes)."""
        datos = self._datos()
        lineas = []
        claves_a_quitar = []

        for clave, cantidad in list(datos.items()):
            producto_id_str, _, variante_id_str = clave.partition(":")
            try:
                producto_id = int(producto_id_str)
            except ValueError:
                claves_a_quitar.append(clave)
                continue

            producto = Producto.objects.filter(pk=producto_id, activo=True).first()
            if producto is None:
                claves_a_quitar.append(clave)
                if mensajes is not None:
                    mensajes.append("Un producto de tu carrito ya no está disponible y fue quitado.")
                continue

            variante = None
            if variante_id_str:
                variante = VarianteProducto.objects.filter(
                    pk=variante_id_str, producto=producto, activo=True
                ).first()
                if variante is None:
                    claves_a_quitar.append(clave)
                    if mensajes is not None:
                        mensajes.append(
                            f'Una opción de "{producto.nombre}" ya no está disponible y fue quitada de tu carrito.'
                        )
                    continue

            lineas.append(LineaCarrito(clave, producto, variante, cantidad))

        if claves_a_quitar:
            for clave in claves_a_quitar:
                datos.pop(clave, None)
            self._guardar()

        return lineas

    def cantidad_total(self):
        return sum(linea.cantidad for linea in self.items())

    def total(self):
        return sum((linea.subtotal for linea in self.items()), start=0)

    def hay_no_disponibles(self):
        return any(not linea.disponible for linea in self.items())
