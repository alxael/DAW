# Generated by Django 4.2.16 on 2024-12-14 16:43

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('client', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='offermodel',
            name='expiration_date',
        ),
        migrations.CreateModel(
            name='OfferViewModel',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('offer', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='client.offermodel')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]