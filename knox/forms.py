from django.contrib.auth import forms as auth_forms

from . import models


class PasswordChangeForm(auth_forms.PasswordChangeForm):
    """
    Also re-encrypt all a user's encrypted tokens on password change.
    """

    def save(self, *args, **kwargs):
        """
        Delegate to the base class and then re-encrypt all tokens.
        """
        result = super(PasswordChangeForm, self).save(*args, **kwargs)
        models.AuthToken.objects.change_passwords(
            self.user,
            self.cleaned_data["old_password"],
            self.cleaned_data["new_password1"])
        return result


class SetPasswordForm(auth_forms.SetPasswordForm):
    """
    Also delete all a user's encrypted tokens on password reset.
    """

    def save(self, *args, **kwargs):
        """
        Delegate to the base class and then delete all tokens.
        """
        result = super(SetPasswordForm, self).save(*args, **kwargs)
        models.AuthToken.objects.reset_passwords(self.user)
        return result
