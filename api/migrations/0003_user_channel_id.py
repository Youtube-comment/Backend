# Generated by Django 4.2.1 on 2023-05-14 12:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0002_remove_user_email_remove_user_first_name_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="channel_id",
            field=models.CharField(default=1, max_length=100),
            preserve_default=False,
        ),
    ]
