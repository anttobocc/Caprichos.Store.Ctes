from django.shortcuts import get_object_or_404, render

from .models import Categoria, Producto


def home(request):
    categorias = Categoria.objects.filter(activo=True)
    destacados = Producto.objects.filter(activo=True, destacado=True).select_related("categoria")
    return render(request, "catalogo/home.html", {"categorias": categorias, "destacados": destacados})


def lista_productos(request):
    productos = Producto.objects.filter(activo=True).select_related("categoria")
    categoria_slug = request.GET.get("categoria")
    categoria_actual = None
    if categoria_slug:
        categoria_actual = get_object_or_404(Categoria, slug=categoria_slug, activo=True)
        productos = productos.filter(categoria=categoria_actual)
    return render(request, "catalogo/productos_lista.html", {
        "productos": productos,
        "categorias": Categoria.objects.filter(activo=True),
        "categoria_actual": categoria_actual,
    })


def categoria_detalle(request, slug):
    categoria = get_object_or_404(Categoria, slug=slug, activo=True)
    productos = categoria.productos.filter(activo=True)
    return render(request, "catalogo/categoria_detalle.html", {"categoria": categoria, "productos": productos})


def producto_detalle(request, slug):
    producto = get_object_or_404(Producto.objects.select_related("categoria"), slug=slug, activo=True)
    variantes = producto.variantes.filter(activo=True) if producto.tiene_variantes else None
    return render(request, "catalogo/producto_detalle.html", {"producto": producto, "variantes": variantes})
