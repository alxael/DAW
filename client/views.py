from django.core import serializers
from django.http import HttpResponse, JsonResponse
from .models import ProductModel
from .dto import ProductForListDto
from .forms import ProductForm
import json

def products_list(request):
    all_products = ProductModel.objects.all()
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            all_products = ProductModel.objects.filter(name__contains=name)
    products = [ProductForListDto(product) for product in all_products]
    return JsonResponse({'products': products})