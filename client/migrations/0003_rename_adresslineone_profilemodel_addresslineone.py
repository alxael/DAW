# Generated by Django 4.2.16 on 2024-12-04 10:30

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('client', '0002_alter_profilemodel_addresslinetwo_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='profilemodel',
            old_name='adressLineOne',
            new_name='addressLineOne',
        ),
    ]
