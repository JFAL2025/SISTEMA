from django.shortcuts import render, redirect, get_object_or_404
from .models import Usuarios, Rol
from datetime import datetime

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
                return redirect('panel')
            else:
                print("❌ Contraseña incorrecta")
        except Usuarios.DoesNotExist:
            print(f"❌ Usuario no existe: {correo}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        return render(request, 'login.html', {'error': 'Credenciales incorrectas'})
    
    return render(request, 'login.html')

def panel(request):
    print("=== PANEL ===")
    print(f"Session ID: {request.session.get('usuario_id')}")
    print(f"Session Nombre: {request.session.get('usuario_nombre')}")
    print(f"Session Rol: {request.session.get('usuario_rol')}")
    
    if not request.session.get('usuario_id'):
        print("No hay sesión, redirigiendo a login")
        return redirect('login')
    
    usuarios = Usuarios.objects.select_related('id_rol').all().order_by('-fecha_registro')
    roles = Rol.objects.filter(estado=1).all()
    
    print(f"Total usuarios encontrados: {usuarios.count()}")
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'crear':
            usuario = Usuarios(
                nombre=request.POST['nombre'],
                apellido=request.POST['apellido'],
                correo=request.POST['correo'],
                contrasena=request.POST['contrasena'],
                id_rol_id=request.POST.get('id_rol'),
                fecha_registro=datetime.now()
            )
            usuario.save()
            print(f"Usuario creado: {usuario.nombre}")
        
        elif action == 'editar':
            usuario = get_object_or_404(Usuarios, id_usuario=request.POST['id'])
            usuario.nombre = request.POST['nombre']
            usuario.apellido = request.POST['apellido']
            usuario.correo = request.POST['correo']
            usuario.contrasena = request.POST['contrasena']
            usuario.id_rol_id = request.POST.get('id_rol')
            usuario.save()
            print(f"Usuario editado: {usuario.nombre}")
        
        elif action == 'eliminar':
            usuario = get_object_or_404(Usuarios, id_usuario=request.POST['id'])
            usuario.delete()
            print(f"Usuario eliminado ID: {request.POST['id']}")
        
        return redirect('panel')
    
    context = {
        'usuarios': usuarios,
        'roles': roles,
        'usuario_logueado': request.session.get('usuario_nombre', 'Invitado'),
        'usuario_rol': request.session.get('usuario_rol', 'Sin rol'),
        'es_admin': request.session.get('es_admin', False),
    }
    
    print(f"Context enviado - usuario_logueado: {context['usuario_logueado']}")
    print(f"Context enviado - usuario_rol: {context['usuario_rol']}")
    
    return render(request, 'login.html', context)

def logout(request):
    request.session.flush()
    return redirect('login')