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
from rest_framework import generics
from .permissions import IsAdmin

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

#codigo nuevo 25/03/2026

class UsuarioListCreateView(APIView):
    """Vista para listar y crear usuarios (solo admin)"""
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAdmin]
    
    def get(self, request):
        """Obtener todos los usuarios"""
        # Obtener todos los usuarios de los tres modelos
        alumnos = Alumno.objects.all().values('id', 'nombre', 'correo')
        profesores = Profesor.objects.all().values('id', 'nombre', 'correo')
        admins = Admin.objects.all().values('id', 'nombre', 'correo')
        
        # Combinar y agregar rol
        usuarios = []
        
        for a in alumnos:
            usuarios.append({
                'id': a['id'],
                'nombre': a['nombre'],
                'correo': a['correo'],
                'rol': 'student'
            })
        
        for p in profesores:
            usuarios.append({
                'id': p['id'],
                'nombre': p['nombre'],
                'correo': p['correo'],
                'rol': 'teacher'
            })
        
        for a in admins:
            usuarios.append({
                'id': a['id'],
                'nombre': a['nombre'],
                'correo': a['correo'],
                'rol': 'admin'
            })
        
        return Response(usuarios)
    
    def post(self, request):
        """Crear un nuevo usuario"""
        nombre = request.data.get('nombre')
        correo = request.data.get('correo')
        contrasena = request.data.get('contrasena')
        rol = request.data.get('rol')
        
        # Validaciones
        if not nombre or not correo or not contrasena or not rol:
            return Response({'message': 'Todos los campos son requeridos'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Validar que no exista el correo
        if (Alumno.objects.filter(correo=correo).exists() or 
            Profesor.objects.filter(correo=correo).exists() or
            Admin.objects.filter(correo=correo).exists()):
            return Response({'message': 'El correo ya está registrado'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Crear según rol
        try:
            if rol == 'student':
                user = Alumno.objects.create(
                    nombre=nombre, 
                    correo=correo, 
                    contrasena=contrasena
                )
            elif rol == 'teacher':
                user = Profesor.objects.create(
                    nombre=nombre, 
                    correo=correo, 
                    contrasena=contrasena
                )
            elif rol == 'admin':
                user = Admin.objects.create(
                    nombre=nombre, 
                    correo=correo, 
                    contrasena=contrasena
                )
            else:
                return Response({'message': 'Rol no válido'}, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({
                'id': user.id,
                'nombre': user.nombre,
                'correo': user.correo,
                'rol': rol
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({'message': f'Error al crear usuario: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

class UsuarioDetailView(APIView):
    """Vista para obtener, actualizar y eliminar un usuario específico (solo admin)"""
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAdmin]
    
    def get_user_and_role(self, pk):
        """Helper para obtener usuario y su rol"""
        try:
            user = Alumno.objects.get(id=pk)
            return user, 'student'
        except Alumno.DoesNotExist:
            try:
                user = Profesor.objects.get(id=pk)
                return user, 'teacher'
            except Profesor.DoesNotExist:
                try:
                    user = Admin.objects.get(id=pk)
                    return user, 'admin'
                except Admin.DoesNotExist:
                    raise NotFound('Usuario no encontrado')
    
    def get(self, request, pk):
        """Obtener un usuario específico"""
        user, role = self.get_user_and_role(pk)
        
        return Response({
            'id': user.id,
            'nombre': user.nombre,
            'correo': user.correo,
            'rol': role
        })
    
    def put(self, request, pk):
        """Actualizar un usuario"""
        user, role = self.get_user_and_role(pk)
        
        # Actualizar campos
        if 'nombre' in request.data:
            user.nombre = request.data['nombre']
        
        if 'correo' in request.data:
            new_email = request.data['correo']
            if new_email != user.correo:
                # Verificar que el nuevo correo no exista en otros usuarios
                email_exists = False
                
                if role != 'student' and Alumno.objects.filter(correo=new_email).exists():
                    email_exists = True
                elif role != 'teacher' and Profesor.objects.filter(correo=new_email).exists():
                    email_exists = True
                elif role != 'admin' and Admin.objects.filter(correo=new_email).exists():
                    email_exists = True
                
                if email_exists:
                    return Response({'message': 'El correo ya está en uso'}, status=status.HTTP_400_BAD_REQUEST)
                
                user.correo = new_email
        
        if 'contrasena' in request.data and request.data['contrasena']:
            user.contrasena = request.data['contrasena']
        
        user.save()
        
        return Response({
            'id': user.id,
            'nombre': user.nombre,
            'correo': user.correo,
            'rol': role
        })
    
    def delete(self, request, pk):
        """Eliminar un usuario"""
        user, role = self.get_user_and_role(pk)
        user.delete()
        return Response({'message': 'Usuario eliminado correctamente'}, status=status.HTTP_200_OK)