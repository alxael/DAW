# Generated by Django 5.1.2 on 2024-12-29 09:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('client', '0002_profilemodel_is_following_newsletter'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderoffermodel',
            name='discount',
            field=models.DecimalField(decimal_places=3, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name='orderoffermodel',
            name='price',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
            preserve_default=False,
        ),
    ]