# from django.db.models.fields import return_None
# from knox.models import get_token_model,get_refresh_token_model,get_refresh_family_model
#
#
# def delete_family(auth_object):
#     token_model = get_token_model()
#     refresh_token_model = get_refresh_token_model()
#     refresh_family_model = get_refresh_family_model()
#
#     # print(token._meta.model_name)
#     parent = None
#
#     if isinstance(auth_object, token_model):
#         parent = refresh_family_model.objects.filter(token=auth_object.token_key).first()
#     
#     elif isinstance(auth_object, refresh_token_model):
#         parent = refresh_family_model.objects.filter(refresh_token=auth_object.token_key).first()
#     
#     elif auth_object._meta.model_name == refresh_family_model._meta.model_name:
#         parent = auth_object.parent
#     
#     if parent:
#         refresh_family_model.objects.filter(parent=parent.parent).delete()    # token_model,refresh_token_model,refresh_family_model]:
#         # if token._meta.model_name == i._meta.model_name:
#
#
#
