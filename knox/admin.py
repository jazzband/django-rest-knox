from django.contrib import admin
from knox import models

@admin.register(models.EmailConfirmation)
class EmailConfirmationAdmin(admin.ModelAdmin):
    list_display = ('account', 'verified',)

@admin.register(models.AuthToken)
class EmailConfirmationAdmin(admin.ModelAdmin):
    list_display = ('key', 'user',)
