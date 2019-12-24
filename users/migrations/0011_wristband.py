# Generated by Django 2.1.7 on 2019-10-22 09:06

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0010_auto_20190919_1418'),
    ]

    operations = [
        migrations.CreateModel(
            name='Wristband',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('token', models.CharField(max_length=512, unique=True)),
                ('wallet', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='wristbands', to='users.Wallet')),
            ],
        ),
    ]
