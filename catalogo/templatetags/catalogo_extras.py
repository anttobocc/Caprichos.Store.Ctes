"""Filtros de presentación para nombres de producto.

Estos filtros NUNCA tocan el valor almacenado en la base de datos: solo
recortan el texto que se muestra en pantalla cuando la categoría del
producto ya es evidente por el contexto (encabezado de grupo, breadcrumb,
etc.). Si el nombre del producto no empieza con el nombre de su categoría
(en singular o plural), se devuelve el nombre completo sin modificar, para
que el helper sea seguro con categorías/productos nuevos que no sigan la
convención "Categoría de algo".
"""
from django import template

register = template.Library()

_CONECTORES = ("de la ", "de las ", "de los ", "del ", "de ")


def quitar_prefijo_categoria(nombre, categoria_nombre):
    if not nombre or not categoria_nombre:
        return nombre

    palabras = nombre.split()
    if not palabras:
        return nombre

    primera = palabras[0].lower()
    cat = categoria_nombre.strip().lower()
    candidatos = {cat, cat.rstrip("s"), cat + "s"}
    if primera not in candidatos:
        return nombre

    resto = " ".join(palabras[1:]).strip()
    if not resto:
        return nombre

    resto_lower = resto.lower()
    for conector in _CONECTORES:
        if resto_lower.startswith(conector):
            resto = resto[len(conector):]
            break

    resto = resto.strip()
    if not resto:
        return nombre

    return resto[0].upper() + resto[1:]


@register.filter
def nombre_sin_categoria(producto):
    """Nombre del producto sin repetir el nombre de su categoría.

    Uso: {{ producto|nombre_sin_categoria }} en un contexto donde la
    categoría ya se muestra aparte (encabezado de grupo, breadcrumb, etc.).
    No modifica producto.nombre; solo devuelve un string para mostrar.
    """
    categoria = getattr(producto, "categoria", None)
    if categoria is None:
        return getattr(producto, "nombre", producto)
    return quitar_prefijo_categoria(producto.nombre, categoria.nombre)
