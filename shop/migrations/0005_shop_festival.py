# Generated by Django 2.1.7 on 2019-07-25 15:38

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('festival', '0001_initial'),
        ('shop', '0004_order_total_amount'),
    ]

    operations = [
        migrations.AddField(
            model_name='shop',
            name='festival',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='festival.Festival'),
        ),
    ]
