# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2018-02-16 22:01
from __future__ import unicode_literals

from django.db import migrations, models
import django_prices.models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0035_order_tax_rate'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='max_delivery_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='min_delivery_date',
            field=models.DateField(blank=True, null=True),
        )
    ]