from django.urls import path, include
from . import views

auth_urlpatterns = [
    path("signin", views.sign_in, name="sign-in"),
    path("signup", views.sign_up, name="sign-up"),
    path("signout", views.sign_out, name="sign-out"),
    path("profile", views.profile, name="profile"),
    path("change-password", views.change_password, name="change-password"),
    path("email-confirmation/<email_confirmation_uuid>", views.email_confirmation, name="email-confirmation")
]

product_urlpatterns = [
    path("list", views.product_list, name="product-list"),
    path("add", views.product_add, name="product-add"),
    path("edit/<product_uuid>", views.product_edit, name="product-edit"),
    path("delete/<product_uuid>", views.product_delete, name="product-delete")
]

offer_urlpatterns = [
    path("list", views.offer_list, name="offer-list"),
    path("view/<offer_uuid>", views.offer_view, name="offer-view")
]

promotion_urlpatterns = [
    path("list", views.promotion_list, name="promotion-list"),
    path("add", views.promotion_add, name="promotion-add"),
    path("delete/<promotion_uuid>", views.promotion_delete, name="promotion-delete")
]

urlpatterns = [
    path("", views.presentation, name="presentation"),
    path("", include(auth_urlpatterns)),
    path("product/", include(product_urlpatterns)),
    path("offer/", include(offer_urlpatterns)),
    path("promotion/", include(promotion_urlpatterns))
]
