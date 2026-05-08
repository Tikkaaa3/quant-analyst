from django.urls import path
from . import views

urlpatterns = [
    path("", views.analysis_lab, name="analysis_lab"),
    path('run_analysis/', views.run_analysis, name='run_analysis'),
    path("vault/", views.vault, name="vault"),
]
