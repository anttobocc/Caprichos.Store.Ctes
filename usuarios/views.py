from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.urls import reverse_lazy
from django.shortcuts import redirect, render

from .forms import PerfilForm, RegistroForm

LOGIN_URL_CLIENTE = "usuarios:login"


class ClienteLoginView(LoginView):
    template_name = "usuarios/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy("usuarios:perfil")


class ClienteLogoutView(LogoutView):
    next_page = reverse_lazy("usuarios:login")


class ClientePasswordChangeView(PasswordChangeView):
    template_name = "usuarios/password_change_form.html"
    success_url = reverse_lazy("usuarios:password_change_done")
    login_url = reverse_lazy("usuarios:login")


def registro(request):
    if request.user.is_authenticated:
        return redirect("usuarios:perfil")

    if request.method == "POST":
        form = RegistroForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            auth_login(request, usuario)
            messages.success(request, "¡Cuenta creada correctamente! Ya podés hacer tu pedido.")
            return redirect("usuarios:perfil")
    else:
        form = RegistroForm()
    return render(request, "usuarios/registro.html", {"form": form})


@login_required(login_url=LOGIN_URL_CLIENTE)
def perfil(request):
    return render(request, "usuarios/perfil.html", {"perfil": request.user.perfil})


@login_required(login_url=LOGIN_URL_CLIENTE)
def perfil_editar(request):
    if request.method == "POST":
        form = PerfilForm(request.POST, instance=request.user.perfil, usuario=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Tus datos se actualizaron correctamente.")
            return redirect("usuarios:perfil")
    else:
        form = PerfilForm(instance=request.user.perfil, usuario=request.user)
    return render(request, "usuarios/perfil_form.html", {"form": form})


@login_required(login_url=LOGIN_URL_CLIENTE)
def password_change_done(request):
    return render(request, "usuarios/password_change_done.html")
