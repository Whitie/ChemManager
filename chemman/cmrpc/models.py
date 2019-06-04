# -*- coding: utf-8 -*-

from django.contrib.auth.models import User
from django.db import models


# Create your models here.

class RpcSession(models.Model):
    user = models.OneToOneField(
        User, related_name='cmrpc_session', on_delete=models.CASCADE
    )
    token = models.CharField(max_length=150)
    saved = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '{} -> {}'.format(self.user, self.token)
