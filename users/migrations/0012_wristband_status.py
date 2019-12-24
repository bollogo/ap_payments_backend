# Generated by Django 2.1.7 on 2019-10-22 10:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0011_wristband'),
    ]

    operations = [
        migrations.AddField(
            model_name='wristband',
            name='status',
            field=models.CharField(blank=True, choices=[('ACTIVE', 'ACTIVE'), ('DISABLED', 'DISABLED')], max_length=255, null=True),
        ),
    ]
