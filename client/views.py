from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from .models import ProductModel
from .forms import FilterProductsForm, ContactForm
from .dto import ProductListDto

def index(request):
    contact_form = ContactForm()
    if request.method == 'POST':
        contact_form = ContactForm(request.POST)
        if contact_form.is_valid():
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'errors': contact_form.errors})
    return render(request, 'presentation-page.html', {'completed': False, 'form': contact_form})

def products_list(request):
    all_products = ProductModel.objects.all()
    if request.method == 'POST':
        filter_form = FilterProductsForm(request.POST)
        if filter_form.is_valid():
            name = filter_form.cleaned_data['name']
            if name:
                all_products = all_products.filter(name__contains=name)
            categories = filter_form.cleaned_data['categories']
            if categories:
                all_products = all_products.filter(categories__in=[categories.uuid])
        products = [ProductListDto(product) for product in all_products]
        return JsonResponse({'products': products})
    filter_form = FilterProductsForm()
    return render(request, 'products-page.html', {'form': filter_form})
