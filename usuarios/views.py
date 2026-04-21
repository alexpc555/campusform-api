from django.db.models import Count, F
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import PermissionDenied, NotFound
from rest_framework.permissions import IsAuthenticated

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
    permission_classes = []  # Permitir acceso público
    authentication_classes = []  # Sin autenticación requerida
    
    def post(self, request):
        print("📥 Datos recibidos en registro:", request.data)  # Debug
        
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
            
            print(f"✅ Usuario creado: {user.nombre} - {role}")  # Debug
            
            return Response(
                {
                    "message": "Usuario creado exitosamente", 
                    "id": user.id,
                    "role": role
                },
                status=status.HTTP_201_CREATED
            )
        
        print("❌ Errores de validación:", serializer.errors)  # Debug
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = []  # Permitir acceso público
    authentication_classes = []  # Sin autenticación requerida
    
    def post(self, request):
        print("📥 Datos recibidos en login:", request.data)  # Debug
        
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
                redirect_url = "/student-panel"
            elif user_model == "teacher":
                redirect_url = "/profesor"
            else:  # admin
                redirect_url = "/admin"
            
            print(f"✅ Login exitoso: {user.nombre} - {user_model}")  # Debug
            
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
        
        print("❌ Errores de validación en login:", serializer.errors)  # Debug
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


class MisComentariosView(generics.ListAPIView):
    """Vista para obtener los comentarios del usuario autenticado"""
    serializer_class = ComentarioSerializer
    authentication_classes = [CustomJWTAuthentication]

    def get_queryset(self):
        user = self.request.user

        if isinstance(user, Alumno):
            return Comentario.objects.filter(autor_alumno=user).order_by('-fecha_creacion')

        if isinstance(user, Profesor):
            return Comentario.objects.filter(autor_profesor=profesor).order_by('-fecha_creacion')

        if isinstance(user, Admin):
            return Comentario.objects.filter(autor_admin=user).order_by('-fecha_creacion')

        return Comentario.objects.none()
    

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
        nombre = request.data.get('nombre', '').strip()
        correo = request.data.get('correo', '').strip().lower()
        contrasena = request.data.get('contrasena', '')
        rol = request.data.get('rol', '')
        
        # Validaciones
        if not nombre or not correo or not contrasena or not rol:
            return Response(
                {'message': 'Todos los campos son requeridos'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar que no exista el correo
        if (Alumno.objects.filter(correo=correo).exists() or 
            Profesor.objects.filter(correo=correo).exists() or
            Admin.objects.filter(correo=correo).exists()):
            return Response(
                {'message': 'El correo ya está registrado'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
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
                return Response(
                    {'message': 'Rol no válido'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return Response({
                'id': user.id,
                'nombre': user.nombre,
                'correo': user.correo,
                'rol': rol
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'message': f'Error al crear usuario: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )


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
        
        # Actualizar nombre
        if 'nombre' in request.data:
            user.nombre = request.data['nombre'].strip()
        
        # Actualizar correo
        if 'correo' in request.data:
            new_email = request.data['correo'].strip().lower()
            
            # Si el correo NO cambió, no hacer nada
            if new_email == user.correo:
                pass  # No validar, es el mismo correo
            else:
                # Verificar si el nuevo correo ya existe en CUALQUIER tabla
                email_exists = (
                    Alumno.objects.filter(correo=new_email).exists() or
                    Profesor.objects.filter(correo=new_email).exists() or
                    Admin.objects.filter(correo=new_email).exists()
                )
                
                if email_exists:
                    return Response(
                        {'message': 'El correo ya está registrado por otro usuario'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                user.correo = new_email
        
        # Actualizar contraseña (opcional)
        if 'contrasena' in request.data and request.data['contrasena'].strip():
            user.contrasena = request.data['contrasena'].strip()
        
        # No permitir cambiar el rol
        if 'rol' in request.data and request.data['rol'] != role:
            return Response(
                {'message': 'No se puede cambiar el rol de un usuario existente'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
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
        return Response(
            {'message': 'Usuario eliminado correctamente'}, 
            status=status.HTTP_200_OK
        )


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
        
        print(f" MisPostsView - Usuario: {user}")
        print(f" MisPostsView - Tipo: {type(user)}")
        print(f" MisPostsView - ID: {user.id}")
        print(f" MisPostsView - Nombre: {user.nombre}")
        
        try:
            alumno = Alumno.objects.get(id=user.id)
            print(f" Usuario es Alumno")
            queryset = Post.objects.filter(autor_alumno=alumno)
        except Alumno.DoesNotExist:
            try:
                profesor = Profesor.objects.get(id=user.id)
                print(f" Usuario es Profesor (ID: {profesor.id})")
                queryset = Post.objects.filter(autor_profesor=profesor)
                print(f" Posts encontrados para profesor {profesor.nombre}: {queryset.count()}")
                for post in queryset:
                    print(f"   - Post: {post.titulo} (Autor: {post.autor_nombre})")
            except Profesor.DoesNotExist:
                try:
                    admin = Admin.objects.get(id=user.id)
                    print(f" Usuario es Admin")
                    queryset = Post.objects.filter(autor_admin=admin)
                except Admin.DoesNotExist:
                    print(f" Usuario no encontrado en ninguna tabla")
                    return Post.objects.none()
        
        return queryset.annotate(
            comentarios_count=Count('comentarios')
        ).order_by('-fecha_creacion')


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


class AnalyticsDashboardView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CustomJWTAuthentication]

    def get(self, request):
        total_alumnos = Alumno.objects.count()
        total_profesores = Profesor.objects.count()
        total_admins = Admin.objects.count()
        total_users = total_alumnos + total_profesores + total_admins

        total_posts = Post.objects.count()
        total_comments = Comentario.objects.count()
        total_reports = Reporte.objects.count()

        avg_comments_per_post = 0
        if total_posts > 0:
            avg_comments_per_post = round(total_comments / total_posts, 2)

        posts_per_category = (
            Categoria.objects.annotate(posts_count=Count("posts"))
            .values("id", "nombre", "posts_count")
            .order_by("-posts_count")
        )

        return Response({
            "summary": {
                "total_users": total_users,
                "total_alumnos": total_alumnos,
                "total_profesores": total_profesores,
                "total_admins": total_admins,
                "total_posts": total_posts,
                "total_comments": total_comments,
                "total_reports": total_reports,
                "avg_comments_per_post": avg_comments_per_post
            },
            "posts_per_category": [
                {
                    "id": item["id"],
                    "name": item["nombre"],
                    "posts": item["posts_count"]
                }
                for item in posts_per_category
            ]
        })


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

    def perform_destroy(self, instance):
        user = self.request.user
        try:
            Admin.objects.get(id=user.id)
            instance.delete()
        except Admin.DoesNotExist:
            raise PermissionDenied("Solo administradores pueden eliminar reportes")