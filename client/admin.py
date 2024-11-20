from django.contrib import admin
from .models import UnitModel, CurrencyModel, SupplierModel, CategoryModel, ProductModel, StockModel, OfferModel

# Register your models here.

class UnitAdmin(admin.ModelAdmin):
    list_display = ['name', 'shortName']
    search_fields = ['name']

admin.site.register(UnitModel, UnitAdmin)

class CurrencyAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'countryCode']
    search_fields = ['code', 'countryCode']

admin.site.register(CurrencyModel, CurrencyAdmin)

class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'address', 'url']
    search_fields = ['name', 'address']

admin.site.register(SupplierModel, SupplierAdmin)

class CategoryAdmin(admin.ModelAdmin):
    list_display = ['uuid', 'parentUuid', 'name']
    list_filter = ['name', 'parentUuid']
    search_fields = ['name', 'uuid', 'parentUuid']
    
admin.site.register(CategoryModel, CategoryAdmin)

class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'quantity', 'unitUuid']
    list_filter = ['name', 'categories']
    search_fields = ['name', 'categories']

admin.site.register(ProductModel, ProductAdmin)

admin.site.register(StockModel)

admin.site.register(OfferModel)