from django.urls import path
from . import views


urlpatterns = [
    path('', views.getData),
    path('approve/', views.processData),
    path('getCsv/', views.getCsv),
]