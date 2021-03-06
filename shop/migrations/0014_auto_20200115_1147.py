# Generated by Django 2.1.7 on 2020-01-15 11:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0017_payout_status'),
        ('shop', '0013_order_tx'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='shop',
            name='pub_key',
        ),
        migrations.AddField(
            model_name='shop',
            name='wallet',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='shops', to='users.Wallet'),
        ),
    ]
