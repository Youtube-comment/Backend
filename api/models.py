from django.db import models

class User(models.Model):
    name = models.CharField(max_length=100)
    mail = models.CharField(max_length=100)
    g_id = models.CharField(max_length=100)
    access_token = models.CharField(max_length=100)