from rest_framework import permissions
from .models import Admin, Profesor


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            isinstance(request.user, Admin)
        )


class IsAdminOrProfesorForWrite(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        return bool(
            request.user and
            request.user.is_authenticated and
            (
                isinstance(request.user, Admin) or
                isinstance(request.user, Profesor)
            )
        )


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)

        return bool(
            request.user and
            request.user.is_authenticated and
            isinstance(request.user, Admin)
        )


class IsAdminProfesorOwnerOrReadOnly(permissions.BasePermission):
    """
    GET/HEAD/OPTIONS: cualquiera
    POST: admin o profesor
    PUT/PATCH: admin o profesor dueño de la categoría
    DELETE: solo admin
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        if not request.user or not request.user.is_authenticated:
            return False

        if isinstance(request.user, Admin):
            return True

        if isinstance(request.user, Profesor):
            return request.method in ['POST', 'PUT', 'PATCH']

        return False

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        if isinstance(request.user, Admin):
            return True

        if isinstance(request.user, Profesor):
            if request.method in ['PUT', 'PATCH']:
                return obj.creada_por_profesor_id == request.user.id
            if request.method == 'DELETE':
                return False

        return False