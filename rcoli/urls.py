from django.urls import path
from . import views

urlpatterns = [
    path("add_comics_and_issues", views.add_comics_and_issues),
    path("add_pages", views.add_pages),
    path("add_pages_missing_issues", views.add_pages_missing_issues),
]
