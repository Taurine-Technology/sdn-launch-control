from django.apps import AppConfig
from .batcher import start_default_batchers_if_enabled
from .gauges import start_gauges_if_enabled
import os

class ObservabilityConfig(AppConfig):
    name = "observability"
    verbose_name = "Observability"

    def ready(self):
        try:
            # Register celery signals by importing the module
            if os.environ.get("OBS_ENABLE", "true").lower() == "true":
                from . import celery_signals  # noqa: F401
                from .channels_hooks import start_channels_flusher_if_enabled
                from .profiler import start_profiler_if_enabled
            start_default_batchers_if_enabled()
            start_gauges_if_enabled()
            if os.environ.get("OBS_ENABLE", "true").lower() == "true":
                start_channels_flusher_if_enabled()
                start_profiler_if_enabled()
        except Exception:
            # Never fail app startup due to observability utilities
            pass


