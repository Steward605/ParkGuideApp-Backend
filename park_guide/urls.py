"""
URL configuration for park_guide project.
"""
from django.urls import path, include

urlpatterns = [
    # Fresh API routes MUST come FIRST to avoid conflicts with dashboard api/* patterns
    path('api/', include('courses.urls_fresh')),  # Fresh API - complete rewrite
    path('api/notifications/', include('notifications.urls')),
    path('api/user-progress/', include('user_progress.urls')),
    path('api/secure-files/', include('secure_files.urls')),
    path('api/accounts/', include('accounts.urls')),
    
    # Dashboard routes (includes conflicting api/* patterns, so must come after)
    path('', include('dashboard.urls')),
    # Admin disabled - not needed for this app
    # path('admin/', admin_site.urls),
]
