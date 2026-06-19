import logging
from django.db import close_old_connections


class DBLogHandler(logging.Handler):
    """Handler que grava registros de log na tabela LogEvento do banco."""

    def __init__(self, origem=None):
        super().__init__()
        self.origem = origem

    def emit(self, record):
        close_old_connections()
        try:
            from .models import LogEvento
            LogEvento.objects.create(
                nivel=record.levelname,
                origem=self.origem or record.name,
                mensagem=self.format(record),
            )
        except Exception:
            # Nunca deixar o handler de log interromper a execução do script
            pass
