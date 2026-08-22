"""Control de acceso al panel administrativo.

No se usa un campo `rol`: "ser administrador" se resuelve enteramente con
`is_staff` (y el usuario debe además estar activo). `is_superuser` se deja
intacto como mecanismo propio de Django (acceso total a /admin/), sin
mezclarlo con esta condición.
"""
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def es_administrador(user):
    return user.is_authenticated and user.is_active and user.is_staff


def panel_admin_required(view_func):
    """No autenticado -> redirige a panel:login. Autenticado pero sin
    permisos (is_staff=False o is_active=False) -> 403, nunca lo deja pasar
    solo por estar logueado."""

    @login_required(login_url="panel:login")
    @wraps(view_func)
    def _envoltorio(request, *args, **kwargs):
        if not es_administrador(request.user):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return _envoltorio
