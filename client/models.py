import uuid
from django.db import models
from django import forms
from django_prose_editor.fields import ProseEditorField


class UnitModel(models.Model):
    uuid = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    shortName = models.CharField(max_length=10)

    def get_uuid_display(self):
        return self.shortName


class CurrencyModel(models.Model):
    uuid = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10)
    countryCode = models.CharField(max_length=10, blank=True)

    def get_uuid_display(self):
        return self.name


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
    parentUuid = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True)

    def get_uuid_display(self):
        return self.name


class ProductModel(models.Model):
    uuid = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    quantity = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)
    unitUuid = models.ForeignKey(
        UnitModel, on_delete=models.PROTECT, null=True, blank=True)
    description = models.TextField(blank=True, max_length=100)
    details = ProseEditorField(blank=True)
    categories = models.ManyToManyField(CategoryModel)

    def get_uuid_display(self):
        return self.name

    def get_categories(self):
        return [{'uuid': category.uuid, 'name': category.name} for category in self.categories.all()]

    def clean(self):
        errors = {}

        unit = (str(int(self.quantity)) + " " +
                self.unitUuid.shortName).lower()
        if unit not in self.description.lower():
            errors['__all__'] = [
                "Unit should appear in product description at least once!"]

        if errors:
            raise forms.ValidationError(errors)


class StockModel(models.Model):
    uuid = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False)
    productUuid = models.ForeignKey(ProductModel, on_delete=models.RESTRICT)
    supplierUuid = models.ForeignKey(SupplierModel, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unitUuid = models.ForeignKey(UnitModel, on_delete=models.PROTECT)
    receptionDate = models.DateTimeField()
    expirationDate = models.DateTimeField(null=True, blank=True)

    def get_productUuid_display(self):
        return self.productUuid.get_uuid_display()


class OfferModel(models.Model):
    uuid = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False)
    stockUuid = models.ForeignKey(StockModel, on_delete=models.PROTECT)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currencyUuid = models.ForeignKey(CurrencyModel, on_delete=models.PROTECT)
    expirationDate = models.DateTimeField(null=True, blank=True)
