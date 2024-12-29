from __future__ import absolute_import, unicode_literals

import logging
from datetime import timedelta
from celery import shared_task, states
from celery.exceptions import Ignore
from celery.utils.log import get_task_logger
from django.db.models.functions import Now
from django.core.mail import EmailMessage, EmailMultiAlternatives, get_connection, mail_admins
from django.template.loader import render_to_string, get_template, TemplateDoesNotExist
from django_celery_beat.models import PeriodicTask, IntervalSchedule
from .models import ProfileModel, PromotionModel, OfferModel

logger = get_task_logger('django')


@shared_task(bind=True, max_retries=3)
def send_email_html(self, content_path, content_data, subject, to):
    try:
        content = render_to_string(content_path, content_data)
        confirmation_email = EmailMessage(
            subject=subject,
            body=content,
            to=to
        )
        confirmation_email.content_subtype = "html"
        confirmation_email.send(fail_silently=False)
        return True
    except TemplateDoesNotExist:
        error_message = "Could not find template!"
        logger.error(error_message)
        self.update_state(
            state=states.FAILURE,
            meta=error_message
        )
        raise Ignore()


@shared_task(bind=True, max_retries=3)
def send_email_admins_html(self, content_path, content_data, subject):
    try:
        content = render_to_string(content_path, content_data)
        mail_admins(subject=subject, message=content, html_message=content, fail_silently=False)
        logger.info(f"Mailed admins! Subject: {subject}")
        return True
    except TemplateDoesNotExist:
        error_message = "Could not find template!"
        logger.error(error_message)
        self.update_state(
            state=states.FAILURE,
            meta=error_message
        )
        raise Ignore()


@shared_task(bind=True, max_retries=3)
def send_promotion_emails_html(self, content_path, users, promotion, subject):
    promotion_emails = []
    for user in users:
        content_data = {"category_name": promotion.category.name, "expiration_date": promotion.end_date, "discount": promotion.discount * 100, "first_name": user.first_name}
        content = render_to_string(content_path, content_data)
        promotion_email = EmailMultiAlternatives(
            subject=subject,
            body=content,
            to=[user.email]
        )
        promotion_email.content_subtype = "html"
        promotion_emails.append(promotion_email)

    connection = get_connection()
    connection.open()
    connection.send_messages(promotion_emails)
    connection.close()

    return True


@shared_task(bind=True)
def delete_unconfirmed_users(self):
    unconfirmed_users = ProfileModel.objects.all().filter(is_email_confirmed=False, date_joined__lte=Now() - timedelta(hours=24))
    logger.info(f"Deleting {unconfirmed_users.count()} unconfirmed users.")
    unconfirmed_users.delete()


@shared_task(bind=True)
def send_newsletter_emails(self, content_path, subject):
    users = ProfileModel.objects.all().filter(is_following_newsletter=True)

    active_promotions = PromotionModel.objects.all().filter(start_date__lte=Now(), end_date__gte=Now())
    max_discount = int(max([promotion.discount for promotion in active_promotions] + [0])) * 100
    categories = [promotion.category.name for promotion in active_promotions]
    
    if max_discount == 0:
        logger.warning('No active promotions! No newsletter emails will be sent!')
        return

    content_data = {"max_discount": max_discount, "categories": ", ".join(categories)}
    content = render_to_string(content_path, content_data)

    newsletter_emails = []
    for user in users:
        newsletter_email = EmailMultiAlternatives(
            subject=subject,
            body=content,
            to=[user.email]
        )
        newsletter_email.content_subtype = "html"
        newsletter_emails.append(newsletter_email)

    connection = get_connection()
    connection.open()
    connection.send_messages(newsletter_emails)
    connection.close()

@shared_task(bind=True)
def calculate_discounts(self):
    offers = OfferModel.objects.all()
    active_promotions = PromotionModel.objects.all().filter(start_date__lte=Now(), end_date__gte=Now())
    
    for offer in offers:
        discount = 0
        for promotion in active_promotions:
            if promotion.category in offer.product.categories:
                discount = max(discount, promotion.discount)
        offer.discount = discount
        offer.save()
        
@shared_task(bind=True)
def delete_expired_promotions(self):
    expired_promotions = PromotionModel.objects.all().filter(end_date__lt=Now())
    expired_promotions.delete()