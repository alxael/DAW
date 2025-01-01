from .models import ProductModel, OfferModel, PromotionModel, CurrencyModel, CurrencyConversionModel


class ProductListDto(dict):
    def __init__(self, product_model: ProductModel):
        self['uuid'] = product_model.uuid
        self['name'] = product_model.name
        self['description'] = product_model.description
        self['categories'] = product_model.get_categories()


class OfferListDto(dict):
    def __init__(self, offer_model: OfferModel, currency_model: CurrencyModel):
        self['uuid'] = offer_model.uuid
        self['name'] = offer_model.product.name
        self['description'] = offer_model.product.description
        self['categories'] = offer_model.product.get_categories()

        currency_conversion = CurrencyConversionModel.objects.get(source=offer_model.currency, destination=currency_model)
        self['price'] = offer_model.get_price(currency_conversion)
        self['price_discounted'] = offer_model.get_price_discounted(currency_conversion)


class PromotionListDto(dict):
    def __init__(self, promotion_model: PromotionModel):
        self['uuid'] = promotion_model.uuid
        self['name'] = promotion_model.name
        self['category_name'] = promotion_model.get_category_display()
        self['discount'] = promotion_model.get_discount_display()
        self['start_date'] = promotion_model.start_date
        self['end_date'] = promotion_model.end_date
        self['active'] = promotion_model.get_active()


class CurrencyListDto(dict):
    def __init__(self, currency_model: CurrencyModel):
        self['uuid'] = currency_model.uuid
        self['name'] = currency_model.name
        self['code'] = currency_model.code
