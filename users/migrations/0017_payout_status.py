# Generated by Django 2.1.7 on 2020-01-14 15:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0016_charge_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='payout',
            name='status',
            field=models.CharField(choices=[('pending', 'pending'), ('paid', 'paid'), ('ready', 'ready'), ('success', 'success'), ('error', 'error')], default='pending', max_length=255),
        ),
    ]
