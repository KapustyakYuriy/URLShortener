import sys
import threading
from django.apps import AppConfig

class AnalyticsConfig(AppConfig):
    name = "apps.analytics"

    def ready(self):
        if "runserver" not in sys.argv and "gunicorn" not in sys.argv[0]:
            return
        from apps.analytics.subscriber import run_subscriber
        thread = threading.Thread(target=run_subscriber, daemon=True)
        thread.start()