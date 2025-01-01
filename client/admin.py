from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .forms import ProfileChangeAdminForm, SignupForm
from .models import UnitModel, CurrencyModel, CurrencyConversionModel, SupplierModel, CategoryModel, ProductModel, StockModel, OfferModel, OfferViewModel, PromotionModel, ProfileModel, OrderModel, OrderOfferModel, PROFILE_FIELDS

# Register your models here.


class UnitAdmin(admin.ModelAdmin):
    list_display = ['name', 'short_name']
    search_fields = ['name']


admin.site.register(UnitModel, UnitAdmin)


class CurrencyAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'country']
    search_fields = ['code', 'country']


admin.site.register(CurrencyModel, CurrencyAdmin)


class CurrencyConversionAdmin(admin.ModelAdmin):
    list_display = ['source', 'destination', 'rate']
    search_fields = ['source', 'destination']


admin.site.register(CurrencyConversionModel, CurrencyConversionAdmin)


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
                    'reception_date', 'expiration_date']
    list_filter = ['product', 'supplier',
                   'reception_date', 'expiration_date']
    search_fields = ['product', 'supplier',
                     'reception_date', 'expiration_date']


admin.site.register(StockModel, StockAdmin)

admin.site.register(OfferModel)

admin.site.register(OfferViewModel)

admin.site.register(PromotionModel)


class ProfileAdmin(UserAdmin):
    list_display = ["email", "username", "is_email_confirmed"]
    search_fields = ["email", "username"]

    form = ProfileChangeAdminForm
    add_form = SignupForm
    model = ProfileModel

    def get_form(self, request, obj=None, **kwargs):
        kwargs['form'] = self.form
        form = super().get_form(request, obj, **kwargs)

        class CreateChangeProfileForm(form):
            def __init__(self, *args, **kwargs):
                kwargs['current_user'] = request.user
                super().__init__(*args, **kwargs)

        return CreateChangeProfileForm

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        for field in PROFILE_FIELDS:
            if not request.user.has_perm(f"auth.change_user_{field}"):
                readonly_fields.append(field)
        return readonly_fields

    fieldsets = [
        ("General",
         {
             "fields": [
                 "email",
                 "username",
                 "is_email_confirmed",
                 "is_blocked"
             ]
         }),
        ("Personal information",
         {
             "fields": [
                 "first_name",
                 "last_name",
                 "date_of_birth",
                 "phone_number",
                 "country",
                 "city",
                 "address_line_one",
                 "address_line_two"
             ]
         }),
        ("Permissions",
         {
             "fields": [
                 "is_active",
                 "is_staff",
                 "is_superuser",
                 "groups",
                 "user_permissions",
             ],
         }),
        ("Important dates",
         {
             "fields": [
                 "last_login",
                 "date_joined"
             ],
         })
    ]

    add_fieldsets = [
        ("General",
         {
             "fields": [
                 "email",
                 "username",
                 "is_email_confirmed",
                 "is_blocked"
             ]
         }),
        ("Personal information",
         {
             "fields": [
                 "first_name",
                 "last_name",
                 "date_of_birth",
                 "phone_number",
                 "country",
                 "city",
                 "address_line_one",
                 "address_line_two"
             ]
         }),
        ("Permissions",
         {
             "fields": [
                 "is_active",
                 "is_staff",
                 "is_superuser",
                 "groups",
                 "user_permissions",
             ],
         }),
        ("Important dates",
         {
             "fields": [
                 "last_login",
                 "date_joined"
             ],
         })
    ]


admin.site.register(ProfileModel, ProfileAdmin)

admin.site.register(OrderModel)

admin.site.register(OrderOfferModel)
