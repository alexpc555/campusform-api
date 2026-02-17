from django.db import models
from django.contrib.auth.hashers import make_password

class Alumno(models.Model):
    nombre = models.CharField(max_length=100)
    correo = models.EmailField(unique=True)
    contrasena = models.CharField(max_length=255)

    def save(self, *args, **kwargs):
        if self.contrasena and not self.contrasena.startswith("pbkdf2_"):
            self.contrasena = make_password(self.contrasena)
        super().save(*args, **kwargs)

class Profesor(models.Model):
    nombre = models.CharField(max_length=100)
    correo = models.EmailField(unique=True)
    contrasena = models.CharField(max_length=255)

    def save(self, *args, **kwargs):
        if self.contrasena and not self.contrasena.startswith("pbkdf2_"):
            self.contrasena = make_password(self.contrasena)
        super().save(*args, **kwargs)
