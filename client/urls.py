from django.urls import path
from . import views

urlpatterns = [
    path("product/list", views.products_list, name="products-list"),
    path("", views.index, name="index")
]