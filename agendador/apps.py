import os
from django.apps import AppConfig


class AgendadorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'agendador'
    verbose_name = 'Agendador'

    def ready(self):
        # No autoreloader do runserver, só inicia no processo filho (RUN_MAIN=true).
        # Em produção (gunicorn/uwsgi) RUN_MAIN não é definido, então inicia normalmente.
        run_main = os.environ.get('RUN_MAIN')
        if run_main == 'true' or run_main is None:
            from .scheduler import start_scheduler
            try:
                start_scheduler()
            except Exception:
                pass
