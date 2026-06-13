from django.urls import path
from . import views

urlpatterns = [
    # ================== VISTAS DE PANTALLA (TEMPLATES HTML) ==================
    path('', views.login, name='login'),
    path('panel/', views.panel, name='panel'),                                 # Menú principal / Dashboard
    path('admin.html/', views.admin_panel, name='admin.html'),
    path('logout/', views.logout, name='logout'),
    path('riesgo.html/', views.riesgo, name='riesgo'),                        # Pantalla de Gestión de Riesgos
    path('leccion.html/', views.leccion, name='leccion'),                      # Pantalla de Gestión de Lecciones

    # ================== APIs GRÁFICOS Y DASHBOARD GENERAL ==================
    path('api/reportes/listar/', views.listar_reportes_api, name='listar_reportes_api'),

    # ================== APIs MÓDULO DE RIESGOS ==================
    path('api/riesgos/listar/', views.listar_riesgos_api, name='listar_riesgos_api'),
    path('api/riesgos/crear/', views.crear_riesgo_api, name='crear_riesgo_api'),
    path('api/riesgos/actualizar/<int:id>/', views.actualizar_riesgo_api, name='actualizar_riesgo_api'),
    path('api/riesgos/eliminar/<int:id>/', views.eliminar_riesgo_api, name='eliminar_riesgo_api'),

    # ================== APIs MÓDULO DE LECCIONES APRENDIDAS ==================
    path('api/lecciones/listar/', views.listar_lecciones_api, name='listar_lecciones_api'),
    path('api/lecciones/crear/', views.crear_leccion_api, name='crear_leccion_api'),
    path('api/lecciones/actualizar/<int:id>/', views.actualizar_leccion_api, name='actualizar_leccion_api'),
    path('api/lecciones/eliminar/<int:id>/', views.eliminar_leccion_api, name='eliminar_leccion_api'),

    # ================== RUTAS UNIFICADAS SPRINT 1 ==================
    path('api/reportes/listar-tabla/', views.listar_reportes_tabla_api, name='listar_reportes_tabla_api'),
    path('reportes/listar-tabla/', views.vista_reportes_tabla, name='vista_reportes_tabla'),
    
    # Detalle de reporte específico (Funcionalidad 6 del Sprint 1)
    path('api/reportes/detalle/<int:id_reporte>/', views.detalle_reporte_unificado_api, name='detalle_reporte_unificado_api'),

    # ================== SPRINT 2: REPORTES Y AUDITORÍA (B.4 & B.5) ==================
    path('api/lecciones/exportar-csv/', views.exportar_lecciones_csv, name='exportar_lecciones_csv'),
    path('auditoria/', views.vista_auditoria, name='vista_auditoria'),
    path('api/auditoria/listar/', views.api_listar_auditoria, name='api_listar_auditoria'),
]