# Generated by Django 5.1.2 on 2024-11-07 13:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('client', '0008_productmodel_quantity_productmodel_unituuid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='offermodel',
            name='expirationDate',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='stockmodel',
            name='expirationDate',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]