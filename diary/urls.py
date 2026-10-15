from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('save/', views.save_entry, name='save'),
    path('reset/', views.reset_entries, name='reset'),
    path('toggle-theme/', views.toggle_theme, name='toggle_theme'),
    path('generate-share/', views.generate_share_token, name='generate_share'),
    path('share/<str:token>/', views.share_view, name='share_view')
]