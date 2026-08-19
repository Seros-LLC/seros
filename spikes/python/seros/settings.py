"""Django settings for the Seros Option-A spike. Deliberately small."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "spike-only-not-a-real-secret")
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "django_tasks",
    "django_tasks_db",
    "slice",
]

MIDDLEWARE = [
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
]

ROOT_URLCONF = "seros.urls"
WSGI_APPLICATION = "seros.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "slice" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": ["django.template.context_processors.request"]},
    }
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.environ.get("SEROS_DB", str(BASE_DIR / "spike.sqlite3")),
        "OPTIONS": {"init_command": "PRAGMA foreign_keys=ON;"},
    }
}

# A real queue: rows in the DB, drained by a separate `manage.py db_worker` process.
TASKS = {
    "default": {
        "BACKEND": "django_tasks_db.backend.DatabaseBackend",
        "QUEUES": ["detect", "write", "maintenance"],
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
STATIC_URL = "static/"
USE_TZ = True
TIME_ZONE = "UTC"

# --- spike knobs -----------------------------------------------------------
SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET", "spike-signing-secret")
SLACK_MAX_SKEW_SECONDS = 60 * 5
# Which provider implementation the workers use. Default is the offline fake.
MODEL_PROVIDER = os.environ.get("SEROS_MODEL_PROVIDER", "slice.providers.fake.FakeProvider")
# tier -> concrete model id, per ADR 0004 rule 2 (config, not code)
MODEL_TIERS = {
    "cheap": {"model_id": "fake-cheap-1", "price_per_1k_in": 0.0, "price_per_1k_out": 0.0},
    "standard": {"model_id": "fake-standard-1", "price_per_1k_in": 0.0, "price_per_1k_out": 0.0},
}
WORKSPACE_ACTION_BUDGET = int(os.environ.get("SEROS_ACTION_BUDGET", "10000"))

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "operator": {
            "()": "slice.logging_ext.RedactingFormatter",
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
        }
    },
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "operator"}},
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {"slice": {"handlers": ["console"], "level": "INFO", "propagate": False}},
}
