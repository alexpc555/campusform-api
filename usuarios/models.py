from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone

# ==================== USUARIOS ====================
class Alumno(models.Model):
    nombre = models.CharField(max_length=100)
    correo = models.EmailField(unique=True)
    contrasena = models.CharField(max_length=255)

    def save(self, *args, **kwargs):
        if self.contrasena and not self.contrasena.startswith("pbkdf2_"):
            self.contrasena = make_password(self.contrasena)
        super().save(*args, **kwargs)
    
    def check_password(self, raw_password):
        return check_password(raw_password, self.contrasena)
    
    @property
    def is_authenticated(self):
        return True

class Profesor(models.Model):
    nombre = models.CharField(max_length=100)
    correo = models.EmailField(unique=True)
    contrasena = models.CharField(max_length=255)

    def save(self, *args, **kwargs):
        if self.contrasena and not self.contrasena.startswith("pbkdf2_"):
            self.contrasena = make_password(self.contrasena)
        super().save(*args, **kwargs)
    
    def check_password(self, raw_password):
        return check_password(raw_password, self.contrasena)
    
    @property
    def is_authenticated(self):
        return True

class Admin(models.Model):
    nombre = models.CharField(max_length=100)
    correo = models.EmailField(unique=True)
    contrasena = models.CharField(max_length=255)

    def save(self, *args, **kwargs):
        if self.contrasena and not self.contrasena.startswith("pbkdf2_"):
            self.contrasena = make_password(self.contrasena)
        super().save(*args, **kwargs)
    
    def check_password(self, raw_password):
        return check_password(raw_password, self.contrasena)
    
    @property
    def is_authenticated(self):
        return True

# ==================== CATEGORÍAS ====================
class Categoria(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    creada_por = models.ForeignKey(Admin, on_delete=models.CASCADE, related_name='categorias')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return self.nombre
    
    @property
    def post_count(self):
        return self.posts.count() if hasattr(self, 'posts') else 0

# ==================== POSTS ====================
class Post(models.Model):
    titulo = models.CharField(max_length=150)
    contenido = models.TextField()
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='posts')
    autor_alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE, null=True, blank=True, related_name='posts')
    autor_profesor = models.ForeignKey(Profesor, on_delete=models.CASCADE, null=True, blank=True, related_name='posts')
    autor_admin = models.ForeignKey(Admin, on_delete=models.CASCADE, null=True, blank=True, related_name='posts')
    etiquetas = models.CharField(max_length=500, blank=True, null=True)
    vistas = models.IntegerField(default=0)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Publicación'
        verbose_name_plural = 'Publicaciones'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return self.titulo

    @property
    def autor(self):
        if self.autor_alumno:
            return self.autor_alumno
        elif self.autor_profesor:
            return self.autor_profesor
        elif self.autor_admin:
            return self.autor_admin
        return None

    @property
    def autor_nombre(self):
        autor = self.autor
        return autor.nombre if autor else 'Usuario desconocido'

    @property
    def autor_tipo(self):
        if self.autor_alumno:
            return 'student'
        elif self.autor_profesor:
            return 'teacher'
        elif self.autor_admin:
            return 'admin'
        return None

# ==================== COMENTARIOS ====================
class Comentario(models.Model):
    contenido = models.TextField()
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comentarios')
    autor_alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE, null=True, blank=True, related_name='comentarios')
    autor_profesor = models.ForeignKey(Profesor, on_delete=models.CASCADE, null=True, blank=True, related_name='comentarios')
    autor_admin = models.ForeignKey(Admin, on_delete=models.CASCADE, null=True, blank=True, related_name='comentarios')
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Comentario'
        verbose_name_plural = 'Comentarios'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"Comentario de {self.autor_nombre} en {self.post.titulo}"

    @property
    def autor(self):
        if self.autor_alumno:
            return self.autor_alumno
        elif self.autor_profesor:
            return self.autor_profesor
        elif self.autor_admin:
            return self.autor_admin
        return None

    @property
    def autor_nombre(self):
        autor = self.autor
        return autor.nombre if autor else 'Usuario desconocido'

# ==================== REPORTES ====================
class Reporte(models.Model):
    MOTIVOS = [
        ('spam', 'Spam o contenido engañoso'),
        ('contenido_inapropiado', 'Contenido inapropiado'),
        ('acoso', 'Acoso o intimidación'),
        ('lenguaje_ofensivo', 'Lenguaje ofensivo'),
        ('informacion_falsa', 'Información falsa'),
        ('derechos_autor', 'Violación de derechos de autor'),
        ('otro', 'Otro'),
    ]
    
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('revisado', 'Revisado'),
        ('resuelto', 'Resuelto'),
    ]
    
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='reportes')
    motivo = models.CharField(max_length=50, choices=MOTIVOS)
    razon = models.TextField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    creado_por_alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE, null=True, blank=True, related_name='reportes')
    creado_por_profesor = models.ForeignKey(Profesor, on_delete=models.CASCADE, null=True, blank=True, related_name='reportes')
    creado_por_admin = models.ForeignKey(Admin, on_delete=models.CASCADE, null=True, blank=True, related_name='reportes')
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Reporte'
        verbose_name_plural = 'Reportes'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"Reporte de {self.autor_nombre} - {self.get_motivo_display()}"

    @property
    def autor(self):
        if self.creado_por_alumno:
            return self.creado_por_alumno
        elif self.creado_por_profesor:
            return self.creado_por_profesor
        elif self.creado_por_admin:
            return self.creado_por_admin
        return None

    @property
    def autor_nombre(self):
        autor = self.autor
        return autor.nombre if autor else 'Usuario desconocido'