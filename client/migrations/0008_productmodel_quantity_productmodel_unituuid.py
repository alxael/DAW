# Generated by Django 5.1.2 on 2024-11-07 13:35

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('client', '0007_alter_offermodel_expirationdate_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='productmodel',
            name='quantity',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='productmodel',
            name='unitUuid',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='client.unitmodel'),
        ),
    ]
