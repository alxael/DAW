import uuid
from django.db import models
from django import forms
from django.utils import timezone
from django.urls import reverse
from django_prose_editor.fields import ProseEditorField
from django.contrib.auth.models import AbstractUser
from phonenumber_field.modelfields import PhoneNumberField

ORDER_STATUS = [
    (0, "New"),
    (1, "Processing"),
    (2, "Confirmed"),
    (3, "Delivering"),
    (4, "Received"),
    (5, "Completed")
]

PROFILE_FIELDS = [
    "email",
    "username",
    "is_email_confirmed",
    "is_blocked",
    "first_name",
    "last_name",
    "date_of_birth",
    "phone_number",
    "country",
    "city",
    "address_line_one",
    "address_line_two",
    "is_active",
    "is_staff",
    "is_superuser",
    "groups",
    "user_permissions",
    "last_login",
    "date_joined"
]


class ProfileModel(AbstractUser):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email_confirmation_code = models.UUIDField(null=True, blank=True)
    is_email_confirmed = models.BooleanField(default=False)
    date_of_birth = models.DateTimeField(null=True, blank=True)
    phone_number = PhoneNumberField()
    country = models.ForeignKey('cities_light.Country', on_delete=models.CASCADE, null=True, blank=True)
    city = models.ForeignKey('cities_light.City', on_delete=models.CASCADE, null=True, blank=True)
    address_line_one = models.CharField(max_length=100, null=True, blank=True)
    address_line_two = models.CharField(max_length=100, null=True, blank=True)
    is_following_newsletter = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)

    class Meta:
        permissions = [(f"change_user_{property_name}", f"Can change user {property_name}") for property_name in PROFILE_FIELDS]


class UnitModel(models.Model):
    uuid = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    short_name = models.CharField(max_length=10)

    def get_uuid_display(self):
        return self.short_name


class CurrencyModel(models.Model):
    uuid = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10)
    country = models.ForeignKey('cities_light.Country', on_delete=models.CASCADE, null=True, blank=True)

    def get_uuid_display(self):
        return self.name


class CurrencyConversionModel(models.Model):
    uuid = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False)
    source = models.ForeignKey(
        CurrencyModel, on_delete=models.PROTECT, null=True, blank=True, related_name="source")
    destination = models.ForeignKey(
        CurrencyModel, on_delete=models.PROTECT, null=True, blank=True, related_name="destination")
    rate = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True)
    date = models.DateTimeField(auto_now=True)


class SupplierModel(models.Model):
    uuid = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = ProseEditorField(blank=True)
    address = models.TextField(blank=True)
    url = models.URLField(blank=True)

    def get_uuid_display(self):
        return self.name


class CategoryModel(models.Model):
    uuid = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, max_length=100)
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True)

    def get_uuid_display(self):
        return self.name

    def get_parent_display(self):
        return self.parent.name

    def __str__(self):
        return self.name


class ProductModel(models.Model):
    uuid = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    quantity = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)
    unit = models.ForeignKey(
        UnitModel, on_delete=models.PROTECT, null=True, blank=True)
    description = models.TextField(blank=True, max_length=100)
    details = ProseEditorField(blank=True)
    categories = models.ManyToManyField(CategoryModel)

    def get_uuid_display(self):
        return self.name

    def get_unit_display(self):
        return f"{self.quantity:g} {self.unit.short_name}"

    def get_categories(self):
        return [{'uuid': category.uuid, 'name': category.name} for category in self.categories.all()]

    def clean(self):
        errors = {}

        if self.quantity and self.unit:
            quantity = str(int(self.quantity)).lower()
            unit_short_name = self.unit.short_name.lower()
            if quantity not in self.description.lower() and unit_short_name not in self.description.lower():
                errors['__all__'] = [
                    "Unit value or unit name should appear in product description at least once!"]

        if errors:
            raise forms.ValidationError(errors)

    def __str__(self):
        return self.name


class StockModel(models.Model):
    uuid = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(ProductModel, on_delete=models.RESTRICT)
    supplier = models.ForeignKey(SupplierModel, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    reception_date = models.DateTimeField()
    expiration_date = models.DateTimeField(null=True, blank=True)

    def get_product_display(self):
        return self.product.get_uuid_display()


class OfferModel(models.Model):
    uuid = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(ProductModel, on_delete=models.PROTECT)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    currency = models.ForeignKey(CurrencyModel, on_delete=models.PROTECT)
    last_changed = models.DateTimeField(auto_now=True)

    def get_price(self, currency_conversion):
        return f"{self.price * currency_conversion.rate:.2f}"

    def get_price_discounted(self, currency_conversion):
        return f"{(self.price * currency_conversion.rate * (1 - self.discount)):.2f}"

    def get_absolute_url(self):
        return reverse("offer-view", kwargs={"offer_uuid": self.uuid})


class OfferViewModel(models.Model):
    uuid = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False)
    offer = models.ForeignKey(OfferModel, on_delete=models.PROTECT)
    user = models.ForeignKey(ProfileModel, on_delete=models.PROTECT)
    date_time = models.DateTimeField(auto_now_add=True)


class PromotionModel(models.Model):
    uuid = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    subject = models.CharField(max_length=100)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    category = models.ForeignKey(CategoryModel, on_delete=models.PROTECT)
    discount = models.DecimalField(max_digits=10, decimal_places=3, default=0)

    def get_discount_display(self):
        return f"{int(self.discount * 100)}%"

    def get_category_display(self):
        return self.category.name

    def get_active(self):
        return self.start_date <= timezone.now() <= self.end_date


class OrderModel(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(ProfileModel, on_delete=models.PROTECT, null=True, blank=True)
    offers = models.ManyToManyField(OfferModel, through="OrderOfferModel")
    status = models.PositiveIntegerField(default=ORDER_STATUS[0], choices=ORDER_STATUS)
    full_address = models.CharField(max_length=200, default="")
    contact = models.CharField(max_length=200, default="")


class OrderOfferModel(models.Model):
    order = models.ForeignKey(OrderModel, on_delete=models.PROTECT)
    offer = models.ForeignKey(OfferModel, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=3, default=0)
