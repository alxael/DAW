import re
import uuid
import logging
from datetime import datetime
from django import forms
from django.conf import settings
from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseNotFound
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage, EmailMultiAlternatives, get_connection, mail_admins
from django.core.paginator import Paginator, EmptyPage
from django.core.exceptions import PermissionDenied
from django.template.loader import render_to_string, get_template, TemplateDoesNotExist
from django.db.models import Count
from ipware import get_client_ip
from .models import ProductModel, UnitModel, ProfileModel, OfferModel, OfferViewModel, PromotionModel
from .forms import FilterProductsForm, ProductAddEditForm, FilterOffersForm, FilterPromotionsForm, PromotionAddEditForm, ContactForm, SigninForm, SignupForm, ChangePasswordForm
from .dto import ProductListDto, OfferListDto, PromotionListDto

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


def mail_admins_html(template_path, template_data, subject):
    content = render_to_string(template_path, template_data)
    mail_admins(subject=subject, message=content, html_message=content, fail_silently=False)
    logger.info(f"Mailed admins! Subject: {subject}")


def check_user(request, signed_in, is_staff, is_superuser):
    username = None if not request.user else request.user.username
    template_path = "pages/responses/403.html"
    if signed_in and not request.user and not request.user.is_authenticated:
        return HttpResponseForbidden(
            render(
                request,
                template_path,
                {
                    "username": username,
                    "custom_message": "You do not have access to this resource."
                }
            ))
    if is_staff and not request.user.is_staff and not request.user.is_superuser:
        return HttpResponseForbidden(
            render(
                request,
                template_path,
                {
                    "username": username,
                    "title": "Access forbidden",
                    "custom_message": "You do not have access to this resource."
                }
            ))
    if is_superuser and not request.user.is_superuser:
        return HttpResponseForbidden(
            render(
                request,
                template_path,
                {
                    "username": username,
                    "title": "Access forbidden"
                }
            ))
    return True


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
            mail_admins_html(
                "emails/signup-forbidden-username.html",
                {"username": sign_up_form.data["username"], "ip_address": get_ip_address(request), "datetime": datetime.now()},
                "Suspicious sign up activity detected"
            )

        if sign_up_form.is_valid():
            user = sign_up_form.save(commit=False)
            user.email_confirmation_code = uuid.uuid4()

            relative_url = reverse('email-confirmation', args=[user.email_confirmation_code])
            absolute_url = request.build_absolute_uri(relative_url)

            content_data = {"first_name": user.first_name, "confirmation_url": absolute_url}
            content = render_to_string("emails/email-confirmation.html", content_data)
            confirmation_email = EmailMessage(
                subject="Online Store - Account confirmation",
                body=content,
                to=[user.email]
            )
            confirmation_email.content_subtype = "html"
            confirmation_email.send(fail_silently=False)

            user.save()
            add_data_to_session(request, user)

            return JsonResponse({"success": True})
        else:
            return JsonResponse({"success": False, "errors": sign_up_form.errors})
    elif request.method == "GET":
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
            mail_admins_html(
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

            session_expiry_time = 0 if not sign_in_form.cleaned_data["stay_signed_in"] else 24 * 60 * 60
            request.session.set_expiry(session_expiry_time)

            add_data_to_session(request, user)

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


@login_required
def sign_out(request):
    if request.method == "POST":
        logout(request)
        logger.debug("Logged out user from all sessions!")
        return JsonResponse({"success": True})
    else:
        return HttpResponseNotFound()


@login_required
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


@login_required
def profile(request):
    return render(request, "pages/auth/profile.html")

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


def product_list(request):
    check = check_user(request, signed_in=True, is_staff=True, is_superuser=True)
    if check != True:
        return check

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


def product_add(request):
    check = check_user(request, signed_in=True, is_staff=True, is_superuser=True)
    if check != True:
        return check

    if request.method == 'POST':
        add_form = ProductAddEditForm(request.POST)
        return process_product_form(add_form)
    elif request.method == 'GET':
        add_form = ProductAddEditForm()
        return render(request, 'pages/product/product-add.html', {'form': add_form})
    else:
        return HttpResponseNotFound()


def product_edit(request, product_uuid):
    check = check_user(request, signed_in=True, is_staff=True, is_superuser=True)
    if not check:
        return check

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


def product_delete(request, product_uuid):
    check = check_user(request, signed_in=True, is_staff=True, is_superuser=True)
    if check != True:
        return check

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
                offers = [OfferListDto(offer) for offer in offers]
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
        if request.user.is_authenticated:
            user_offer_views = OfferViewModel.objects.filter(user=request.user).order_by("date_time")
            offer_view = OfferViewModel(user=request.user, offer=offer)
            if user_offer_views.count() >= settings.OFFER_VIEW_USER_HISTORY_SIZE:
                user_offer_views.first().delete()
            offer_view.save()
        return render(request, 'pages/offer/offer-view.html', {'offer': offer})
    else:
        return HttpResponseNotFound()

# Promotions


def process_promotion_form(promotion_form):
    if promotion_form.is_valid():
        promotion = promotion_form.save(commit=False)

        discount = promotion_form.cleaned_data['discount_percentage'] / 100
        promotion.discount = discount

        promotion.save()

        if promotion.get_active():
            offers = OfferModel.objects.all().filter(product__categories__in=[promotion.category])
            offer_uuids = [offer.uuid for offer in offers]
            offer_views = OfferViewModel.objects.all().filter(offer__in=offer_uuids)
            offer_views_users = offer_views.values('user', 'offer').order_by().annotate(view_count=Count('offer'))

            user_uuids = set()
            for offer_views_user in offer_views_users:
                if offer_views_user.get("view_count") >= settings.OFFER_VIEW_PROMOTION_MINIMUM_INTEREST:
                    user_uuids.add(offer_views_user.get("user"))

            for offer in offers:
                offer.discount = max(offer.discount, promotion.discount)
                offer.save()

            users = ProfileModel.objects.all().filter(uuid__in=list(user_uuids))

            promotion_email_path = "emails/category-default.html"
            custom_promotion_email_path = f"emails/category-{snake_case(promotion.category.name)}"
            try:
                get_template(custom_promotion_email_path)
                promotion_email_path = custom_promotion_email_path
            except TemplateDoesNotExist as exception:
                mail_admins_html(
                    "emails/promotion-template-does-not-exist.html",
                    {"category_name": promotion.category.name, "email_template": custom_promotion_email_path, "full_error": str(exception)},
                    "Promotion email template does not exist"
                )

            promotion_emails = []
            for user in users:
                content_data = {"category_name": promotion.category.name, "expiration_date": promotion.end_date, "discount": promotion.discount * 100, "first_name": user.first_name}
                content = render_to_string(promotion_email_path, content_data)
                promotion_email = EmailMultiAlternatives(
                    subject=promotion_form.cleaned_data["subject"],
                    body=content,
                    to=[user.email]
                )
                promotion_email.content_subtype = "html"
                promotion_emails.append(promotion_email)

            connection = get_connection()
            connection.open()
            connection.send_messages(promotion_emails)
            connection.close()

            logger.info(f"Sent promotion emails for {promotion.name}")

        return JsonResponse({'success': True})
    else:
        return JsonResponse({'success': False, 'errors': promotion_form.errors})


def promotion_list(request):
    check = check_user(request, signed_in=True, is_staff=True, is_superuser=True)
    if check != True:
        return check

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


def promotion_add(request):
    check = check_user(request, signed_in=True, is_staff=True, is_superuser=True)
    if check != True:
        return check

    if request.method == 'POST':
        add_form = PromotionAddEditForm(request.POST)
        return process_promotion_form(add_form)
    elif request.method == 'GET':
        add_form = PromotionAddEditForm()
        return render(request, 'pages/promotion/promotion-add.html', {'form': add_form})
    else:
        return HttpResponseNotFound()


def promotion_delete(request, promotion_uuid):
    check = check_user(request, signed_in=True, is_staff=True, is_superuser=True)
    if check != True:
        return check

    if request.method == 'DELETE':
        try:
            existing_promotion = PromotionModel.objects.get(uuid=promotion_uuid)
            existing_promotion.delete()
            # offer discounts should be updated as well
            return JsonResponse({'success': True})
        except ...:
            return JsonResponse({'success': False})
    else:
        return HttpResponseNotFound()
