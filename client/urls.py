from django.urls import path
from . import views

urlpatterns = [
    path("", views.presentation, name="presentation"),
    path("signin", views.sign_in, name="sign-in"),
    path("signup", views.sign_up, name="sign-up"),
    path("signout", views.sign_out, name="sign-out"),
    path("profile", views.profile, name="profile"),
    path("change-password", views.change_password, name="change-password"),
    path("product/list", views.product_list, name="product-list"),
    path("product/add", views.product_add, name="product-add"),
    path("product/edit/<product_uuid>", views.product_edit, name="product-edit"),
    path("product/delete/<product_uuid>", views.product_delete, name="product-delete")
]
