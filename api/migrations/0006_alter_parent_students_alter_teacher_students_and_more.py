# Generated by Django 4.2.4 on 2023-08-06 13:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0005_alter_school_email_2'),
    ]

    operations = [
        migrations.AlterField(
            model_name='parent',
            name='students',
            field=models.ManyToManyField(blank=True, to='api.student'),
        ),
        migrations.AlterField(
            model_name='teacher',
            name='students',
            field=models.ManyToManyField(blank=True, to='api.student'),
        ),
        migrations.AlterField(
            model_name='teacher',
            name='subject',
            field=models.JSONField(null=True),
        ),
    ]
