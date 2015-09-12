from django.contrib import admin
from knox import models

@admin.register(models.AuthToken)
class AuthTokenAdmin(admin.ModelAdmin):
    list_display = ('key', 'user', 'created',)
    fields = ('user',)
