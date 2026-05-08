from django.urls import path
from . import views

urlpatterns = [
    path("", views.analysis_lab, name="analysis_lab"),
]
