from django.urls import path
from . import views

urlpatterns = [
    # path('add_comic/', views.AddComicView.as_view(), name='add_comic'),
    path('get_all_comics', views.get_all_comics),
    path('get_comic/<int:comic_id>', views.get_comic),
    path('search_comics', views.search_comics),
    path('add_comic', views.add_comic),
    path('update_comic/<int:comic_id>', views.update_comic),
    path('delete_comic/<int:comic_id>', views.delete_comic),
]