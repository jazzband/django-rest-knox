from django
from django.db import migrations
from knox import crypto
from knox.settings import CONSTANTS


def convert_tokens(apps, schema_editor):
    try:
        Token = apps.get_model("authtoken", "token")
    except LookupError:
        Token = False
        
    if Token:
        AuthToken = apps.get_model("knox", "authtoken")
        db_alias = schema_editor.connection.alias

        for token in Token.objects.using(db_alias).all():
            digest = crypto.hash_token(token.key)
            # bypass custom manager
            AuthToken.objects.using(db_alias).bulk_create(
                [
                    AuthToken(
                        digest=digest,
                        token_key=token.key[: CONSTANTS.TOKEN_KEY_LENGTH],
                        user_id=token.user_id,
                        expiry=None,  # or whatever logic you want
                    )
                ]
            )
            # bypass auto_now_add restriction
            AuthToken.objects.using(db_alias).filter(digest=digest).update(
                created=token.created
            )

        Token.objects.using(db_alias).all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("knox", "0009_extend_authtoken_field"),
    ]

    operations = [migrations.RunPython(convert_tokens)]