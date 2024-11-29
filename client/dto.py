from .models import ProductModel


class ProductListDto(dict):
    def __init__(self, product_model: ProductModel):
        self['uuid'] = product_model.uuid
        self['name'] = product_model.name
        self['description'] = product_model.description
        self['categories'] = product_model.get_categories()
