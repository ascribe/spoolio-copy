from django.apps import AppConfig


class AclAppConfig(AppConfig):
    name = 'acl'
    verbose_name = 'Access Control List for pieces and editions'

    def ready(self):
        # If you re using the receiver() decorator, simply import the signals submodule inside ready().
        # https://docs.djangoproject.com/en/1.8/topics/signals/#connecting-receiver-functions

        from acl import signals