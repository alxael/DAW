# Generated by Django 5.1.2 on 2024-11-07 12:55

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('client', '0004_alter_categorymodel_parentuuid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='categorymodel',
            name='parentUuid',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='client.categorymodel'),
        ),
    ]
