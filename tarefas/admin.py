from django.contrib import admin
from .models import Tarefa


@admin.register(Tarefa)
class TarefaAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'prioridade', 'concluida', 'criada_em']
    list_filter = ['concluida', 'prioridade']
    search_fields = ['titulo', 'descricao']
    list_editable = ['concluida']
