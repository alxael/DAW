# Generated by Django 5.1.2 on 2025-01-02 15:00

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('client', '0018_remove_ordermodel_offers'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='orderoffermodel',
            name='currency',
        ),
        migrations.AddField(
            model_name='ordermodel',
            name='currency',
            field=models.ForeignKey(default='8a4955ed-1e8c-46bc-88d1-558f219bec83', on_delete=django.db.models.deletion.PROTECT, to='client.currencymodel'),
            preserve_default=False,
        ),
    ]
