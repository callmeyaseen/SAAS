from django.apps import AppConfig


class SecurityConfig(AppConfig):
    name = 'security'

class AccountsConfig(AppConfig):
    name = 'accounts'

    def ready(self):
        import accounts.signals