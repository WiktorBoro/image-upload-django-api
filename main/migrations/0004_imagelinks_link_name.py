# Generated by Django 4.0.6 on 2022-07-11 15:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0003_rename_image_images_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='imagelinks',
            name='link_name',
            field=models.CharField(default=1, max_length=100),
            preserve_default=False,
        ),
    ]
