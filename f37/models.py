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


class ReporteSeguridad(models.Model):
    id_reporte = models.AutoField(primary_key=True, db_column='ID_REPORTE')
    id_usuario = models.IntegerField(db_column='ID_USUARIO', blank=True, null=True)
    fecha_reporte = models.DateTimeField(db_column='FECHA_REPORTE', auto_now_add=True)
    estado = models.CharField(max_length=50, db_column='ESTADO', blank=True, null=True)
    
    class Meta:
        db_table = 'REPORTE_DE_SEGURIDAD'
        managed = False
    
    def __str__(self):
        return f"Reporte {self.id_reporte}"


class RiesgoSeguridad(models.Model):
    id_rsf = models.AutoField(primary_key=True, db_column='ID_RSF')
    id_reporte = models.CharField(max_length=100, db_column='ID_REPORTE', blank=True, null=True)
    origen_mejora = models.TextField(db_column='ORIGEN_MEJORA', blank=True, null=True)
    responsable_seguimiento = models.CharField(max_length=200, db_column='RESPONSABLE_SEGUIMIENTO', blank=True, null=True)
    macroproceso = models.CharField(max_length=200, db_column='MACROPROCESO', blank=True, null=True)
    actividad = models.TextField(db_column='ACTIVIDAD', blank=True, null=True)
    area = models.CharField(max_length=200, db_column='AREA', blank=True, null=True)
    recomendacion = models.TextField(db_column='RECOMENDACION', blank=True, null=True)
    dependencia = models.CharField(max_length=200, db_column='DEPENDENCIA', blank=True, null=True)
    nivel_riesgo = models.CharField(max_length=20, db_column='NIVEL_RIESGO', blank=True, null=True)
    
    class Meta:
        db_table = 'RIESGO_DE_SEGURIDAD'
        managed = False
    
    def __str__(self):
        return f"{self.id_rsf} - {self.actividad[:50] if self.actividad else 'Sin actividad'}"


class LeccionAprendida(models.Model):
    id_leccion_aprendida = models.AutoField(primary_key=True, db_column='ID_LECCION_APRENDIDA')
    tipo = models.CharField(max_length=100, db_column='TIPO', blank=True, null=True)
    descripcion = models.TextField(db_column='DESCRIPCION', blank=True, null=True)
    fecha_identificacion = models.DateField(db_column='FECHA_IDENTIFICACION', blank=True, null=True)
    impacto_situacion = models.TextField(db_column='IMPACTO_SITUACION', blank=True, null=True)
    recomendacion = models.TextField(db_column='RECOMENDACION', blank=True, null=True)
    accion_tomar = models.TextField(db_column='ACCION_TOMAR', blank=True, null=True)
    justificacion = models.TextField(db_column='JUSTIFICACION', blank=True, null=True)
    nivel_eficacia = models.CharField(max_length=20, db_column='NIVEL_EFICACIA', blank=True, null=True)
    id_reporte = models.CharField(max_length=100, db_column='ID_REPORTE', blank=True, null=True)
    # Nota: Si tu base de datos tiene una columna física para la FK de usuario, puedes mapearla con db_column si es necesario.
    asignado_a = models.ForeignKey(Usuarios, on_delete=models.SET_NULL, null=True, blank=True, related_name='lecciones_assigned')
    
    class Meta:
        db_table = 'LECCION_APRENDIDA'
        managed = False
    
    def __str__(self):
        return f"{self.id_leccion_aprendida} - {self.tipo}"


# ================= NUEVO MODELO PARA SPRINT 2 (B.4) =================
class BitacoraAuditoria(models.Model):
    id_auditoria = models.AutoField(primary_key=True, db_column='ID_AUDITORIA')
    usuario = models.CharField(max_length=150, db_column='USUARIO')
    accion = models.CharField(max_length=50, db_column='ACCION')          # CREAR, EDITAR, ELIMINAR
    modulo = models.CharField(max_length=100, db_column='MODULO')          # LECCIONES, RIESGOS
    detalle = models.TextField(db_column='DETALLE')                       # Descripción del movimiento
    fecha_accion = models.DateTimeField(auto_now_add=True, db_column='FECHA_ACCION')

    class Meta:
        db_table = 'BITACORA_AUDITORIA'
        managed = True  # Mantenemos True para que Django sí pueda crear esta tabla específica si ejecutas migraciones
        verbose_name = 'Auditoría'
        verbose_name_plural = 'Auditorías'

    def __str__(self):
        return f"{self.usuario} - {self.accion} ({self.fecha_accion})"