from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics, permissions
from rest_framework_simplejwt.tokens import RefreshToken
from .authentication import CustomJWTAuthentication
from rest_framework.exceptions import PermissionDenied, NotFound
from django.db.models import Count
from .serializers import RegisterSerializer, LoginSerializer, CategoriaSerializer
from .models import Alumno, Profesor, Admin, Categoria
from .permissions import IsAdmin, IsAdminOrReadOnly, IsAdminOrProfesorForWrite  # Agregué IsAdminOrProfesorForWrite

class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Determinar el rol del usuario creado
            if isinstance(user, Alumno):
                role = "student"
            elif isinstance(user, Profesor):
                role = "teacher"
            else:
                role = "admin"
            
            return Response(
                {
                    "message": "Usuario creado", 
                    "id": user.id,
                    "role": role
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            user_model = serializer.validated_data['user_model']
            
            # Generar tokens JWT
            refresh = RefreshToken()
            
            # Agregar información personalizada al token
            refresh['user_id'] = user.id
            refresh['name'] = user.nombre
            refresh['email'] = user.correo
            refresh['role'] = user_model
            
            access_token = refresh.access_token
            
            # Determinar la redirección según el rol
            if user_model == "student":
                redirect_url = "/dashboard"
            elif user_model == "teacher":
                redirect_url = "/profesor"
            else:  # admin
                redirect_url = "/admin"
            
            return Response({
                "message": "Login exitoso",
                "token": str(access_token),
                "refresh": str(refresh),
                "user": {
                    "id": user.id,
                    "name": user.nombre,
                    "email": user.correo,
                    "role": user_model
                },
                "redirect": redirect_url
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CategoriaListCreateView(generics.ListCreateAPIView):
    serializer_class = CategoriaSerializer
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAdminOrProfesorForWrite]  # Lectura pública, escritura restringida
    
    def get_queryset(self):
        return Categoria.objects.all().order_by('-fecha_creacion')
    
    def perform_create(self, serializer):
        user = getattr(self.request, 'admin', None) or getattr(self.request, 'profesor', None)
        if not user:
            raise PermissionDenied("Solo administradores o profesores pueden crear categorías")
        
        serializer.save(creada_por=user)

class CategoriaDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Vista para ver, actualizar y eliminar una categoría específica.
    - GET: Cualquier usuario autenticado puede ver
    - PUT/PATCH/DELETE: Solo admin puede modificar/eliminar
    """
    serializer_class = CategoriaSerializer
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAdminOrProfesorForWrite]
    
    def get_queryset(self):
        """
        Obtener categorías con conteo de posts.
        """
        try:
            return Categoria.objects.annotate(
                post_count=Count('posts')
            )
        except:
            return Categoria.objects.all()
    
    def perform_update(self, serializer):
        """
        Verificar que solo admin pueda actualizar.
        """
        admin = getattr(self.request, 'admin', None)
        if not admin:
            try:
                admin = Admin.objects.get(id=self.request.user.id)
            except Admin.DoesNotExist:
                raise PermissionDenied("Solo administradores pueden actualizar categorías")
        
        serializer.save()
    
    def perform_destroy(self, instance):
        """
        Verificar que solo admin pueda eliminar.
        """
        admin = getattr(self.request, 'admin', None)
        if not admin:
            try:
                admin = Admin.objects.get(id=self.request.user.id)
            except Admin.DoesNotExist:
                raise PermissionDenied("Solo administradores pueden eliminar categorías")
        
        instance.delete()