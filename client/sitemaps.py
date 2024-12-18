from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import OfferModel


class OfferSitemap(Sitemap):
    changefreq = "weekly"
    priority = 1

    def items(self):
        return OfferModel.objects.all().order_by("uuid")

    def lastmod(self, obj):
        return obj.last_changed


class StaticViewsSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.8

    def items(self):
        return [
            "sign-in",
            'sign-up',
            'sign-out',
            'profile',
            'change-password',
            'offer-list',
            'presentation'
        ]

    def location(self, item):
        return reverse(item)
