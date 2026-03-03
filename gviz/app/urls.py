from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('load-plugin/', views.load_plugin, name='load_plugin'),
]
