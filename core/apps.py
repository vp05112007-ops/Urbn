from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = "core"
    
    def ready(self):
        print("CORE APPCONFIG READY EXECUTING!")
        from . import signals
