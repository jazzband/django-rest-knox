from django.contrib import admin
from knox.models import EmailConfirmation

@admin.register(EmailConfirmation)
class EmailConfirmationAdmin(admin.ModelAdmin):
    list_display = ('account', 'verified',)
