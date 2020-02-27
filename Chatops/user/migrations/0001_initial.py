# Generated by Django 3.0.2 on 2020-01-27 16:50

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Users',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_id', models.CharField(max_length=250)),
                ('name', models.CharField(max_length=250, null=True)),
                ('email', models.CharField(max_length=250, null=True)),
                ('roles', models.CharField(max_length=250, null=True)),
                ('channel_id', models.CharField(max_length=250, null=True)),
                ('isManager', models.BooleanField(default=False)),
                ('created_date', models.DateTimeField(default=datetime.datetime(2020, 1, 27, 16, 50, 7, 498209))),
            ],
        ),
    ]
