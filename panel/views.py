from django.contrib import messages
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, LogoutView
from django.db import models
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST

from catalogo.models import Categoria, Producto
from pedidos.models import Pedido

from .forms import (
    CategoriaForm,
    ConfiguracionNegocioForm,
    PedidoEstadoForm,
    ProductoForm,
    UsuarioCrearForm,
    UsuarioEditarForm,
    VarianteProductoFormSet,
)
from .models import ConfiguracionNegocio
from .permisos import panel_admin_required


class PanelLoginView(LoginView):
    template_name = "panel/login.html"
    redirect_authenticated_user = True


class PanelLogoutView(LogoutView):
    next_page = reverse_lazy("panel:login")


@panel_admin_required
def dashboard(request):
    contexto = {
        "total_productos": Producto.objects.count(),
        "total_categorias": Categoria.objects.count(),
        "total_usuarios": User.objects.count(),
        "total_pedidos": Pedido.objects.count(),
        "pedidos_recientes": Pedido.objects.order_by("-fecha_creacion")[:5],
    }
    return render(request, "panel/dashboard.html", contexto)


@panel_admin_required
def usuarios_lista(request):
    query = request.GET.get("q", "").strip()
    usuarios = User.objects.all().order_by("username")
    if query:
        usuarios = usuarios.filter(username__icontains=query)
    return render(request, "panel/usuarios_lista.html", {"usuarios": usuarios, "q": query})


@panel_admin_required
def usuario_crear(request):
    if request.method == "POST":
        form = UsuarioCrearForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Usuario creado correctamente.")
            return redirect("panel:usuarios")
    else:
        form = UsuarioCrearForm()
    return render(request, "panel/usuario_form.html", {"form": form, "modo": "crear"})


@panel_admin_required
def usuario_editar(request, pk):
    usuario = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        form = UsuarioEditarForm(request.POST, instance=usuario)
        if form.is_valid():
            es_uno_mismo = usuario.pk == request.user.pk
            if es_uno_mismo and not form.cleaned_data["is_staff"]:
                messages.error(request, "No podés quitarte tus propios permisos administrativos.")
                return render(request, "panel/usuario_form.html", {"form": form, "modo": "editar", "usuario": usuario})
            if es_uno_mismo and not form.cleaned_data["is_active"]:
                messages.error(request, "No podés desactivar tu propia cuenta.")
                return render(request, "panel/usuario_form.html", {"form": form, "modo": "editar", "usuario": usuario})
            form.save()
            messages.success(request, "Usuario actualizado correctamente.")
            return redirect("panel:usuarios")
    else:
        form = UsuarioEditarForm(instance=usuario)
    return render(request, "panel/usuario_form.html", {"form": form, "modo": "editar", "usuario": usuario})


@panel_admin_required
def usuario_password(request, pk):
    usuario = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        form = SetPasswordForm(usuario, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f'Contraseña de "{usuario.username}" actualizada correctamente.')
            return redirect("panel:usuarios")
    else:
        form = SetPasswordForm(usuario)
    return render(request, "panel/usuario_password.html", {"form": form, "usuario": usuario})


@panel_admin_required
def categorias_lista(request):
    query = request.GET.get("q", "").strip()
    categorias = Categoria.objects.order_by("orden", "nombre")
    if query:
        categorias = categorias.filter(nombre__icontains=query)
    return render(request, "panel/categorias_lista.html", {"categorias": categorias, "q": query})


@panel_admin_required
def categoria_crear(request):
    if request.method == "POST":
        form = CategoriaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Categoría creada correctamente.")
            return redirect("panel:categorias")
    else:
        form = CategoriaForm()
    return render(request, "panel/categoria_form.html", {"form": form, "modo": "crear"})


@panel_admin_required
def categoria_editar(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == "POST":
        form = CategoriaForm(request.POST, instance=categoria)
        if form.is_valid():
            form.save()
            messages.success(request, "Categoría actualizada correctamente.")
            return redirect("panel:categorias")
    else:
        form = CategoriaForm(instance=categoria)
    return render(request, "panel/categoria_form.html", {"form": form, "modo": "editar", "categoria": categoria})


@panel_admin_required
@require_POST
def categoria_toggle_activo(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    categoria.activo = request.POST.get("activo") == "on"
    categoria.save(update_fields=["activo"])
    estado = "activada" if categoria.activo else "desactivada"
    messages.success(request, f'"{categoria.nombre}" fue {estado}.')
    return redirect("panel:categorias")


def _variantes_activas(formset):
    """Variantes que quedarían activas tras guardar el formset (no marcadas
    para borrar y con activo=True)."""
    activas = []
    for form in formset.forms:
        if not form.cleaned_data:
            continue
        if form.cleaned_data.get("DELETE"):
            continue
        if form.cleaned_data.get("activo"):
            activas.append(form)
    return activas


def _validar_coherencia_precio(prod_form, formset):
    """Producto sin variantes activas -> precio obligatorio.
    Producto con variantes activas -> precio debe quedar vacío (error
    explícito si se cargó, nunca se limpia solo)."""
    precio = prod_form.cleaned_data.get("precio")
    hay_variantes_activas = bool(_variantes_activas(formset))
    if hay_variantes_activas and precio is not None:
        prod_form.add_error(
            "precio",
            "Un producto con variantes debe tener el precio del producto vacío.",
        )
        return False
    if not hay_variantes_activas and precio is None:
        prod_form.add_error(
            "precio",
            "Un producto sin variantes debe tener un precio.",
        )
        return False
    return True


@panel_admin_required
def productos_lista(request):
    query = request.GET.get("q", "").strip()
    productos = Producto.objects.select_related("categoria").order_by("nombre")
    if query:
        productos = productos.filter(nombre__icontains=query)
    return render(request, "panel/productos_lista.html", {"productos": productos, "q": query})


@panel_admin_required
def producto_crear(request):
    if request.method == "POST":
        prod_form = ProductoForm(request.POST, request.FILES)
        formset = VarianteProductoFormSet(request.POST, prefix="variantes")
        if prod_form.is_valid() and formset.is_valid():
            if _validar_coherencia_precio(prod_form, formset):
                producto = prod_form.save()
                formset.instance = producto
                formset.save()
                messages.success(request, "Producto creado correctamente.")
                return redirect("panel:productos")
    else:
        prod_form = ProductoForm()
        formset = VarianteProductoFormSet(prefix="variantes")
    return render(request, "panel/producto_form.html", {"form": prod_form, "formset": formset, "modo": "crear"})


@panel_admin_required
def producto_editar(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == "POST":
        prod_form = ProductoForm(request.POST, request.FILES, instance=producto)
        formset = VarianteProductoFormSet(request.POST, instance=producto, prefix="variantes")
        if prod_form.is_valid() and formset.is_valid():
            if _validar_coherencia_precio(prod_form, formset):
                prod_form.save()
                formset.save()
                messages.success(request, "Producto actualizado correctamente.")
                return redirect("panel:productos")
    else:
        prod_form = ProductoForm(instance=producto)
        formset = VarianteProductoFormSet(instance=producto, prefix="variantes")
    return render(request, "panel/producto_form.html", {
        "form": prod_form, "formset": formset, "modo": "editar", "producto": producto,
    })


@panel_admin_required
@require_POST
def producto_toggle_activo(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    producto.activo = request.POST.get("activo") == "on"
    producto.save(update_fields=["activo"])
    estado = "activado" if producto.activo else "desactivado"
    messages.success(request, f'"{producto.nombre}" fue {estado}.')
    return redirect("panel:productos")


@panel_admin_required
@require_POST
def producto_toggle_disponible(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    producto.disponible = request.POST.get("disponible") == "on"
    producto.save(update_fields=["disponible"])
    estado = "disponible" if producto.disponible else "no disponible"
    messages.success(request, f'"{producto.nombre}" quedó {estado}.')
    return redirect("panel:productos")


@panel_admin_required
@require_POST
def producto_toggle_destacado(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    producto.destacado = request.POST.get("destacado") == "on"
    producto.save(update_fields=["destacado"])
    estado = "destacado" if producto.destacado else "quitado de destacados"
    messages.success(request, f'"{producto.nombre}" quedó {estado}.')
    return redirect("panel:productos")


@panel_admin_required
def pedidos_lista(request):
    query = request.GET.get("q", "").strip()
    estado = request.GET.get("estado", "").strip()
    pedidos = Pedido.objects.order_by("-fecha_creacion")
    if query:
        pedidos = pedidos.filter(
            models.Q(nombre__icontains=query)
            | models.Q(apellido__icontains=query)
            | models.Q(telefono__icontains=query)
        )
    if estado:
        pedidos = pedidos.filter(estado=estado)
    return render(request, "panel/pedidos_lista.html", {
        "pedidos": pedidos,
        "q": query,
        "estado": estado,
        "estados": Pedido.Estado.choices,
    })


@panel_admin_required
def pedido_detalle(request, pk):
    pedido = get_object_or_404(Pedido.objects.select_related("usuario").prefetch_related("items"), pk=pk)
    items = list(pedido.items.all())
    subtotal = sum((item.subtotal for item in items), start=0)
    costo_envio = pedido.total - subtotal
    form = PedidoEstadoForm(instance=pedido)
    return render(request, "panel/pedido_detalle.html", {
        "pedido": pedido,
        "items": items,
        "subtotal": subtotal,
        "costo_envio": costo_envio,
        "form": form,
    })


@panel_admin_required
@require_POST
def pedido_cambiar_estado(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)
    form = PedidoEstadoForm(request.POST, instance=pedido)
    if form.is_valid():
        form.save()
        messages.success(request, f"El pedido #{pedido.pk} quedó en estado \"{pedido.get_estado_display()}\".")
    else:
        messages.error(request, "No se pudo actualizar el estado del pedido.")
    return redirect("panel:pedido_detalle", pk=pedido.pk)


@panel_admin_required
def configuracion(request):
    config = ConfiguracionNegocio.get_solo()
    if request.method == "POST":
        form = ConfiguracionNegocioForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, "Configuración actualizada correctamente.")
            return redirect("panel:configuracion")
    else:
        form = ConfiguracionNegocioForm(instance=config)
    return render(request, "panel/configuracion_form.html", {"form": form})
