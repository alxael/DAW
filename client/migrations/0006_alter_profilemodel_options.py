# Generated by Django 5.1.2 on 2024-12-30 10:13

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('client', '0005_profilemodel_is_blocked'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='profilemodel',
            options={'permissions': [('manager', "User can change any user's username, email, first name, last name, block status and email confirmation status.")]},
        ),
    ]