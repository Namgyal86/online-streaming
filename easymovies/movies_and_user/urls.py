from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views


urlpatterns = [
    # Authentication URLs
    path('signup/', views.register_view, name='signup_page'),
    path('login/', views.login_view, name='login_page'),
    path('logout/',views.logout_view,name='logout'),
    path('admin-dashboard',views.admin_dashboard,name='admin_dashboard'),
    path('admin-search/', views.admin_search, name='admin_search'),
    path('user-dashboard/',views.user_dashboard,name='user_dashboard'),
    path('admin_dadhboard/add-admin/',views.add_admin,name='add-admin'),
    path('admin_dadhboard/add-movies/',views.add_movies,name='add-movies'),
    path('delete-movie/<int:movie_id>/', views.delete_movie, name='delete_movie'),
    path('movies-details/', views.movies_detail, name='movies-details'),
    path('user-profile/',views.user_profile,name='user-profile'),
    path('watch/<int:movie_id>', views.watch_movies, name='watch_movies'),
    path('user-detail/',views.admin_user_details,name='user-details'),
    path('subscription/',views.subscription_page,name='subscription'),
    path('user-detail/edit/<int:user_id>/', views.admin_edit_user, name='edit_user'),
    path('user-detail/delete/<int:user_id>/', views.delete_user, name='delete_user'),
    path('payment_page/<int:subscription_id>/<int:package_id>/', views.payment_page, name='payment_page'),
    path('movie-stream/<int:movie_id>/',views.movie_stream,name='movie_stream'),
    path('add-review/<int:movie_id>/',views.add_review,name='add_review'),
    path('esewa/payment/<int:subscription_id>/', views.esewa_payment_page, name='esewa_payment'),
    path('esewa/payment/success/<int:subscription_id>/', views.esewa_success, name='esewa_success'),
    path('esewa/payment/failure/<int:subscription_id>/', views.esewa_failure, name='esewa_failure'),
    path('payment_failed/<int:subscription_id>/', views.payment_failed, name='payment_failed'),
    path('init_khalti_payment/<int:subscription_id>/', views.init_khalti_payment, name='init_khalti_payment'),
    path('verify-khalti/<int:subscription_id>/', views.verify_khalti, name='verify_khalti'),
    path('recommendations/view-all/', views.view_all_recommendations, name='view_all_recommendations'),
    path('trending/view-all/', views.view_all_trending, name='view_all_trending'),
    path('popular/view-all/', views.view_all_popular, name='view_all_popular'),
    path('recently-added/view-all-recently-added/',views.view_all_recently_add,name='view_all_recently_added'),
    path('category/<str:category_name>/', views.movies_by_category, name='movies_by_category'),
    path('about-movie/<int:movie_id>/',views.about_movie,name='about_movie'),
    path('search/', views.movie_search, name='movie_search'),
    path('add-package/', views.add_package, name='add-package'),
    path('edit-package/<int:package_id>/', views.edit_package, name='edit-package'),
    path('delete-package/<int:package_id>/', views.delete_package, name='delete-package'),

    #reset password
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password_reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password_reset/complete/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
]

#Serve media files in development
if settings.DEBUG:
   urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
