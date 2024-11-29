import re
import bleach
from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import ProductModel, UnitModel
from .forms import FilterProductsForm, ProductAddEditForm, ContactForm
from .dto import ProductListDto


def presentation(request):
    if request.method == 'POST':
        contact_form = ContactForm(request.POST)
        if contact_form.is_valid():
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'errors': contact_form.errors})
    elif request.method == 'GET':
        contact_form = ContactForm()
        return render(request, 'pages/presentation.html', {'completed': False, 'form': contact_form})
    else:
        # add 404 page here
        return JsonResponse({"title": "404 page should go here"})


def process_product_form(product_form):
    if product_form.is_valid():
        product = product_form.save(commit=False)

        unit = product_form.cleaned_data['unit']
        unit = re.sub(r" {2,}", ' ', unit)

        quantity = float(unit.split(' ')[0].strip())
        unit_short_name = unit.split(' ')[1].lower().strip()

        try:
            unit_uuid = UnitModel.objects.get(shortName=unit_short_name)
        except UnitModel.DoesNotExist:
            product_form.errors["unit"] = ["Could not find specified unit!"]
            return JsonResponse({'success': False, 'errors': product_form.errors})

        product.quantity = quantity
        product.unitUuid = unit_uuid

        product.save()
        product_form.save_m2m()

        return JsonResponse({'success': True})
    else:
        return JsonResponse({'success': False, 'errors': product_form.errors})


def product_list(request):
    all_products = ProductModel.objects.all()
    if request.method == 'POST':
        filter_form = FilterProductsForm(request.POST)
        if filter_form.is_valid():
            name = filter_form.cleaned_data['name']
            if name:
                all_products = all_products.filter(name__contains=name)
            categories = filter_form.cleaned_data['categories']
            if categories:
                all_products = all_products.filter(
                    categories__in=[categories.uuid])
        products = [ProductListDto(product) for product in all_products]
        return JsonResponse({'products': products})
    elif request.method == 'GET':
        filter_form = FilterProductsForm()
        return render(request, 'pages/product/product-list.html', {'form': filter_form})
    else:
        return redirect('presentation')


def product_add(request):
    if request.method == 'POST':
        add_form = ProductAddEditForm(request.POST)
        return process_product_form(add_form)
    elif request.method == 'GET':
        add_form = ProductAddEditForm()
        return render(request, 'pages/product/product-add.html', {'form': add_form})
    else:
        return redirect('presentation')


def product_edit(request, product_uuid):
    if request.method == 'POST':
        existing_product = ProductModel.objects.get(uuid=product_uuid)
        edit_form = ProductAddEditForm(request.POST, instance=existing_product)
        return process_product_form(edit_form)
    elif request.method == 'GET':
        product = ProductModel.objects.get(uuid=product_uuid)
        edit_form = ProductAddEditForm(instance=product, initial={"unit": f"{
                                       product.quantity:g} {product.unitUuid.shortName}"})
        return render(request, 'pages/product/product-edit.html', {'form': edit_form})
    else:
        return redirect('presentation')


def product_delete(request, product_uuid):
    if request.method == 'DELETE':
        try:
            existing_product = ProductModel.objects.get(uuid=product_uuid)
            existing_product.delete()
            return JsonResponse({'success': True})
        except ...:
            return JsonResponse({'success': False})
    else:
        return redirect('presentation')
