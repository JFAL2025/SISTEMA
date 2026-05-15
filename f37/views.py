from django.shortcuts import render, redirect, get_object_or_404
from .models import Usuarios, Rol
from datetime import datetime
from django.contrib import messages


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
                # Guardar en sesión
                request.session['usuario_id'] = usuario.id_usuario
                request.session['usuario_nombre'] = f"{usuario.nombre} {usuario.apellido}"
                request.session['usuario_rol'] = usuario.id_rol.nombre_rol if usuario.id_rol else "Sin rol"
                request.session['es_admin'] = (usuario.id_rol.nombre_rol == 'ADMINISTRADOR') if usuario.id_rol else False
                
                print(f"Sesión guardada - Nombre: {request.session.get('usuario_nombre')}")
                print(f"Sesión guardada - Rol: {request.session.get('usuario_rol')}")
                print("✅ Login exitoso. Redirigiendo...")
                
                # ✅ CORREGIDO: Redirigir según el rol
                if request.session.get('es_admin'):
                    return redirect('panel')  # Admin va al panel de administración
                else:
                    return redirect('panel')  # Usuario normal va al panel principal
            else:
                print("❌ Contraseña incorrecta")
        except Usuarios.DoesNotExist:
            print(f"❌ Usuario no existe: {correo}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        return render(request, 'login.html', {'error': 'Credenciales incorrectas'})
    
    return render(request, 'login.html')


def panel(request):
    """Menú principal con botones para acceder a diferentes módulos"""
    print("=== PANEL PRINCIPAL ===")
    print(f"Session ID: {request.session.get('usuario_id')}")
    print(f"Session Nombre: {request.session.get('usuario_nombre')}")
    print(f"Session Rol: {request.session.get('usuario_rol')}")
    
    if not request.session.get('usuario_id'):
        print("No hay sesión, redirigiendo a login")
        return redirect('login')
    
    context = {
        'usuario_logueado': request.session.get('usuario_nombre', 'Invitado'),
        'usuario_rol': request.session.get('usuario_rol', 'Sin rol'),
        'es_admin': request.session.get('es_admin', False),
    }
    
    print(f"Context enviado - usuario_logueado: {context['usuario_logueado']}")
    print(f"Context enviado - usuario_rol: {context['usuario_rol']}")
    print(f"Es admin: {context['es_admin']}")
    
    return render(request, 'panel.html', context)


def admin_panel(request):
    """CRUD de usuarios - Solo para administradores"""
    print("=== PANEL DE ADMINISTRACIÓN ===")
    print(f"Session ID: {request.session.get('usuario_id')}")
    print(f"Session Nombre: {request.session.get('usuario_nombre')}")
    print(f"Session Rol: {request.session.get('usuario_rol')}")
    
    if not request.session.get('usuario_id'):
        print("No hay sesión, redirigiendo a login")
        return redirect('login')
    
    # Verificar que sea administrador
    if not request.session.get('es_admin'):
        print("❌ Usuario no es administrador, redirigiendo a panel principal")
        return redirect('panel')
    
    # Procesar POST (crear, editar, eliminar)
    if request.method == 'POST':
        action = request.POST.get('action')
        print(f"📝 Acción recibida: {action}")
        
        if action == 'crear':
            correo = request.POST.get('correo')
            
            # Validación: Verificar si el correo ya existe
            if Usuarios.objects.filter(correo=correo).exists():
                print(f"❌ Error: El correo {correo} ya existe")
                messages.error(request, f'❌ El correo "{correo}" ya está registrado')
                return redirect('admin.html')  # ✅ Corregido
                
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
            print(f"✅ Usuario creado: {usuario.nombre}")
        
        elif action == 'editar':
            usuario_id = request.POST.get('id')
            usuario = get_object_or_404(Usuarios, id_usuario=usuario_id)
            nuevo_correo = request.POST.get('correo')
            
            # Validación: Verificar si el nuevo correo ya existe (excluyendo el actual)
            if Usuarios.objects.filter(correo=nuevo_correo).exclude(id_usuario=usuario_id).exists():
                print(f"❌ Error: El correo {nuevo_correo} ya existe")
                messages.error(request, f'❌ El correo "{nuevo_correo}" ya está registrado por otro usuario')
                return redirect('admin.html')  # ✅ Corregido
            
            usuario.nombre = request.POST['nombre']
            usuario.apellido = request.POST['apellido']
            usuario.correo = nuevo_correo
            if request.POST.get('contrasena'):
                usuario.contrasena = request.POST['contrasena']
            usuario.id_rol_id = request.POST.get('id_rol')
            usuario.save()
            messages.success(request, f'✅ Usuario {usuario.nombre} actualizado exitosamente')
            print(f"✅ Usuario editado: {usuario.nombre}")
        
        elif action == 'eliminar':
            usuario_id = request.POST.get('id')
            
            # Evitar que el admin se elimine a sí mismo
            if int(usuario_id) == request.session.get('usuario_id'):
                messages.error(request, '❌ No puedes eliminar tu propia cuenta')
                return redirect('admin.html')  # ✅ Corregido
            
            usuario = get_object_or_404(Usuarios, id_usuario=usuario_id)
            nombre_usuario = usuario.nombre
            usuario.delete()
            messages.success(request, f'✅ Usuario {nombre_usuario} eliminado exitosamente')
            print(f"✅ Usuario eliminado ID: {usuario_id}")
        
        return redirect('admin.html')  # ✅ Corregido
    
    # Obtener datos para mostrar
    usuarios = Usuarios.objects.select_related('id_rol').all().order_by('-fecha_registro')
    roles = Rol.objects.filter(estado=1).all()
    
    print(f"Total usuarios encontrados: {usuarios.count()}")
    print(f"Roles disponibles: {roles.count()}")
    
    context = {
        'usuarios': usuarios,
        'roles': roles,
        'usuario_logueado': request.session.get('usuario_nombre', 'Invitado'),
        'usuario_rol': request.session.get('usuario_rol', 'Sin rol'),
        'es_admin': request.session.get('es_admin', False),
    }
    
    print(f"Context enviado - usuario_logueado: {context['usuario_logueado']}")
    print(f"Context enviado - usuario_rol: {context['usuario_rol']}")
    
    return render(request, 'admin.html', context)


def logout(request):
    request.session.flush()
    return redirect('login')