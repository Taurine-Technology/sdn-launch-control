from django.apps import AppConfig
from .batcher import start_default_batchers_if_enabled
from .gauges import start_gauges_if_enabled
import os
import logging


class ObservabilityConfig(AppConfig):
    name = "observability"
    verbose_name = "Observability"

    def ready(self):
        logger = logging.getLogger(__name__)
        try:
            # Register celery signals by importing the module
            obs_enabled = os.environ.get("OBS_ENABLE", "true").lower() == "true"
            logger.info("ObservabilityConfig.ready called; OBS_ENABLE=%s", obs_enabled)
            if obs_enabled:
                from . import celery_signals  # noqa: F401
                from .channels_hooks import start_channels_flusher_if_enabled
                from .profiler import start_profiler_if_enabled
            start_default_batchers_if_enabled()
            start_gauges_if_enabled()
            if obs_enabled:
                start_channels_flusher_if_enabled()
                start_profiler_if_enabled()
            logger.info("Observability utilities initialized (batchers, gauges, optional hooks)")
        except Exception:
            # Never fail app startup due to observability utilities
            logger.warning("Observability initialization failed (non-fatal)", exc_info=True)


