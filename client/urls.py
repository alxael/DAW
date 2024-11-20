from django.urls import path, re_path
from . import views

urlpatterns = [
    path("products-list", views.products_list, name="products-list")
]