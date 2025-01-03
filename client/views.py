import re
import io
import uuid
import json
import time
import logging
from datetime import datetime
from ipware import get_client_ip
from reportlab.pdfgen import canvas
from django import forms
from django.conf import settings
from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.models import Permission
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseNotFound
from django.core.paginator import Paginator, EmptyPage
from django.template.loader import get_template, TemplateDoesNotExist
from django.db.models import Count
from .models import ProductModel, UnitModel, ProfileModel, OfferModel, OfferViewModel, PromotionModel, StockModel, CurrencyModel, OrderModel, OrderOfferModel, CurrencyConversionModel
from .forms import FilterProductsForm, ProductAddEditForm, FilterOffersForm, FilterPromotionsForm, PromotionAddEditForm, ContactForm, SigninForm, SignupForm, ChangePasswordForm
from .dto import ProductListDto, OfferListDto, PromotionListDto, CurrencyListDto, OrderListDto
from .tasks import send_email_html, send_promotion_emails_html, send_email_admins_html, calculate_discounts

# Utilities

logger = logging.getLogger('django')


def snake_case(s):
    return '_'.join(
        re.sub('([A-Z][a-z]+)', r' \1',
               re.sub('([A-Z]+)', r' \1',
                      s.replace('-', ' '))).split()).lower()


def get_ip_address(request):
    ip_address, _is_routable = get_client_ip(request)
    if ip_address is None:
        logger.warning(f"Could not determine IP address for request: {request}")
        ip_address = "Could not be determined"
    return ip_address


def get_response_forbidden(request, template_data):
    template_path = "pages/responses/403.html"
    template_data["username"] = None if not request.user else request.user.username
    return HttpResponseForbidden(render(request, template_path, template_data))

# Custom decorators


def signin_required(function):
    def wrapper(request, *args, **kwargs):
        if request.user.is_anonymous:
            return get_response_forbidden(
                request,
                {
                    "title": "Forbidden",
                    "custom_message": "You must be authenticated to view this page!"
                }
            )
        response = function(request, *args, **kwargs)
        return response
    return wrapper


def permissions_required(permissions):
    def decorator(function):
        def wrapper(request, *args, **kwargs):
            for permission in permissions:
                if not request.user.has_perm(f"client.{permission}"):
                    permission_description = Permission.objects.all().get(codename=permission).name[3:]
                    return get_response_forbidden(request, {"custom_message": f"You do not have the permissions to {permission_description}!"})
            response = function(request, *args, **kwargs)
            return response
        return wrapper
    return decorator

# Pagination


def get_paginated_objects(request, objects_list):
    page_number = request.GET.get("page_number", 1)
    records_per_page = request.GET.get("records_per_page", 10)
    paginator = Paginator(objects_list, per_page=records_per_page)
    try:
        objects_list = paginator.page(page_number).object_list
        pages = list(paginator.get_elided_page_range(page_number, on_each_side=1, on_ends=2))
    except EmptyPage:
        logger.critical("Invalid page number! Could not paginate objects, reverting to default values.")
        page_number, records_per_page = 1, 10
        objects_list = paginator.page(page_number).object_list
        pages = list(paginator.get_elided_page_range(page_number, on_each_side=1, on_ends=2))
    return (objects_list, pages)


# Presentation


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
        return HttpResponseNotFound()

# Authentication


def add_data_to_session(request, user):
    request.session["username"] = user.username
    request.session["email"] = user.email

    fullname = ""
    if user.first_name:
        fullname += user.first_name + " "
    if user.last_name:
        fullname += user.last_name
    request.session["fullname"] = fullname

    request.session["date_of_birth"] = user.date_of_birth.strftime("%d/%m/%Y") if user.date_of_birth else ""
    request.session["phone_number"] = user.phone_number.as_international if user.phone_number else ""

    location = ""
    if user.country:
        location += user.country.name + " "
    if user.city:
        location += user.city.name
    request.session["location"] = location

    address = ""
    if user.address_line_one:
        address += user.address_line_one + " "
    if user.address_line_two:
        address += user.address_line_two
    request.session["address"] = address

    request.session.modified = True


def sign_up(request):
    if request.method == "POST":
        sign_up_form = SignupForm(request.POST)

        if sign_up_form.data["username"] in settings.FORBIDDEN_USERNAMES and not sign_up_form.is_valid():
            send_email_admins_html.delay(
                "emails/signup-forbidden-username.html",
                {"username": sign_up_form.data["username"], "ip_address": get_ip_address(request), "datetime": datetime.now()},
                "Suspicious sign up activity detected"
            )
            sign_up_form.add_error("username", "You can not sign up with this name!")
            return JsonResponse({"success": False, "errors": sign_up_form.errors})

        if sign_up_form.is_valid():
            user = sign_up_form.save(commit=False)
            user.email_confirmation_code = uuid.uuid4()

            relative_url = reverse('email-confirmation', args=[user.email_confirmation_code])
            absolute_url = request.build_absolute_uri(relative_url)

            send_email_html.delay(
                "emails/email-confirmation.html",
                {"first_name": user.first_name, "confirmation_url": absolute_url},
                "Online Store - Account confirmation",
                [user.email],
                []
            )

            user.save()

            return JsonResponse({"success": True})
        else:
            return JsonResponse({"success": False, "errors": sign_up_form.errors})
    elif request.method == "GET":
        if request.user and request.user.is_authenticated:
            return redirect("profile")
        sign_up_form = SignupForm()
        return render(request, "pages/auth/signup.html", {"form": sign_up_form})
    else:
        return HttpResponseNotFound()


def sign_in(request):
    if request.method == "POST":
        sign_in_form = SigninForm(request, data=request.POST)

        sign_in_attempts = request.session["sign_in_attempts"] + 1 if "sign_in_attempts" in request.session else 1
        request.session["sign_in_attempts"] = sign_in_attempts

        if sign_in_attempts % settings.SIGNIN_FAILED_ATTEMPTS_COUNT_TRIGGER == 0 and not sign_in_form.is_valid():
            send_email_admins_html.delay(
                "emails/signin-suspicious-activity.html",
                {"username": sign_in_form.data["username"], "ip_address": get_ip_address(request), "datetime": datetime.now()},
                "Suspicious sign in activity detected"
            )

        if sign_in_form.is_valid():
            user = sign_in_form.get_user()
            login(request, user)

            if not user.is_email_confirmed:
                sign_in_form.add_error(None, "You have not confirmed your email! Please check your inbox and confirm your email!")
                return JsonResponse({'success': False, 'errors': sign_in_form.errors})

            if user.is_blocked:
                sign_in_form.add_error(None, "Your account is blocked! Please contact an administrator to review your situation.")
                return JsonResponse({'success': False, 'errors': sign_in_form.errors})

            session_expiry_time = 0 if not sign_in_form.cleaned_data["stay_signed_in"] else 24 * 60 * 60
            request.session.set_expiry(session_expiry_time)

            request.session["sign_in_attempts"] = 0
            return JsonResponse({"success": True})
        else:
            return JsonResponse({"success": False, "errors": sign_in_form.errors})
    elif request.method == "GET":
        if request.user and request.user.is_authenticated:
            return redirect("profile")
        sign_in_form = SigninForm()
        return render(request, "pages/auth/signin.html", {"form": sign_in_form})
    else:
        return HttpResponseNotFound()


def email_confirmation(request, email_confirmation_uuid):
    if request.method == "GET":
        try:
            user = ProfileModel.objects.get(email_confirmation_code=email_confirmation_uuid)
        except (ProfileModel.DoesNotExist, forms.ValidationError):
            logger.debug("Could not find user with specified confirmation code!")
            return redirect("presentation")
        if user.is_email_confirmed == True:
            return redirect("signin")
        else:
            user.is_email_confirmed = True
            user.save()
            return render(request, "pages/auth/email-confirmation.html")
    else:
        return HttpResponseNotFound()


@signin_required
def sign_out(request):
    if request.method == "POST":
        logout(request)
        logger.debug("Logged out user from all sessions!")
        return JsonResponse({"success": True})
    else:
        return HttpResponseNotFound()


@signin_required
def change_password(request):
    if request.method == "POST":
        change_password_form = ChangePasswordForm(user=request.user, data=request.POST)
        if change_password_form.is_valid():
            change_password_form.save()
            update_session_auth_hash(request, request.user)
            logger.debug("Logged out user from all sessions!")
            return JsonResponse({"success": True})
        else:
            return JsonResponse({"success": False, "errors": change_password_form.errors})
    elif request.method == "GET":
        change_password_form = ChangePasswordForm(user=request.user)
        return render(request, "pages/auth/change-password.html", {"form": change_password_form})
    else:
        return HttpResponseNotFound()


@signin_required
def profile(request):
    if request.method == "GET":
        add_data_to_session(request, request.user)
        return render(request, "pages/auth/profile.html")
    else:
        return HttpResponseNotFound()


# Product


def process_product_form(product_form):
    if product_form.is_valid():
        product = product_form.save(commit=False)

        unit = product_form.cleaned_data['unit_string']
        unit = re.sub(r" {2,}", ' ', unit)

        quantity = float(unit.split(' ')[0].strip())
        unit_short_name = unit.split(' ')[1].lower().strip()

        try:
            existing_unit = UnitModel.objects.get(short_name=unit_short_name)
        except UnitModel.DoesNotExist:
            product_form.add_error("unit_string", "Could not find specified unit!")
            return JsonResponse({'success': False, 'errors': product_form.errors})

        product.quantity = quantity
        product.unit = existing_unit

        product.save()
        product_form.save_m2m()

        return JsonResponse({'success': True})
    else:
        return JsonResponse({'success': False, 'errors': product_form.errors})


@signin_required
@permissions_required(["view_productmodel"])
def product_list(request):
    all_products = ProductModel.objects.all().order_by("uuid")
    if request.method == 'POST':
        filter_form = FilterProductsForm(request.POST)
        if filter_form.is_valid():
            try:
                name = filter_form.cleaned_data['name']
                if name:
                    all_products = all_products.filter(name__icontains=name)

                category = filter_form.cleaned_data['category']
                if category:
                    all_products = all_products.filter(
                        categories__in=[category.uuid]).distinct()

                products, pages = get_paginated_objects(request, all_products)
                products = [ProductListDto(product) for product in products]
                return JsonResponse({"success": True, 'products': products, 'pages': pages})
            except ...:
                logger.error("Could not return products list!")
                return JsonResponse({"success": False})
        else:
            return JsonResponse({"success": False, 'errors': filter_form.errors})
    elif request.method == 'GET':
        filter_form = FilterProductsForm()
        return render(request, 'pages/product/product-list.html', {'form': filter_form})
    else:
        return HttpResponseNotFound()


@signin_required
@permissions_required(["add_productmodel"])
def product_add(request):
    if request.method == 'POST':
        add_form = ProductAddEditForm(request.POST)
        return process_product_form(add_form)
    elif request.method == 'GET':
        add_form = ProductAddEditForm()
        return render(request, 'pages/product/product-add.html', {'form': add_form})
    else:
        return HttpResponseNotFound()


@signin_required
@permissions_required(["change_productmodel"])
def product_edit(request, product_uuid):
    if request.method == 'POST':
        existing_product = ProductModel.objects.get(uuid=product_uuid)
        edit_form = ProductAddEditForm(request.POST, instance=existing_product)
        return process_product_form(edit_form)
    elif request.method == 'GET':
        product = ProductModel.objects.get(uuid=product_uuid)
        edit_form = ProductAddEditForm(instance=product, initial={
                                       "unit_string": product.get_unit_display()})
        return render(request, 'pages/product/product-edit.html', {'form': edit_form})
    else:
        return HttpResponseNotFound()


@signin_required
@permissions_required(["delete_productmodel"])
def product_delete(request, product_uuid):
    if request.method == 'DELETE':
        try:
            existing_product = ProductModel.objects.get(uuid=product_uuid)
            existing_product.delete()
            return JsonResponse({'success': True})
        except ...:
            return JsonResponse({'success': False})
    else:
        return HttpResponseNotFound()

# Offer


def offer_list(request):
    all_offers = OfferModel.objects.all().order_by("uuid")

    currency_code = request.GET.get("currency", settings.DEFAULT_CURRENCY_CODE)
    currency = CurrencyModel.objects.get(code=currency_code)

    if request.method == 'POST':
        filter_form = FilterOffersForm(request.POST)
        if filter_form.is_valid():
            try:
                name = filter_form.cleaned_data['name']
                if name:
                    all_offers = all_offers.filter(product__name__icontains=name)

                category = filter_form.cleaned_data['category']
                if category:
                    all_offers = all_offers.filter(
                        product__categories__in=[category.uuid]).distinct()

                offers, pages = get_paginated_objects(request, all_offers)
                offers = [OfferListDto(offer, currency) for offer in offers]
                return JsonResponse({"success": True, 'offers': offers, 'pages': pages})
            except ...:
                logger.critical("Could not return offer list!")
        else:
            return JsonResponse({"success": False, 'errors': filter_form.errors})
    elif request.method == 'GET':
        filter_form = FilterOffersForm()
        return render(request, 'pages/offer/offer-list.html', {'form': filter_form})
    else:
        return HttpResponseNotFound()


def offer_view(request, offer_uuid):
    if request.method == 'GET':
        offer = get_object_or_404(OfferModel, uuid=offer_uuid)

        currency_code = request.GET.get("currency", settings.DEFAULT_CURRENCY_CODE)
        currency = CurrencyModel.objects.get(code=currency_code)
        currency_conversion = CurrencyConversionModel.objects.get(source=offer.currency, destination=currency)

        if request.user.is_authenticated:
            user_offer_views = OfferViewModel.objects.filter(user=request.user).order_by("date_time")
            offer_view = OfferViewModel(user=request.user, offer=offer)
            if user_offer_views.count() >= settings.OFFER_VIEW_USER_HISTORY_SIZE:
                user_offer_views.first().delete()
            offer_view.save()

        return render(request, 'pages/offer/offer-view.html', {'offer': offer, 'currency_conversion': currency_conversion})
    else:
        return HttpResponseNotFound()

# Cart


@signin_required
def cart(request):
    if request.method == 'POST':
        data = json.loads(request.body)

        currency_code = request.GET.get("currency", settings.DEFAULT_CURRENCY_CODE)
        currency = CurrencyModel.objects.get(code=currency_code)

        offers = OfferModel.objects.all().filter(uuid__in=data['offers'])
        return JsonResponse({'offers': [OfferListDto(offer, currency) for offer in offers]})
    elif request.method == 'GET':
        return render(request, 'pages/order/cart.html')
    else:
        return HttpResponseNotFound()

# Order


def generate_invoice_page_information(pdf, page_index, order, total_price):
    title = pdf.beginText(50, 780)
    title.setFont("Helvetica", 22)
    title.textLine("Online store")

    subtitle = pdf.beginText(50, 760)
    subtitle.setFont("Helvetica", 16)
    subtitle.textLine("Invoice")

    price = pdf.beginText(50, 740)
    price.setFont("Helvetica", 12)
    price.textLine(f"Price: {total_price} {order.currency.code}")

    admin_email = pdf.beginText(50, 720)
    admin_email.setFont("Helvetica", 12)
    admin_email.textLine("Administrator email:")
    admin_email.textLine(settings.ADMINS[0][1])

    pdf.drawText(title)
    pdf.drawText(subtitle)
    pdf.drawText(price)
    pdf.drawText(admin_email)

    full_name = pdf.beginText(250, 790)
    full_name.setFont("Helvetica", 12)
    full_name.textLine(f"Full name: {order.user.get_full_name()}")

    email = pdf.beginText(250, 770)
    email.setFont("Helvetica", 12)
    email.textLine(f"Email: {order.user.email}")

    phone_number = pdf.beginText(250, 750)
    phone_number.setFont("Helvetica", 12)
    phone_number.textLine(f"Phone number: {order.user.phone_number}")

    location = pdf.beginText(250, 730)
    location.setFont("Helvetica", 12)
    location.textLine(f"Location: {order.user.country} {order.user.city}")

    address = pdf.beginText(250, 710)
    address.setFont("Helvetica", 12)
    address.textLine(f"Full address: {order.user.address_line_one} {order.user.address_line_two}")

    pdf.drawText(full_name)
    pdf.drawText(email)
    pdf.drawText(phone_number)
    pdf.drawText(location)
    pdf.drawText(address)

    page_number = pdf.beginText(50, 50)
    page_number.setFont("Helvetica", 12)
    page_number.textLine(f"Page {int(page_index)}")

    pdf.drawText(page_number)


def generate_invoice(path, order):
    offers_per_page = 6

    pdf = canvas.Canvas(path)
    pdf.setFont("Helvetica", 12)

    order_offers = OrderOfferModel.objects.filter(order=order)

    for index, order_offer in enumerate(order_offers):
        offer_box_y = 580 - (index % offers_per_page) * 100
        pdf.rect(50, offer_box_y, 500, 100)

        offer_name = pdf.beginText(70, offer_box_y + 70)
        offer_name.setFont("Helvetica", 16)
        offer_name.textLine(order_offer.offer.product.name)

        offer_description = pdf.beginText(70, offer_box_y + 55)
        offer_description.setFont("Helvetica", 12)
        offer_description.textLine(order_offer.offer.product.description)

        offer_quantity = pdf.beginText(70, offer_box_y + 20)
        offer_quantity.setFont("Helvetica", 12)
        offer_quantity.textLine(f"Quantity: {order_offer.quantity}")

        offer_price_str = f"Price: {order_offer.quantity * order_offer.price} {order.currency.code}"
        offer_price_str_width = int(pdf.stringWidth(offer_price_str, "Helvetica", 12))
        offer_price = pdf.beginText(530 - offer_price_str_width, offer_box_y + 20)
        offer_price.setFont("Helvetica", 12)
        offer_price.textLine(offer_price_str)

        pdf.drawText(offer_name)
        pdf.drawText(offer_description)
        pdf.drawText(offer_quantity)
        pdf.drawText(offer_price)

        if index % offers_per_page == (offers_per_page - 1):
            pdf.showPage()
        if index % offers_per_page == 0:
            generate_invoice_page_information(
                pdf,
                index / offers_per_page + 1,
                order,
                order.total_price
            )

    pdf.save()

    return pdf


@signin_required
def order_add(request):
    if request.method == 'POST':
        data = json.loads(request.body)

        currency_code = data['currency']
        currency = CurrencyModel.objects.get(code=currency_code)

        product_stock = {product.uuid: 0 for product in ProductModel.objects.all()}

        stocks = StockModel.objects.all()
        for stock in stocks:
            product_stock[stock.product.uuid] += int(stock.quantity)

        order = OrderModel(
            user=request.user,
            full_address=request.user.get_full_address(),
            phone_number=request.user.phone_number,
            currency=currency
        )

        total_price = 0
        order_offers = []
        for offer_data in data['offers']:
            offer = get_object_or_404(OfferModel, uuid=offer_data['offerUuid'])
            currency_conversion = CurrencyConversionModel.objects.get(source=offer.currency, destination=currency)
            quantity = int(offer_data['quantity'])
            price = float(offer.get_price_discounted(currency_conversion))

            total_price += float(offer.get_price_discounted(currency_conversion)) * quantity

            order_offer = OrderOfferModel(
                order=order,
                offer=offer,
                quantity=quantity,
                price=price
            )
            order_offers.append(order_offer)

            product_stock[offer.product.uuid] -= quantity
            if product_stock[offer.product.uuid] < 0:
                return JsonResponse({"success": False, "error": "Attempting to purchase more items than are in stock!"})

        order.total_price = total_price
        order.save()

        for order_offer in order_offers:
            order_offer.save()

        timestamp = int(time.time())
        pdf_name = f"invoice-{timestamp}.pdf"
        pdf_relative_path = f"pdf/{pdf_name}"
        pdf_absolute_path = f"{settings.MEDIA_ROOT}/{pdf_relative_path}"

        generate_invoice(pdf_absolute_path, order)
        send_email_html.delay(
            "emails/order-added.html",
            {'first_name': request.user.first_name},
            "Invoice",
            [request.user.email],
            attachments=[pdf_relative_path]
        )

        order.invoice = pdf_relative_path
        order.save()

        return JsonResponse({"success": True})
    else:
        return HttpResponseNotFound()


@signin_required
def order_list(request):
    if request.method == 'GET':
        return render(request, 'pages/order/order-list.html')
    elif request.method == 'POST':
        all_orders = OrderModel.objects.all().filter(user=request.user)

        orders, pages = get_paginated_objects(request, all_orders)
        orders = [OrderListDto(order) for order in orders]
        return JsonResponse({"success": True, 'orders': orders, 'pages': pages})
    else:
        return HttpResponseNotFound()

# Promotions


def process_promotion_form(promotion_form):
    if promotion_form.is_valid():
        promotion = promotion_form.save(commit=False)

        discount = promotion_form.cleaned_data['discount_percentage'] / 100
        promotion.discount = discount

        promotion.save()

        calculate_discounts.delay()

        if promotion.get_active():
            offers = OfferModel.objects.all().filter(product__categories__in=[promotion.category])
            offer_uuids = [offer.uuid for offer in offers]
            offer_views = OfferViewModel.objects.all().filter(offer__in=offer_uuids)
            offer_views_users = offer_views.values('user', 'offer').order_by().annotate(view_count=Count('offer'))

            user_uuids = set()
            for offer_views_user in offer_views_users:
                if offer_views_user.get("view_count") >= settings.OFFER_VIEW_PROMOTION_MINIMUM_INTEREST:
                    user_uuids.add(offer_views_user.get("user"))

            if len(user_uuids) > 0:
                users = ProfileModel.objects.all().filter(uuid__in=list(user_uuids))

                promotion_email_path = "emails/category-default.html"
                custom_promotion_email_path = f"emails/category-{snake_case(promotion.category.name)}"
                try:
                    get_template(custom_promotion_email_path)
                    promotion_email_path = custom_promotion_email_path
                except TemplateDoesNotExist as exception:
                    send_email_admins_html.delay(
                        "emails/promotion-template-does-not-exist.html",
                        {"category_name": promotion.category.name, "email_template": custom_promotion_email_path, "full_error": str(exception)},
                        "Promotion email template does not exist"
                    )

                send_promotion_emails_html.delay(
                    promotion_email_path,
                    users,
                    promotion,
                    promotion_form.cleaned_data["subject"]
                )
                logger.info(f"Sent promotion emails for {promotion.name}")
            else:
                logger.warning("No users to send promotion to!")
        return JsonResponse({'success': True})
    else:
        return JsonResponse({'success': False, 'errors': promotion_form.errors})


@signin_required
@permissions_required(["view_promotionmodel"])
def promotion_list(request):
    all_promotions = PromotionModel.objects.all().order_by("uuid")
    if request.method == 'POST':
        filter_form = FilterPromotionsForm(request.POST)
        if filter_form.is_valid():
            try:
                name = filter_form.cleaned_data['name']
                if name:
                    all_promotions = all_promotions.filter(name__icontains=name)

                category = filter_form.cleaned_data['category']
                if category:
                    all_promotions = all_promotions.filter(category=category).distinct()

                promotions, pages = get_paginated_objects(request, all_promotions)
                promotions = [PromotionListDto(promotion) for promotion in promotions]
                return JsonResponse({"success": True, 'promotions': promotions, 'pages': pages})
            except ...:
                logger.error("Could not return promotions list!")
                return JsonResponse({"success": False})
        else:
            return JsonResponse({"success": False, 'errors': filter_form.errors})
    elif request.method == 'GET':
        filter_form = FilterPromotionsForm()
        return render(request, 'pages/promotion/promotion-list.html', {'form': filter_form})
    else:
        return HttpResponseNotFound()


@signin_required
@permissions_required(["add_promotionmodel"])
def promotion_add(request):
    if request.method == 'POST':
        add_form = PromotionAddEditForm(request.POST)
        return process_promotion_form(add_form)
    elif request.method == 'GET':
        add_form = PromotionAddEditForm()
        return render(request, 'pages/promotion/promotion-add.html', {'form': add_form})
    else:
        return HttpResponseNotFound()


@signin_required
@permissions_required(["change_promotionmodel"])
def promotion_edit(request, promotion_uuid):
    if request.method == 'POST':
        existing_promotion = PromotionModel.objects.get(uuid=promotion_uuid)
        edit_form = PromotionAddEditForm(request.POST, instance=existing_promotion)
        return process_promotion_form(edit_form)
    elif request.method == 'GET':
        promotion = PromotionModel.objects.get(uuid=promotion_uuid)
        edit_form = PromotionAddEditForm(instance=promotion, initial={"discount_percentage": promotion.discount * 100})
        return render(request, 'pages/promotion/promotion-edit.html', {'form': edit_form})
    else:
        return HttpResponseNotFound()


@signin_required
@permissions_required(["delete_promotionmodel"])
def promotion_delete(request, promotion_uuid):
    if request.method == 'DELETE':
        try:
            existing_promotion = PromotionModel.objects.get(uuid=promotion_uuid)
            existing_promotion.delete()
            calculate_discounts.delay()
            return JsonResponse({'success': True})
        except ...:
            return JsonResponse({'success': False})
    else:
        return HttpResponseNotFound()

# Stock


def stock_list_offers(request):
    if request.method == "GET":
        product_stock = {product.uuid.__str__(): 0 for product in ProductModel.objects.all()}
        stocks = StockModel.objects.all()
        for stock in stocks:
            product_stock[stock.product.uuid.__str__()] += int(stock.quantity)
        offer_product = {offer.uuid.__str__(): offer.product.uuid.__str__() for offer in OfferModel.objects.all()}
        return JsonResponse({"product_stock": product_stock, "offer_product": offer_product})
    else:
        return HttpResponseNotFound()


# Currency

def currency_list(request):
    if request.method == "GET":
        currencies = CurrencyModel.objects.all()
        currencies_list = [CurrencyListDto(currency) for currency in currencies]
        return JsonResponse({"currencies": currencies_list})
    else:
        return HttpResponseNotFound()
