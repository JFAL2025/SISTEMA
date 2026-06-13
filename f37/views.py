import os
import csv
import json
import traceback
from datetime import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.conf import settings

from .models import Usuarios, Rol, RiesgoSeguridad, ReporteSeguridad, LeccionAprendida, BitacoraAuditoria

# ========== 1. FUNCIÓN DE VERIFICACIÓN DE PERMISOS (ALTA PRIORIDAD) ==========

def verificar_permiso(request, requiere_admin=False, solo_lectura=False):
    if not request.session.get('usuario_id'):
        return {'error': 'No autorizado', 'status': 401}
    
    usuario_id = request.session.get('usuario_id')
    try:
        usuario = Usuarios.objects.select_related('id_rol').get(id_usuario=usuario_id)
        rol = usuario.id_rol.nombre_rol if usuario.id_rol else 'ENCARGADO'
        
        if rol == 'ADMINISTRADOR':
            return {'allowed': True, 'rol': rol}
        
        if rol in ['COORDINADOR', 'ENCARGADO']:
            if requiere_admin:
                return {'error': 'No tiene permisos de administrador', 'status': 403}
            return {'allowed': True, 'rol': rol}
        
        return {'error': 'Rol sin permisos', 'status': 403}
    except Usuarios.DoesNotExist:
        return {'error': 'Usuario no encontrado', 'status': 401}


# ========== 2. FUNCIÓN AUXILIAR DE AUDITORÍA AUTOMÁTICA ==========

def registrar_en_auditoria(request, accion, modulo, detalle):
    """Inserta de forma automática un movimiento en la bitácora usando la sesión activa"""
    try:
        usuario_nombre = request.session.get('usuario_nombre', 'Sistema Automático')
        BitacoraAuditoria.objects.create(
            usuario=usuario_nombre,
            accion=accion,
            modulo=modulo,
            detalle=detalle
        )
        print(f"🕵️‍♂️ Auditoría registrada: {accion} en {modulo} por {usuario_nombre}")
    except Exception as e:
        print(f"❌ Fallo al escribir historial de auditoría: {str(e)}")


# ========== 3. VISTAS DE PANTALLA GENERALES ==========

def vista_gestion_lecciones(request):
    context = {
        'usuarios': Usuarios.objects.all(),
        'usuario_id': request.session.get('usuario_id'), 
        'usuario_logueado': request.session.get('usuario_nombre'),
        'es_admin': request.session.get('usuario_rol') == 'ADMINISTRADOR', 
    }
    return render(request, 'lecciones.html', context)


def exportar_lecciones_csv(request):
    """B.5: Genera y descarga un reporte automático en formato Excel/CSV de las lecciones"""
    if not request.session.get('usuario_id'):
        return HttpResponse('No autorizado', status=401)
        
    try:
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="Reporte_Lecciones_Aprendidas.csv"'
        response.write(u'\ufeff'.encode('utf8'))
        
        writer = csv.writer(response, delimiter=';')
        writer.writerow([
            'ID LECCIÓN', 'TIPO EVENTO', 'FECHA IDENTIFICACIÓN', 
            'DESCRIPCIÓN / HALLAZGO', 'IMPACTO / SITUACIÓN', 
            'RECOMENDACIÓN TÉCNICA', 'ACCIÓN A TOMAR', 
            'JUSTIFICACIÓN', 'NIVEL EFICACIA', 'ID REPORTE PADRE'
        ])
        
        lecciones = LeccionAprendida.objects.all().order_by('-id_leccion_aprendida')
        
        for l in lecciones:
            writer.writerow([
                l.id_leccion_aprendida,
                l.tipo or 'GENERAL',
                l.fecha_identificacion or 'No registrada',
                l.descripcion or 'Sin descripción',
                l.impacto_situacion or 'No especificado',
                l.recomendacion or 'Ninguna',
                l.accion_tomar or 'Ninguna',
                l.justificacion or 'No especificada',
                l.nivel_eficacia or 'PENDIENTE',
                l.id_reporte or 'N/A'
            ])
            
        registrar_en_auditoria(
            request,
            accion="CREAR",
            modulo="REPORTES",
            detalle="Se generó y descargó el reporte automático consolidado de lecciones aprendidas en formato Excel CSV"
        )
        return response
    except Exception as e:
        print(f"❌ Error al exportar reporte: {str(e)}")
        return HttpResponse(f"Error interno al generar el reporte: {str(e)}", status=500)


def login(request):
    if request.method == 'POST':
        correo = request.POST.get('correo')
        contrasena = request.POST.get('contrasena')
        
        print("=" * 50)
        print(f"Correo ingresado: '{correo}'")
        print(f"Contraseña ingresada: '{contrasena}'")
        
        try:
            usuario = Usuarios.objects.select_related('id_rol').get(correo=correo)
            print(f"Usuario encontrado: {usuario.nombre} {usuario.apellido}")
            print(f"Contraseña en BD: '{usuario.contrasena}'")
            
            if usuario.contrasena == contrasena:
                print("✅ Contraseña correcta")
                request.session['usuario_id'] = usuario.id_usuario
                request.session['usuario_nombre'] = f"{usuario.nombre} {usuario.apellido}"
                request.session['usuario_rol'] = usuario.id_rol.nombre_rol if usuario.id_rol else "Sin rol"
                request.session['es_admin'] = (usuario.id_rol.nombre_rol == 'ADMINISTRADOR') if usuario.id_rol else False
                
                print(f"Sesión guardada - Nombre: {request.session.get('usuario_nombre')}")
                print(f"Sesión guardada - Rol: {request.session.get('usuario_rol')}")
                print("✅ Login exitoso. Redirigiendo...")
                
                return redirect('panel')
            else:
                print("❌ Contraseña incorrecta")
        except Usuarios.DoesNotExist:
            print(f"❌ Usuario no existe: {correo}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        return render(request, 'login.html', {'error': 'Credenciales incorrectas'})
    
    return render(request, 'login.html')


def logout(request):
    request.session.flush()
    return redirect('login')


def panel(request):
    if not request.session.get('usuario_id'):
        return redirect('login')
    
    context = {
        'usuario_logueado': request.session.get('usuario_nombre', 'Invitado'),
        'usuario_rol': request.session.get('usuario_rol', 'Sin rol'),
        'es_admin': request.session.get('es_admin', False),
    }
    return render(request, 'panel.html', context)


def admin_panel(request):
    if not request.session.get('usuario_id'):
        return redirect('login')
    
    if not request.session.get('es_admin'):
        return redirect('panel')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'crear':
            correo = request.POST.get('correo')
            if Usuarios.objects.filter(correo=correo).exists():
                messages.error(request, f'❌ El correo "{correo}" ya está registrado')
                return redirect('admin.html')
                
            usuario = Usuarios(
                nombre=request.POST['nombre'],
                apellido=request.POST['apellido'],
                correo=correo,
                contrasena=request.POST['contrasena'],
                id_rol_id=request.POST.get('id_rol'),
                fecha_registro=datetime.now()
            )
            usuario.save()
            messages.success(request, f'✅ Usuario {usuario.nombre} creado exitosamente')
        
        elif action == 'editar':
            usuario_id = request.POST.get('id')
            usuario = get_object_or_404(Usuarios, id_usuario=usuario_id)
            nuevo_correo = request.POST.get('correo')
            
            if Usuarios.objects.filter(correo=nuevo_correo).exclude(id_usuario=usuario_id).exists():
                messages.error(request, f'❌ El correo "{nuevo_correo}" ya está registrado por otro usuario')
                return redirect('admin.html')
            
            usuario.nombre = request.POST['nombre']
            usuario.apellido = request.POST['apellido']
            usuario.correo = nuevo_correo
            if request.POST.get('contrasena'):
                usuario.contrasena = request.POST['contrasena']
            usuario.id_rol_id = request.POST.get('id_rol')
            usuario.save()
            messages.success(request, f'✅ Usuario {usuario.nombre} actualizado exitosamente')
        
        elif action == 'eliminar':
            usuario_id = request.POST.get('id')
            if int(usuario_id) == request.session.get('usuario_id'):
                messages.error(request, '❌ No puedes eliminar tu propia cuenta')
                return redirect('admin.html')
            
            usuario = get_object_or_404(Usuarios, id_usuario=usuario_id)
            nombre_usuario = usuario.nombre
            usuario.delete()
            messages.success(request, f'✅ Usuario {nombre_usuario} eliminado exitosamente')
        
        return redirect('admin.html')
    
    usuarios = Usuarios.objects.select_related('id_rol').all().order_by('-fecha_registro')
    roles = Rol.objects.filter(estado=1).all()
    
    context = {
        'usuarios': usuarios,
        'roles': roles,
        'usuario_logueado': request.session.get('usuario_nombre', 'Invitado'),
        'usuario_rol': request.session.get('usuario_rol', 'Sin rol'),
        'es_admin': request.session.get('es_admin', False),
    }
    return render(request, 'admin.html', context)


def riesgo(request):
    if not request.session.get('usuario_id'):
        return redirect('login')
    
    context = {
        'usuario_logueado': request.session.get('usuario_nombre', 'Invitado'),
        'usuario_rol': request.session.get('usuario_rol', 'Sin rol'),
        'es_admin': request.session.get('es_admin', False),
    }
    return render(request, 'riesgo.html', context)


def leccion(request):
    if not request.session.get('usuario_id'):
        return redirect('login')
    
    usuarios = Usuarios.objects.select_related('id_rol').all()
    context = {
        'usuario_logueado': request.session.get('usuario_nombre', 'Invitado'),
        'usuario_rol': request.session.get('usuario_rol', 'Sin rol'),
        'es_admin': request.session.get('es_admin', False),
        'usuarios': usuarios,
    }
    return render(request, 'leccion.html', context)


# ========== 4. VISTAS Y APIs DE REPORTES UNIFICADOS ==========

def vista_reportes_tabla(request):
    if not request.session.get('usuario_id'):
        return redirect('login')
    
    try:
        tabla_consolidada = []
        reportes_db = {rep['id_reporte']: rep['estado'] for rep in ReporteSeguridad.objects.all().values('id_reporte', 'estado')}

        # 1. Procesar Riesgos
        riesgos = RiesgoSeguridad.objects.all()
        for r in riesgos:
            estado = reportes_db.get(r.id_reporte, 'PENDIENTE')
            tabla_consolidada.append({
                'id_reporte': r.id_reporte,
                'tipo_modulo': 'RIESGO DE SEGURIDAD',
                'origen_mejora': r.origen_mejora,
                'responsable': r.responsable_seguimiento,
                'area': r.area,
                'nivel_riesgo': r.nivel_riesgo,
                'estado': estado
            })

        # 2. Procesar Lecciones
        lecciones = LeccionAprendida.objects.all()
        for l in lecciones:
            estado = reportes_db.get(l.id_reporte, 'PENDIENTE')
            nombre_resp = "Sin Asignar"
            if l.asignado_a_id:
                u = Usuarios.objects.filter(id_usuario=l.asignado_a_id).first()
                if u: 
                    nombre_resp = f"{u.nombre} {u.apellido}"

            tabla_consolidada.append({
                'id_reporte': l.id_reporte,
                'tipo_modulo': 'LECCIÓN APRENDIDA',
                'origen_mejora': f"Lección - {l.tipo}",
                'responsable': nombre_resp,
                'area': "Módulo Lecciones",
                'nivel_riesgo': 'MEDIO' if l.tipo == 'INCIDENTE' else 'ALTO',
                'estado': estado
            })

        tabla_consolidada.sort(key=lambda x: x['id_reporte'], reverse=True)

        context = {
            'reportes_lista': tabla_consolidada,
            'usuario_logueado': request.session.get('usuario_nombre', 'Invitado'),
            'usuario_role': request.session.get('usuario_rol', 'Sin rol'),
            'es_admin': request.session.get('es_admin', False),
        }
        return render(request, 'reportes.html', context)
    except Exception as e:
        print(f"❌ Error al consolidar tabla: {str(e)}")
        raise e


def listar_reportes_api(request):
    if not request.session.get('usuario_id'):
        return JsonResponse({'error': 'No autorizado'}, status=401)
    try:
        reportes = ReporteSeguridad.objects.all().values('id_reporte', 'estado')
        return JsonResponse(list(reportes), safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def listar_reportes_tabla_api(request):
    permiso = verificar_permiso(request, solo_lectura=True)
    if 'error' in permiso:
        return JsonResponse({'error': permiso['error']}, status=permiso['status'])

    try:
        tabla_consolidada = []
        reportes_db = {rep['id_reporte']: rep['estado'] for rep in ReporteSeguridad.objects.all().values('id_reporte', 'estado')}

        riesgos = RiesgoSeguridad.objects.all()
        for r in riesgos:
            tabla_consolidada.append({
                'id_reporte': r.id_reporte,
                'id_rsf': r.id_rsf,
                'tipo_modulo': 'RIESGO DE SEGURIDAD',
                'origen_mejora': r.origen_mejora,
                'responsable': r.responsable_seguimiento,
                'area': r.area,
                'nivel_riesgo': r.nivel_riesgo,
                'estado': reportes_db.get(r.id_reporte, 'PENDIENTE')
            })

        lecciones = LeccionAprendida.objects.all()
        for l in lecciones:
            nombre_resp = "Sin Asignar"
            if l.asignado_a_id:
                u = Usuarios.objects.filter(id_usuario=l.asignado_a_id).values('nombre', 'apellido').first()
                if u: 
                    nombre_resp = f"{u.get('nombre')} {u.get('apellido')}"

            tabla_consolidada.append({
                'id_reporte': l.id_reporte,
                'id_rsf': f"LECC-{l.id_leccion_aprendida}",
                'tipo_modulo': 'LECCIÓN APRENDIDA',
                'origen_mejora': f"Lección - {l.tipo}",
                'responsable': nombre_resp,
                'area': "Módulo Lecciones",
                'nivel_riesgo': 'MEDIO' if l.tipo == 'INCIDENTE' else 'ALTO',
                'estado': reportes_db.get(l.id_reporte, 'PENDIENTE')
            })

        tabla_consolidada.sort(key=lambda x: x['id_reporte'], reverse=True)
        return JsonResponse(tabla_consolidada, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def detalle_reporte_unificado_api(request, id_reporte):
    try:
        reporte_padre = ReporteSeguridad.objects.filter(id_reporte=id_reporte).values('id_reporte', 'estado').first()
        if not reporte_padre:
            return JsonResponse({'error': f'El reporte #{id_reporte} no existe'}, status=404)
        
        riesgo = RiesgoSeguridad.objects.filter(id_reporte=id_reporte).values(
            'id_reporte', 'origen_mejora', 'responsable_seguimiento', 'area', 'nivel_riesgo', 'recomendacion'
        ).first()
        
        if riesgo:
            return JsonResponse({
                'id_reporte': int(id_reporte),
                'estado': str(reporte_padre.get('estado') or 'PENDIENTE'),
                'area': str(riesgo.get('area') or 'Módulo General'),
                'responsable_seguimiento': str(riesgo.get('responsable_seguimiento') or 'Sin Asignar'),
                'descripcion_riesgo': f"Origen: {riesgo.get('origen_mejora')}. Recomendación: {riesgo.get('recomendacion') or 'Ninguna'}",
                'nivel_riesgo': str(riesgo.get('nivel_riesgo') or 'MEDIO'),
                'origen_mejora': str(riesgo.get('origen_mejora') or 'No especificado')
            })
            
        leccion = LeccionAprendida.objects.filter(id_reporte=id_reporte).values(
            'id_reporte', 'tipo', 'descripcion', 'asignado_a_id', 'nivel_eficacia'
        ).first()
        
        if leccion:
            nombre_resp = "Sin Asignar"
            if leccion.get('asignado_a_id'):
                u = Usuarios.objects.filter(id_usuario=leccion['asignado_a_id']).values('nombre', 'apellido').first()
                if u: 
                    nombre_resp = f"{u.get('nombre') or ''} {u.get('apellido') or ''}".strip() or "Sin Asignar"
            
            return JsonResponse({
                'id_reporte': int(id_reporte),
                'estado': str(reporte_padre.get('estado') or 'PENDIENTE'),
                'area': "Módulo Lecciones",
                'asignado_a': nombre_resp,
                'descripcion_leccion': str(leccion.get('descripcion') or 'Sin descripción'),
                'tipo_leccion': f"Lección - {str(leccion.get('tipo') or 'GENERAL')}",
                'nivel_eficacia': str(leccion.get('nivel_eficacia') or 'PENDIENTE DE EVALUACIÓN')
            })
            
        return JsonResponse({'error': 'Reporte base encontrado pero sin datos vinculados en módulos hijo'}, status=422)
    except Exception as e:
        print(f"❌ Error crítico real en detalle: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


# ========== 5. APIs PARA RIESGOS CON AUDITORÍA ==========

def listar_riesgos_api(request):
    permiso = verificar_permiso(request, solo_lectura=True)
    if 'error' in permiso:
        return JsonResponse({'error': permiso['error']}, status=permiso['status'])
    try:
        riesgos = RiesgoSeguridad.objects.all().values(
            'id_rsf', 'id_reporte', 'origen_mejora', 'responsable_seguimiento',
            'macroproceso', 'actividad', 'area', 'recomendacion', 'dependencia', 'nivel_riesgo'
        )
        return JsonResponse(list(riesgos), safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def crear_riesgo_api(request):
    permiso = verificar_permiso(request)
    if 'error' in permiso:
        return JsonResponse({'error': permiso['error']}, status=permiso['status'])
    
    if permiso['rol'] not in ['ADMINISTRADOR', 'COORDINADOR', 'ENCARGADO']:
        return JsonResponse({'error': 'No tiene permisos para crear riesgos'}, status=403)
    
    try:
        data = json.loads(request.body)
        campos_requeridos = ['actividad', 'responsable_seguimiento', 'macroproceso', 'area']
        for campo in campos_requeridos:
            if not data.get(campo):
                return JsonResponse({'error': f'El campo {campo} es obligatorio'}, status=400)
        
        reporte = ReporteSeguridad.objects.create(
            id_usuario=request.session.get('usuario_id'),
            fecha_reporte=timezone.now(),
            estado='PENDIENTE'
        )
        
        riesgo_obj = RiesgoSeguridad.objects.create(
            id_reporte=reporte.id_reporte,
            origen_mejora=data.get('origen_mejora', ''),
            responsable_seguimiento=data.get('responsable_seguimiento', ''),
            macroproceso=data.get('macroproceso', ''),
            actividad=data.get('actividad', ''),
            area=data.get('area', ''),
            recomendacion=data.get('recomendacion', ''),
            dependencia=data.get('dependencia', ''),
            nivel_riesgo=data.get('nivel_riesgo', 'MEDIO')
        )
        
        registrar_en_auditoria(
            request,
            accion="CREAR",
            modulo="RIESGOS DE SEGURIDAD",
            detalle=f"Se reportó un nuevo riesgo estratégico (#{riesgo_obj.id_rsf}) en el área de {riesgo_obj.area}"
        )
        
        return JsonResponse({'id': riesgo_obj.id_rsf, 'id_reporte': reporte.id_reporte, 'message': 'Riesgo creado exitosamente'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
def actualizar_riesgo_api(request, id):
    permiso = verificar_permiso(request)
    if 'error' in permiso:
        return JsonResponse({'error': permiso['error']}, status=permiso['status'])
    
    if permiso['rol'] not in ['ADMINISTRADOR', 'COORDINADOR', 'ENCARGADO']:
        return JsonResponse({'error': 'No tiene permisos para editar riesgos'}, status=403)
    
    try:
        data = json.loads(request.body)
        riesgo_obj = RiesgoSeguridad.objects.get(id_rsf=id)
        riesgo_obj.origen_mejora = data.get('origen_mejora', '')
        riesgo_obj.responsable_seguimiento = data.get('responsable_seguimiento', '')
        riesgo_obj.macroproceso = data.get('macroproceso', '')
        riesgo_obj.actividad = data.get('actividad', '')
        riesgo_obj.area = data.get('area', '')
        riesgo_obj.recomendacion = data.get('recomendacion', '')
        riesgo_obj.dependencia = data.get('dependencia', '')
        riesgo_obj.nivel_riesgo = data.get('nivel_riesgo', 'MEDIO')
        riesgo_obj.save()
        
        nuevo_estado = data.get('estado_reporte')
        if nuevo_estado and riesgo_obj.id_reporte:
            if nuevo_estado in ['PENDIENTE', 'EN EJECUCION', 'FINALIZADO']:
                ReporteSeguridad.objects.filter(id_reporte=riesgo_obj.id_reporte).update(estado=nuevo_estado)
        
        registrar_en_auditoria(
            request,
            accion="EDITAR",
            modulo="RIESGOS DE SEGURIDAD",
            detalle=f"Se actualizaron los parámetros del riesgo #{id} (Nivel asignado: {riesgo_obj.nivel_riesgo})"
        )
        
        return JsonResponse({'message': 'Riesgo actualizado exitosamente'})
    except RiesgoSeguridad.DoesNotExist:
        return JsonResponse({'error': 'Riesgo no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
def eliminar_riesgo_api(request, id):
    permiso = verificar_permiso(request)
    if 'error' in permiso:
        return JsonResponse({'error': permiso['error']}, status=permiso['status'])
    
    if permiso['rol'] not in ['ADMINISTRADOR', 'ENCARGADO']:
        return JsonResponse({'error': 'No tiene permisos para eliminar riesgos'}, status=403)
    
    try:
        riesgo_obj = RiesgoSeguridad.objects.get(id_rsf=id)
        id_reporte = riesgo_obj.id_reporte
        riesgo_obj.delete()
        
        if id_reporte:
            ReporteSeguridad.objects.filter(id_reporte=id_reporte).delete()
            
        registrar_en_auditoria(
            request,
            accion="ELIMINAR",
            modulo="RIESGOS DE SEGURIDAD",
            detalle=f"Se eliminó permanentemente el riesgo de seguridad con identificador físico #{id}"
        )
            
        return JsonResponse({'message': 'Riesgo eliminado exitosamente'})
    except RiesgoSeguridad.DoesNotExist:
        return JsonResponse({'error': 'Riesgo no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


# ========== 6. APIs PARA LECCIONES APRENDIDAS CON AUDITORÍA ==========

def listar_lecciones_api(request):
    permiso = verificar_permiso(request, solo_lectura=True)
    if 'error' in permiso:
        return JsonResponse({'error': permiso['error']}, status=permiso['status'])
    
    try:
        lecciones = LeccionAprendida.objects.all()
        lecciones_list = []
        
        for l in lecciones:
            creador_id = 0
            try:
                if hasattr(l, 'id_reporte') and l.id_reporte:
                    creador_id = getattr(l.id_reporte, 'id_usuario', 0)
                else:
                    creador_id = getattr(l, 'id_reporte_id', 0)
            except Exception as fe:
                print(f"⚠️ Aviso: No se pudo extraer creador_id en lección #{l.id_leccion_aprendida}: {fe}")
                creador_id = 0

            assigned_nombre = None
            if l.asignado_a_id:
                try:
                    usuario = Usuarios.objects.filter(id_usuario=l.asignado_a_id).first()
                    if usuario:
                        assigned_nombre = f"{usuario.nombre} {usuario.apellido}"
                except Exception:
                    assigned_nombre = f"ID: {l.asignado_a_id}"
            
            lecciones_list.append({
                'id_leccion_aprendida': getattr(l, 'id_leccion_aprendida', None),
                'tipo': getattr(l, 'tipo', ''),
                'descripcion': getattr(l, 'descripcion', ''),
                'fecha_identificacion': getattr(l, 'fecha_identificacion', None),
                'impacto_situacion': getattr(l, 'impacto_situacion', ''),
                'recomendacion': getattr(l, 'recomendacion', ''),
                'accion_tomar': getattr(l, 'accion_tomar', ''),
                'justificacion': getattr(l, 'justificacion', ''),
                'nivel_eficacia': getattr(l, 'nivel_eficacia', ''),
                'id_reporte': getattr(l, 'id_reporte_id', None),
                'asignado_a_id': getattr(l, 'asignado_a_id', None),
                'assigned_nombre': assigned_nombre,
                'creador_id': creador_id
            })
        
        return JsonResponse(lecciones_list, safe=False)
    except Exception as e:
        print("❌ ERROR CRÍTICO EN LISTAR LECCIONES:")
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)
    

@csrf_exempt
def crear_leccion_api(request):
    if not request.session.get('usuario_id'):
        return JsonResponse({'error': 'No autorizado'}, status=401)
    
    rol = request.session.get('usuario_rol')
    if rol not in ['ADMINISTRADOR', 'COORDINADOR', 'ENCARGADO']:
        return JsonResponse({'error': 'No tiene permisos para crear lecciones'}, status=403)
    
    try:
        data = json.loads(request.body)
        if not data.get('tipo') or not data.get('descripcion'):
            return JsonResponse({'error': 'Tipo y Descripción son campos obligatorios'}, status=400)
        
        reporte = ReporteSeguridad.objects.create(
            id_usuario=request.session.get('usuario_id'),
            fecha_reporte=timezone.now(),
            estado='PENDIENTE'
        )
        
        leccion_obj = LeccionAprendida.objects.create(
            tipo=data.get('tipo', ''),
            descripcion=data.get('descripcion', ''),
            fecha_identificacion=data.get('fecha_identificacion') or None,
            impacto_situacion=data.get('impacto_situacion', ''),
            recomendacion=data.get('recomendacion', ''),
            accion_tomar='',
            justificacion='',
            nivel_eficacia='',
            asignado_a_id=data.get('asignado_a') or None,
            id_reporte=reporte.id_reporte
        )
        
        registrar_en_auditoria(
            request,
            accion="CREAR",
            modulo="LECCIONES APRENDIDAS",
            detalle=f"Se registró una nueva lección unificada (#{leccion_obj.id_leccion_aprendida}) de tipo {leccion_obj.tipo}"
        )
        
        return JsonResponse({'id': leccion_obj.id_leccion_aprendida, 'id_reporte': reporte.id_reporte, 'message': 'Lección creada exitosamente'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
def actualizar_leccion_api(request, id):
    """
    Sincroniza dinámicamente los campos según el actor. 
    Evita que campos deshabilitados en el front pisen los existentes.
    """
    if not request.session.get('usuario_id'):
        return JsonResponse({'error': 'No autorizado'}, status=401)
    
    rol = request.session.get('usuario_rol')
    if rol not in ['ADMINISTRADOR', 'COORDINADOR', 'ENCARGADO']:
        return JsonResponse({'error': 'No tiene permisos para editar lecciones'}, status=403)
    
    try:
        data = json.loads(request.body)
        leccion_obj = LeccionAprendida.objects.get(id_leccion_aprendida=id)
        
        # GUARDADO OPERATIVO SELECTIVO POR ATRIBUTO VIVO
        if 'tipo' in data: leccion_obj.tipo = data.get('tipo', leccion_obj.tipo)
        if 'descripcion' in data: leccion_obj.descripcion = data.get('descripcion', leccion_obj.descripcion)
        if 'fecha_identificacion' in data: leccion_obj.fecha_identificacion = data.get('fecha_identificacion') or leccion_obj.fecha_identificacion
        if 'impacto_situacion' in data: leccion_obj.impacto_situacion = data.get('impacto_situacion', leccion_obj.impacto_situacion)
        if 'recomendacion' in data: leccion_obj.recomendacion = data.get('recomendacion', leccion_obj.recomendacion)
        if 'accion_tomar' in data: leccion_obj.accion_tomar = data.get('accion_tomar', leccion_obj.accion_tomar)
        if 'justificacion' in data: leccion_obj.justificacion = data.get('justificacion', leccion_obj.justificacion)
        if 'nivel_eficacia' in data: leccion_obj.nivel_eficacia = data.get('nivel_eficacia', leccion_obj.nivel_eficacia)
        if 'asignado_a' in data: leccion_obj.asignado_a_id = data.get('asignado_a') or leccion_obj.asignado_a_id
        
        leccion_obj.save()
        
        nuevo_estado = data.get('estado_reporte')
        if nuevo_estado and leccion_obj.id_reporte:
            if nuevo_estado in ['PENDIENTE', 'EN EJECUCION', 'FINALIZADO']:
                ReporteSeguridad.objects.filter(id_reporte=leccion_obj.id_reporte).update(estado=nuevo_estado)
        
        registrar_en_auditoria(
            request,
            accion="EDITAR",
            modulo="LECCIONES APRENDIDAS",
            detalle=f"Se modificaron los parámetros técnicos de la lección analizada #{id}"
        )
        
        return JsonResponse({'message': 'Lección actualizada exitosamente'})
    except LeccionAprendida.DoesNotExist:
        return JsonResponse({'error': 'Lección no encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
def eliminar_leccion_api(request, id):
    if not request.session.get('usuario_id'):
        return JsonResponse({'error': 'No autorizado'}, status=401)
    
    rol = request.session.get('usuario_rol')
    if rol not in ['ADMINISTRADOR', 'ENCARGADO']:
        return JsonResponse({'error': 'No tiene permisos para eliminar lecciones'}, status=403)
    
    try:
        leccion_obj = LeccionAprendida.objects.get(id_leccion_aprendida=id)
        id_reporte = leccion_obj.id_reporte
        leccion_obj.delete()
        
        if id_reporte:
            ReporteSeguridad.objects.filter(id_reporte=id_reporte).delete()
            
        registrar_en_auditoria(
            request,
            accion="ELIMINAR",
            modulo="LECCIONES APRENDIDAS",
            detalle=f"Se removió permanentemente la lección #{id} junto al reporte correlativo #{id_reporte}"
        )
            
        return JsonResponse({'message': 'Lección eliminada exitosamente'})
    except LeccionAprendida.DoesNotExist:
        return JsonResponse({'error': 'Lección no encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


# ========== 7. RENDERS Y APIs VINCULADAS A LA BITÁCORA ==========

def vista_auditoria(request):
    ruta_raiz = os.path.join(settings.BASE_DIR, 'templates', 'auditoria.html')
    ruta_app = os.path.join(settings.BASE_DIR, 'f37', 'templates', 'auditoria.html')
    
    if os.path.exists(ruta_raiz) or os.path.exists(ruta_app):
        return render(request, 'auditoria.html')
    
    html_error = f"""
    <div style="background:#1A1A1A; color:white; padding:30px; font-family:sans-serif; border-radius:10px; border:2px solid #FF8C00; max-width:600px; margin:50px auto;">
        <h2 style="color:#FF8C00; margin-top:0;">⚠️ Archivo auditoria.html no encontrado</h2>
        <p>Por favor, confirma que el archivo <b>auditoria.html</b> está en esta ruta exacta:</p>
        <code style="background:#0D0D0D; display:block; padding:15px; color:#28a745; border-radius:5px; word-break:break-all;">{ruta_raiz}</code>
    </div>
    """
    return HttpResponse(html_error, status=404)


def api_listar_auditoria(request):
    if not request.session.get('usuario_id'):
        return JsonResponse({'error': 'No autorizado'}, status=401)
    try:
        logs = BitacoraAuditoria.objects.all().values('id_auditoria', 'usuario', 'accion', 'modulo', 'detalle', 'fecha_accion')
        logs_list = list(logs)
        for log in logs_list:
            if log['fecha_accion']:
                log['fecha_accion'] = log['fecha_accion'].strftime('%d/%m/%Y %H:%M:%S')
        return JsonResponse(logs_list, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)