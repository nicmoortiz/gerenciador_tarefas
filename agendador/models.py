from django.db import models


class TarefaAgendada(models.Model):
    TIPO_CHOICES = [
        ('diario',     'Diário'),
        ('dias_uteis', 'Dias Úteis'),
        ('uma_vez',    'Uma Vez'),
        ('semanal',    'Semanal'),
        ('mensal',     'Mensal'),
        ('intervalo',  'Por Intervalo'),
    ]

    MODULO_CHOICES = [
        ('',               '— Selecione —'),
        ('ambulatorial',   'Ambulatorial'),
        ('urgencia',       'Urgência'),
        ('leitos_aih',     'Leitos AIH'),
        ('leitos',         'Leitos'),
        ('pre_hospitalar', 'Pré-Hospitalar'),
        ('indicadores',    'Indicadores'),
    ]

    nome = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    modulo = models.CharField(max_length=20, choices=MODULO_CHOICES, blank=True)
    caminho_script = models.CharField(max_length=500)
    argumentos = models.CharField(max_length=500, blank=True)

    # Tipo de agendamento
    tipo_agendamento = models.CharField(max_length=20, choices=TIPO_CHOICES, default='diario')

    # Campos compartilhados
    horario = models.TimeField(null=True, blank=True)
    data_inicio = models.DateField(null=True, blank=True)

    # A cada X min
    intervalo_minutos = models.PositiveIntegerField(null=True, blank=True)

    # Semanal
    dias_semana = models.CharField(max_length=30, blank=True, default='')   # 'mon,wed,fri'
    repetir_semanas = models.PositiveIntegerField(default=1)

    # Mensal
    dias_mes = models.CharField(max_length=100, blank=True, default='')     # '1,15'
    meses_execucao = models.CharField(max_length=50, blank=True, default='*')  # '1,6,12' ou '*'

    assunto = models.CharField(max_length=200, blank=True)
    observacoes = models.TextField(blank=True)

    ativa = models.BooleanField(default=True)
    criada_em = models.DateTimeField(auto_now_add=True)
    atualizada_em = models.DateTimeField(auto_now=True)
    ultima_execucao = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-criada_em']
        verbose_name = 'Tarefa Agendada'
        verbose_name_plural = 'Tarefas Agendadas'

    def __str__(self):
        return self.nome

    def descricao_agendamento(self):
        h = self.horario.strftime('%H:%M') if self.horario else '—'
        tipo = self.tipo_agendamento

        if tipo == 'diario':
            return f'Diário às {h}'
        if tipo == 'dias_uteis':
            return f'Dias úteis às {h}'
        if tipo == 'uma_vez':
            d = self.data_inicio.strftime('%d/%m/%Y') if self.data_inicio else '—'
            return f'Uma vez em {d} às {h}'
        if tipo == 'semanal':
            dias = self.dias_semana or '—'
            rep = f' (a cada {self.repetir_semanas} sem.)' if self.repetir_semanas > 1 else ''
            return f'Semanal às {h} — {dias}{rep}'
        if tipo == 'mensal':
            dias = self.dias_mes or '—'
            meses = self.meses_execucao if self.meses_execucao != '*' else 'todo mês'
            return f'Mensal às {h} — dias {dias} ({meses})'
        if tipo == 'intervalo':
            m = self.intervalo_minutos or 0
            if m and m % 60 == 0:
                return f'A cada {m // 60} hora{"s" if m // 60 != 1 else ""}'
            return f'A cada {m} minuto{"s" if m != 1 else ""}'
        return '—'

    def get_trigger(self):
        """Retorna (tipo_trigger, kwargs) para o APScheduler."""
        from datetime import datetime, time as dtime
        import pytz

        tz = pytz.timezone('America/Sao_Paulo')
        horario = self.horario or dtime(8, 0)

        start_dt = None
        if self.data_inicio:
            start_dt = tz.localize(datetime.combine(self.data_inicio, horario))

        if self.tipo_agendamento == 'diario':
            return 'cron', dict(hour=horario.hour, minute=horario.minute, start_date=start_dt)

        if self.tipo_agendamento == 'dias_uteis':
            return 'cron', dict(
                hour=horario.hour, minute=horario.minute,
                day_of_week='mon-fri', start_date=start_dt,
            )

        if self.tipo_agendamento == 'uma_vez':
            run_dt = start_dt or tz.localize(datetime.combine(
                self.data_inicio or datetime.today().date(), horario
            ))
            return 'date', dict(run_date=run_dt)

        if self.tipo_agendamento == 'semanal':
            week = f'*/{self.repetir_semanas}' if self.repetir_semanas > 1 else '*'
            return 'cron', dict(
                hour=horario.hour, minute=horario.minute,
                day_of_week=self.dias_semana or 'mon',
                week=week, start_date=start_dt,
            )

        if self.tipo_agendamento == 'mensal':
            return 'cron', dict(
                hour=horario.hour, minute=horario.minute,
                day=self.dias_mes or '1',
                month=self.meses_execucao or '*',
                start_date=start_dt,
            )

        if self.tipo_agendamento == 'intervalo':
            return 'interval', dict(
                minutes=self.intervalo_minutos or 30,
                start_date=start_dt,
            )

        return 'cron', dict(hour=8, minute=0)


class HistoricoExecucao(models.Model):
    STATUS_CHOICES = [
        ('rodando', 'Rodando'),
        ('sucesso', 'Sucesso'),
        ('erro',    'Erro'),
    ]

    tarefa = models.ForeignKey(
        TarefaAgendada, on_delete=models.CASCADE, related_name='historico'
    )
    iniciada_em = models.DateTimeField()
    finalizada_em = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='rodando')
    saida = models.TextField(blank=True)
    erro = models.TextField(blank=True)
    codigo_retorno = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ['-iniciada_em']
        verbose_name = 'Histórico de Execução'
        verbose_name_plural = 'Históricos de Execução'

    def duracao(self):
        if self.finalizada_em and self.iniciada_em:
            total = int((self.finalizada_em - self.iniciada_em).total_seconds())
            if total < 60:
                return f'{total}s'
            return f'{total // 60}m {total % 60}s'
        return None


class Configuracao(models.Model):
    chave = models.CharField(max_length=100, unique=True)
    valor = models.TextField()
    descricao = models.CharField(max_length=300, blank=True)
    atualizada_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['chave']
        verbose_name = 'Configuração'
        verbose_name_plural = 'Configurações'

    def __str__(self):
        return self.chave

    @classmethod
    def get(cls, chave, padrao=None):
        try:
            return cls.objects.get(chave=chave).valor
        except cls.DoesNotExist:
            return padrao


class LogEvento(models.Model):
    NIVEL_CHOICES = [
        ('DEBUG',    'DEBUG'),
        ('INFO',     'INFO'),
        ('WARNING',  'WARNING'),
        ('ERROR',    'ERROR'),
        ('CRITICAL', 'CRITICAL'),
    ]

    nivel = models.CharField(max_length=10, choices=NIVEL_CHOICES, default='INFO')
    origem = models.CharField(max_length=200)
    mensagem = models.TextField()
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'Log de Evento'
        verbose_name_plural = 'Logs de Eventos'

    def __str__(self):
        return f'[{self.nivel}] {self.origem}'
