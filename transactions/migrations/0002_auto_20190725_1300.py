# Generated by Django 2.1.7 on 2019-07-25 13:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='invoice',
            options={'ordering': ['-date_created']},
        ),
        migrations.AlterModelOptions(
            name='transaction',
            options={'ordering': ['-date_broadcast']},
        ),
    ]
