from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .forms import SignupForm, ProfileChangeForm
from .models import UnitModel, CurrencyModel, SupplierModel, CategoryModel, ProductModel, StockModel, OfferModel, OfferViewModel, PromotionModel, ProfileModel, OrderModel, OrderOfferModel

# Register your models here.


class UnitAdmin(admin.ModelAdmin):
    list_display = ['name', 'short_name']
    search_fields = ['name']


admin.site.register(UnitModel, UnitAdmin)


class CurrencyAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'country']
    search_fields = ['code', 'country']


admin.site.register(CurrencyModel, CurrencyAdmin)


class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'address', 'url']
    search_fields = ['name', 'address']


admin.site.register(SupplierModel, SupplierAdmin)


class CategoryAdmin(admin.ModelAdmin):
    list_display = ['uuid', 'parent', 'name']
    list_filter = ['name', 'parent']
    search_fields = ['name', 'uuid', 'parent']


admin.site.register(CategoryModel, CategoryAdmin)


class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'quantity', 'unit']
    list_filter = ['name', 'categories']
    search_fields = ['name', 'categories']


admin.site.register(ProductModel, ProductAdmin)


class StockAdmin(admin.ModelAdmin):
    list_display = ['product', 'supplier', 'quantity',
                    'unit', 'reception_date', 'expiration_date']
    list_filter = ['product', 'supplier',
                   'reception_date', 'expiration_date']
    search_fields = ['product', 'supplier',
                     'reception_date', 'expiration_date']


admin.site.register(StockModel, StockAdmin)

admin.site.register(OfferModel)

admin.site.register(OfferViewModel)

admin.site.register(PromotionModel)


class ProfileAdmin(UserAdmin):
    add_form = SignupForm
    form = ProfileChangeForm
    model = ProfileModel
    list_display = ["email", "username"]


admin.site.register(ProfileModel, ProfileAdmin)

admin.site.register(OrderModel)

admin.site.register(OrderOfferModel)
