# Generated by Django 4.2.5 on 2023-09-17 12:43

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='recipe',
            options={},
        ),
        migrations.AlterField(
            model_name='recipe',
            name='cooking_time',
            field=models.PositiveSmallIntegerField(default=1, validators=[django.core.validators.MinValueValidator(1, 'Минимум одна минута')], verbose_name='Время готовки'),
        ),
        migrations.AlterField(
            model_name='recipe',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AddConstraint(
            model_name='recipe',
            constraint=models.UniqueConstraint(fields=('author', 'name'), name='unique_author_name'),
        ),
    ]
