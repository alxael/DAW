import re
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, update_session_auth_hash
from django.http import JsonResponse, Http404
from django.contrib.auth.decorators import login_required
from .models import ProductModel, UnitModel
from .forms import FilterProductsForm, ProductAddEditForm, ContactForm, SigninForm, SignupForm, ChangePasswordForm
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
        return render(request, 'pages/presentation/presentation.html', {'completed': False, 'form': contact_form})
    else:
        return Http404()


def add_data_to_session(request, user):
    request.session["username"] = user.username
    request.session["email"] = user.email

    fullname = ""
    if user.first_name:
        fullname += user.first_name + " "
    if user.last_name:
        fullname += user.last_name
    print(fullname)
    request.session["fullname"] = fullname

    request.session["dateofbirth"] = user.dateOfBirth.strftime("%d/%m/%Y") if user.dateOfBirth else ""
    request.session["phonenumber"] = user.phoneNumber.as_international if user.phoneNumber else ""

    location = ""
    if user.country:
        location += user.country.name + " "
    if user.city:
        location += user.city.name
    request.session["location"] = location

    address = ""
    if user.addressLineOne:
        address += user.addressLineOne + " "
    if user.addressLineTwo:
        address += user.addressLineTwo
    request.session["address"] = address

    request.session.modified = True


def sign_up(request):
    if request.method == "POST":
        sign_up_form = SignupForm(request.POST)
        if sign_up_form.is_valid():
            user = sign_up_form.save()
            add_data_to_session(request, user)
            return JsonResponse({"success": True})
        else:
            return JsonResponse({"success": False, "errors": sign_up_form.errors})
    elif request.method == "GET":
        sign_up_form = SignupForm()
        return render(request, "pages/auth/signup.html", {"form": sign_up_form})
    else:
        return Http404()


def sign_in(request):
    if request.method == "POST":
        sign_in_form = SigninForm(request, data=request.POST)
        if sign_in_form.is_valid():
            user = sign_in_form.get_user()
            login(request, user)

            session_expiry_time = 0 if not sign_in_form.cleaned_data["stay_signed_in"] else 24 * 60 * 60
            request.session.set_expiry(session_expiry_time)

            add_data_to_session(request, user)

            return JsonResponse({"success": True})
        else:
            return JsonResponse({"success": False, "errors": sign_in_form.errors})
    elif request.method == "GET":
        sign_in_form = SigninForm()
        return render(request, "pages/auth/signin.html", {"form": sign_in_form})
    else:
        return Http404()


@login_required
def sign_out(request):
    if request.method == "POST":
        logout(request)
        return JsonResponse({"success": True})
    else:
        return Http404()


@login_required
def change_password(request):
    if request.method == "POST":
        change_password_form = ChangePasswordForm(user=request.user, data=request.POST)
        if change_password_form.is_valid():
            change_password_form.save()
            update_session_auth_hash(request, request.user)
            return JsonResponse({"success": True})
        else:
            return JsonResponse({"success": False, "errors": change_password_form.errors})
    elif request.method == "GET":
        change_password_form = ChangePasswordForm(user=request.user)
        return render(request, "pages/auth/change-password.html", {"form": change_password_form})
    else:
        return Http404()


@login_required
def profile(request):
    return render(request, "pages/auth/profile.html")


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


@login_required
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
        return Http404()


@login_required
def product_add(request):
    if request.method == 'POST':
        add_form = ProductAddEditForm(request.POST)
        return process_product_form(add_form)
    elif request.method == 'GET':
        add_form = ProductAddEditForm()
        return render(request, 'pages/product/product-add.html', {'form': add_form})
    else:
        return Http404()


@login_required
def product_edit(request, product_uuid):
    if request.method == 'POST':
        existing_product = ProductModel.objects.get(uuid=product_uuid)
        edit_form = ProductAddEditForm(request.POST, instance=existing_product)
        return process_product_form(edit_form)
    elif request.method == 'GET':
        product = ProductModel.objects.get(uuid=product_uuid)
        edit_form = ProductAddEditForm(instance=product, initial={
                                       "unit": f"{product.quantity: g} {product.unitUuid.shortName}"})
        return render(request, 'pages/product/product-edit.html', {'form': edit_form})
    else:
        return Http404()


@login_required
def product_delete(request, product_uuid):
    if request.method == 'DELETE':
        try:
            existing_product = ProductModel.objects.get(uuid=product_uuid)
            existing_product.delete()
            return JsonResponse({'success': True})
        except ...:
            return JsonResponse({'success': False})
    else:
        return Http404()
