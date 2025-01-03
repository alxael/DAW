from django.urls import path, include
from django.contrib.sitemaps.views import sitemap
from django.conf import settings
from django.conf.urls.static import static
from .sitemaps import StaticViewsSitemap, OfferSitemap
from . import views

sitemaps = {
    'offer': OfferSitemap,
    'static': StaticViewsSitemap
}

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
    path("view/<offer_uuid>", views.offer_view, name="offer-view"),
    path("cart/", views.cart, name="offer-cart"),
]

promotion_urlpatterns = [
    path("list", views.promotion_list, name="promotion-list"),
    path("add", views.promotion_add, name="promotion-add"),
    path("edit/<promotion_uuid>", views.promotion_edit, name="promotion-edit"),
    path("delete/<promotion_uuid>", views.promotion_delete, name="promotion-delete")
]

stock_urlpatterns = [
    path("list/offers", views.stock_list_offers, name="stock-list-offers")
]

currency_urlpatterns = [
    path("list", views.currency_list, name="currency-list")
]

order_urlpatters = [
    path("list", views.order_list, name="order-list"),
    path("add", views.order_add, name="order-add")
]

urlpatterns = [
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path("", views.presentation, name="presentation"),
    path("", include(auth_urlpatterns)),
    path("product/", include(product_urlpatterns)),
    path("offer/", include(offer_urlpatterns)),
    path("promotion/", include(promotion_urlpatterns)),
    path("stock/", include(stock_urlpatterns)),
    path("currency", include(currency_urlpatterns)),
    path("order/", include(order_urlpatters))
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
