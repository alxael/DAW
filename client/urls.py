from django.urls import path
from . import views

urlpatterns = [
    path("", views.presentation, name="presentation"),
    path("product/list", views.product_list, name="product-list"),
    path("product/add", views.product_add, name="product-add"),
    path("product/edit/<product_uuid>", views.product_edit, name="product-edit"),
    path("product/delete/<product_uuid>", views.product_delete, name="product-delete")
]