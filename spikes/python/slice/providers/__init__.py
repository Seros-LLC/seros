from django.conf import settings
from django.utils.module_loading import import_string


def get_provider():
    """The one place a concrete provider is chosen. ADR 0004 rule 1."""
    return import_string(settings.MODEL_PROVIDER)()
