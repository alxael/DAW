import uuid
from django.db import models

class UnitModel(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    shortName = models.CharField(max_length=10)
    
class CurrencyModel(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10)
    countryCode = models.CharField(max_length=10, blank=True)
    
class SupplierModel(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    address = models.TextField(blank=True)
    url = models.URLField(blank=True)
    
class CategoryModel(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    parentUuid = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    
class ProductModel(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    unitUuid = models.ForeignKey(UnitModel, on_delete=models.PROTECT, null=True, blank=True)
    description = models.TextField(blank=True)
    details = models.TextField(blank=True)
    categories = models.ManyToManyField(CategoryModel)
    
    def get_categories(self):
        return [(category.uuid, category.name) for category in self.categories.all()]
    def get_unit(self):
        return f"{self.quantity} {self.unitUuid.shortName}"
    
class StockModel(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    productUuid = models.ForeignKey(ProductModel, on_delete=models.RESTRICT)
    supplierUuid = models.ForeignKey(SupplierModel, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unitUuid = models.ForeignKey(UnitModel, on_delete=models.PROTECT)
    receptionDate = models.DateTimeField()
    expirationDate = models.DateTimeField(null=True, blank=True)
    
class OfferModel(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    stockUuid = models.ForeignKey(StockModel, on_delete=models.PROTECT)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currencyUuid = models.ForeignKey(CurrencyModel, on_delete=models.PROTECT)
    expirationDate = models.DateTimeField(null=True, blank=True)
    
modelsList = [UnitModel, CurrencyModel, SupplierModel, CategoryModel, ProductModel, StockModel, OfferModel]