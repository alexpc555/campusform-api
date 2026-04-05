from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import PermissionDenied, NotFound
from django.db.models import Count

from .authentication import CustomJWTAuthentication
from .models import Alumno, Profesor, Admin, Categoria, Post, Comentario, Reporte
from .serializers import (
    RegisterSerializer, LoginSerializer, CategoriaSerializer,
    PostSerializer, ComentarioSerializer, ReporteSerializer
)
from .permissions import (
    IsAdmin, IsAdminOrReadOnly, IsAdminOrProfesorForWrite,
    IsAdminProfesorOwnerOrReadOnly
)

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
    permission_classes = [IsAdminProfesorOwnerOrReadOnly]

    def get_queryset(self):
        return Categoria.objects.all().order_by('-fecha_creacion')

    def perform_create(self, serializer):
        user = self.request.user

        if isinstance(user, Admin):
            serializer.save(creada_por_admin=user)
            return

        if isinstance(user, Profesor):
            serializer.save(creada_por_profesor=user)
            return

        raise PermissionDenied("Solo administradores o profesores pueden crear categorías")


class CategoriaDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CategoriaSerializer
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAdminProfesorOwnerOrReadOnly]

    def get_queryset(self):
        return Categoria.objects.all()

    def perform_update(self, serializer):
        categoria = self.get_object()
        user = self.request.user

        if isinstance(user, Admin):
            serializer.save()
            return

        if isinstance(user, Profesor) and categoria.creada_por_profesor_id == user.id:
            serializer.save()
            return

        raise PermissionDenied("No tienes permiso para actualizar esta categoría")

    def perform_destroy(self, instance):
        user = self.request.user

        if isinstance(user, Admin):
            instance.delete()
            return

        raise PermissionDenied("Solo administradores pueden eliminar categorías")
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

        #codigo nuevo 25/03/2026 -----------------------------------------------------------------------
    
class PostListCreateView(generics.ListCreateAPIView):
    """Vista para listar y crear publicaciones"""
    serializer_class = PostSerializer
    authentication_classes = [CustomJWTAuthentication]
    
    def get_queryset(self):
        queryset = Post.objects.all().annotate(
            comentarios_count=Count('comentarios')
        )
        
        categoria_id = self.request.query_params.get('categoria')
        if categoria_id:
            queryset = queryset.filter(categoria_id=categoria_id)
        
        return queryset.order_by('-fecha_creacion')
    
    def perform_create(self, serializer):
        user = self.request.user
        
        try:
            alumno = Alumno.objects.get(id=user.id)
            serializer.save(autor_alumno=alumno)
        except Alumno.DoesNotExist:
            try:
                profesor = Profesor.objects.get(id=user.id)
                serializer.save(autor_profesor=profesor)
            except Profesor.DoesNotExist:
                try:
                    admin = Admin.objects.get(id=user.id)
                    serializer.save(autor_admin=admin)
                except Admin.DoesNotExist:
                    raise PermissionDenied("Usuario no válido")

class MisPostsView(generics.ListAPIView):
    """Vista para obtener los posts del usuario autenticado"""
    serializer_class = PostSerializer
    authentication_classes = [CustomJWTAuthentication]
    
    def get_queryset(self):
        user = self.request.user
        
        try:
            alumno = Alumno.objects.get(id=user.id)
            return Post.objects.filter(autor_alumno=alumno).annotate(
                comentarios_count=Count('comentarios')
            ).order_by('-fecha_creacion')
        except Alumno.DoesNotExist:
            try:
                profesor = Profesor.objects.get(id=user.id)
                return Post.objects.filter(autor_profesor=profesor).annotate(
                    comentarios_count=Count('comentarios')
                ).order_by('-fecha_creacion')
            except Profesor.DoesNotExist:
                try:
                    admin = Admin.objects.get(id=user.id)
                    return Post.objects.filter(autor_admin=admin).annotate(
                        comentarios_count=Count('comentarios')
                    ).order_by('-fecha_creacion')
                except Admin.DoesNotExist:
                    return Post.objects.none()

class PostDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Vista para ver, actualizar y eliminar una publicación específica"""
    serializer_class = PostSerializer
    authentication_classes = [CustomJWTAuthentication]
    
    def get_queryset(self):
        return Post.objects.all().annotate(comentarios_count=Count('comentarios'))
    
    def get_object(self):
        obj = super().get_object()
        if self.request.method == 'GET':
            obj.vistas += 1
            obj.save()
        return obj
    
    def perform_update(self, serializer):
        user = self.request.user
        post = self.get_object()
        autor = post.autor
        
        if autor and autor.id == user.id:
            serializer.save()
        else:
            raise PermissionDenied("Solo el autor puede editar esta publicación")
    
    def perform_destroy(self, instance):
        user = self.request.user
        autor = instance.autor
        
        if autor and autor.id == user.id:
            instance.delete()
        else:
            try:
                Admin.objects.get(id=user.id)
                instance.delete()
            except Admin.DoesNotExist:
                raise PermissionDenied("No tienes permiso para eliminar esta publicación")

# ==================== VISTAS DE COMENTARIOS ====================
class ComentarioListCreateView(generics.ListCreateAPIView):
    """Vista para listar y crear comentarios"""
    serializer_class = ComentarioSerializer
    authentication_classes = [CustomJWTAuthentication]
    
    def get_queryset(self):
        queryset = Comentario.objects.all()
        post_id = self.request.query_params.get('post')
        if post_id:
            queryset = queryset.filter(post_id=post_id)
        return queryset.order_by('-fecha_creacion')
    
    def perform_create(self, serializer):
        user = self.request.user
        
        try:
            alumno = Alumno.objects.get(id=user.id)
            serializer.save(autor_alumno=alumno)
        except Alumno.DoesNotExist:
            try:
                profesor = Profesor.objects.get(id=user.id)
                serializer.save(autor_profesor=profesor)
            except Profesor.DoesNotExist:
                try:
                    admin = Admin.objects.get(id=user.id)
                    serializer.save(autor_admin=admin)
                except Admin.DoesNotExist:
                    raise PermissionDenied("Usuario no válido")

class ComentarioDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Vista para ver, actualizar y eliminar un comentario"""
    serializer_class = ComentarioSerializer
    authentication_classes = [CustomJWTAuthentication]
    
    def get_queryset(self):
        return Comentario.objects.all()
    
    def perform_destroy(self, instance):
        user = self.request.user
        autor = instance.autor
        
        if autor and autor.id == user.id:
            instance.delete()
        else:
            try:
                Admin.objects.get(id=user.id)
                instance.delete()
            except Admin.DoesNotExist:
                raise PermissionDenied("No tienes permiso para eliminar este comentario")

# ==================== VISTAS DE REPORTES ====================
class ReporteListCreateView(generics.ListCreateAPIView):
    """Vista para listar y crear reportes"""
    serializer_class = ReporteSerializer
    authentication_classes = [CustomJWTAuthentication]
    
    def get_queryset(self):
        user = self.request.user
        try:
            Admin.objects.get(id=user.id)
            return Reporte.objects.all().order_by('-fecha_creacion')
        except Admin.DoesNotExist:
            return Reporte.objects.filter(
                creado_por_alumno__id=user.id
            ) | Reporte.objects.filter(
                creado_por_profesor__id=user.id
            ) | Reporte.objects.filter(
                creado_por_admin__id=user.id
            )
    
    def perform_create(self, serializer):
        user = self.request.user
        
        try:
            alumno = Alumno.objects.get(id=user.id)
            serializer.save(creado_por_alumno=alumno)
        except Alumno.DoesNotExist:
            try:
                profesor = Profesor.objects.get(id=user.id)
                serializer.save(creado_por_profesor=profesor)
            except Profesor.DoesNotExist:
                try:
                    admin = Admin.objects.get(id=user.id)
                    serializer.save(creado_por_admin=admin)
                except Admin.DoesNotExist:
                    raise PermissionDenied("Usuario no válido")

class ReporteDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Vista para ver, actualizar y eliminar un reporte"""
    serializer_class = ReporteSerializer
    authentication_classes = [CustomJWTAuthentication]
    
    def get_queryset(self):
        return Reporte.objects.all()
    
    def perform_update(self, serializer):
        user = self.request.user
        try:
            Admin.objects.get(id=user.id)
            serializer.save()
        except Admin.DoesNotExist:
            raise PermissionDenied("Solo administradores pueden actualizar reportes")
    """Vista para ver, actualizar y eliminar una publicación específica"""
    serializer_class = PostSerializer
    authentication_classes = [CustomJWTAuthentication]
    
    def get_queryset(self):
        return Post.objects.all()
    
    def get_object(self):
        obj = super().get_object()
        
        # Incrementar vistas solo para GET requests
        if self.request.method == 'GET':
            obj.vistas += 1
            obj.save()
        
        return obj
    
    def perform_update(self, serializer):
        user = self.request.user
        post = self.get_object()
        
        # Verificar que el usuario sea el autor
        autor = post.autor
        if autor and autor.id == user.id:
            serializer.save()
        else:
            raise PermissionDenied("Solo el autor puede editar esta publicación")
    
    def perform_destroy(self, instance):
        user = self.request.user
        autor = instance.autor
        
        # Verificar que el usuario sea el autor o admin
        if autor and autor.id == user.id:
            instance.delete()
        else:
            # Verificar si es admin
            try:
                Admin.objects.get(id=user.id)
                instance.delete()
            except Admin.DoesNotExist:
                raise PermissionDenied("No tienes permiso para eliminar esta publicación")