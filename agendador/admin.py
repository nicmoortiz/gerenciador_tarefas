from django.contrib import admin
from .models import TarefaAgendada, HistoricoExecucao, Configuracao, LogEvento


@admin.register(TarefaAgendada)
class TarefaAgendadaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'descricao_agendamento', 'ativa', 'ultima_execucao', 'criada_em']
    list_filter = ['ativa']
    search_fields = ['nome', 'caminho_script']
    list_editable = ['ativa']


@admin.register(HistoricoExecucao)
class HistoricoExecucaoAdmin(admin.ModelAdmin):
    list_display = ['tarefa', 'status', 'iniciada_em', 'finalizada_em', 'codigo_retorno']
    list_filter = ['status', 'tarefa']
    readonly_fields = ['tarefa', 'iniciada_em', 'finalizada_em', 'status', 'saida', 'erro', 'codigo_retorno']


@admin.register(Configuracao)
class ConfiguracaoAdmin(admin.ModelAdmin):
    list_display = ['chave', 'valor', 'descricao', 'atualizada_em']
    search_fields = ['chave']
    readonly_fields = ['chave', 'atualizada_em']


@admin.register(LogEvento)
class LogEventoAdmin(admin.ModelAdmin):
    list_display = ['criado_em', 'nivel', 'origem', 'mensagem']
    list_filter = ['nivel', 'origem']
    search_fields = ['mensagem', 'origem']
    readonly_fields = ['nivel', 'origem', 'mensagem', 'criado_em']
