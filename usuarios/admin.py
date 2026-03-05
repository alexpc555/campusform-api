from django.contrib import admin
from .models import Alumno, Profesor


class BaseUserAdmin(admin.ModelAdmin):
    """
    Admin base para Alumno/Profesor.
    Evita editar la contraseña ya hasheada desde el admin para no romperla.
    """
    list_display = ("id", "nombre", "correo")
    search_fields = ("nombre", "correo")
    list_filter = ()
    ordering = ("id",)
    list_per_page = 25

    # Cuando creas uno nuevo, sí deja capturar la contraseña.
    # Cuando editas, la muestra como solo lectura (ya hasheada).
    def get_readonly_fields(self, request, obj=None):
        if obj:  # editando
            return ("contrasena",)
        return ()

    fieldsets = (
        (None, {"fields": ("nombre", "correo", "contrasena")}),
    )


@admin.register(Alumno)
class AlumnoAdmin(BaseUserAdmin):
    pass


@admin.register(Profesor)
class ProfesorAdmin(BaseUserAdmin):
    pass