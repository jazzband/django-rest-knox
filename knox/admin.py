from django.contrib import admin

from knox import models


@admin.register(models.AuthToken)
class AuthTokenAdmin(admin.ModelAdmin):
    list_display = ('digest', 'user', 'created', 'accessed', 'expiry',)
    fields = ()
    raw_id_fields = ('user',)
