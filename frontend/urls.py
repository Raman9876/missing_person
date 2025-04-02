from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from .views import home, upload_view, feed_view
from . import views  # ✅ Add this import


urlpatterns = [
    path('', home, name="home"),
    path('upload_view/', upload_view, name="upload_view"),
    path('update_location/', views.update_location, name='update_location'),
    path('feed/', feed_view, name="feed"),  # Page to view all missing reports
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
