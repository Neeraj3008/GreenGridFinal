from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.energy_dashboard_view, name='home'),
    path('dashboard/', views.energy_dashboard_view, name='energy_dashboard'),
    path("meter-data/<str:meter_id>/", views.meter_data_view, name="meter_data"),
    path("summary-data/", views.summary_data_view, name="summary_data"),
    



]
