from rest_framework import permissions

class IsAdmin(permissions.BasePermission):
    """
    Permiso para verificar si el usuario es administrador.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        from .models import Admin
        try:
            admin = Admin.objects.get(id=request.user.id)
            request.admin = admin
            return True
        except Admin.DoesNotExist:
            return False

class IsAdminOrProfesorForWrite(permissions.BasePermission):
    """
    Permite lectura a cualquiera (incluso no autenticado),
    pero escritura solo a admin o profesor autenticado.
    """
    def has_permission(self, request, view):
        # Permitir métodos seguros (GET, HEAD, OPTIONS) a cualquiera
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Para métodos de escritura, requiere autenticación
        if not request.user or not request.user.is_authenticated:
            return False
        
        user_id = request.user.id
        
        from .models import Admin, Profesor
        
        # Verificar si es admin
        try:
            admin = Admin.objects.get(id=user_id)
            request.admin = admin
            return True
        except Admin.DoesNotExist:
            pass
        
        # Verificar si es profesor
        try:
            profesor = Profesor.objects.get(id=user_id)
            request.profesor = profesor
            return True
        except Profesor.DoesNotExist:
            pass
        
        return False

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permiso que permite lectura a cualquier usuario autenticado,
    pero solo admin puede crear, actualizar o eliminar.
    """
    def has_permission(self, request, view):
        # Permitir siempre métodos seguros (GET, HEAD, OPTIONS)
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # Para métodos de escritura, verificar que sea admin
        return IsAdmin().has_permission(request, view)