
from django.contrib import admin
from django.urls import path,include
from . import views
from django.conf import settings
from django.conf.urls.static import static



urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('blogs/',views.blog_page,name='blog'),
    path('conttact/',views.contact,name='contact'),
    path('user/', include('movies_and_user.urls')),
    path('user/', include('custom_admin.urls')),
    path('trending/view-all/', views.view_all_trending_home, name='view_all_trending'),
    path('popular/view-all/', views.view_all_popular_home, name='view_all_popular'),
    path('recently-added/view-all-recently-added/',views.view_all_recently_add_home,name='view_all_recently_added'),
    path('movie_detail/<int:movie_id>/',views.movies_detail_home,name='movie_detail'),
    path('category/<str:category_name>/', views.movies_by_category_home, name='movies_by_category'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)