# Generated by Django 4.2.4 on 2023-08-07 03:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0007_remove_useraccount_image_remove_useraccount_name_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='parent',
            name='school',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='api.school'),
        ),
    ]