# Generated by Django 2.2.16 on 2022-06-09 18:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0007_follow'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='comment',
            options={'ordering': ('-created',)},
        ),
    ]
