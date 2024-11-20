from .models import ProductModel

class ProductForListDto(dict):
    def __init__(self, product_model: ProductModel):
        self['uuid'] = product_model.uuid
        self['name'] = product_model.name
        self['description'] = product_model.description
        self['details'] = product_model.details
        self['categories'] = product_model.get_categories()
        self['unit'] = product_model.get_unit()
        