from django.urls import path
from . import views

urlpatterns = [
    path("add_comics_and_issues", views.add_comics_and_issues),
]
