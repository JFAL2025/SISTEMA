from django.db import models

class Rol(models.Model):
    id_rol = models.AutoField(primary_key=True, db_column='ID_ROL')
    nombre_rol = models.CharField(max_length=100, unique=True, db_column='NOMBRE_ROL')
    estado = models.BooleanField(default=True, db_column='ESTADO')
    
    class Meta:
        db_table = 'ROL'
        managed = False
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'
    
    def __str__(self):
        return self.nombre_rol

class Usuarios(models.Model):
    id_usuario = models.AutoField(primary_key=True, db_column='ID_USUARIO')
    nombre = models.CharField(max_length=255, db_column='NOMBRE')
    apellido = models.CharField(max_length=255, db_column='APELLIDO')
    correo = models.CharField(max_length=255, db_column='CORREO')
    fecha_registro = models.DateTimeField(db_column='FECHA_REGISTRO', auto_now_add=True)
    contrasena = models.CharField(max_length=255, db_column='CONTRASENA')
    id_rol = models.ForeignKey(Rol, models.DO_NOTHING, db_column='ID_ROL', blank=True, null=True)
    
    class Meta:
        db_table = 'USUARIOS'
        managed = False
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
    
    def __str__(self):
        return f"{self.nombre} {self.apellido}"
    
    @property
    def nombre_rol(self):
        return self.id_rol.nombre_rol if self.id_rol else "Sin rol"
    
    @property
    def es_administrador(self):
        return self.id_rol and self.id_rol.nombre_rol == 'ADMINISTRADOR'
    
    @property
    def es_coordinador(self):
        return self.id_rol and self.id_rol.nombre_rol == 'COORDINADOR'
    
    @property
    def es_encargado(self):
        return self.id_rol and self.id_rol.nombre_rol == 'ENCARGADO'