import threading
from datetime import date, time
from django.shortcuts import render, get_object_or_404, redirect
from django import forms as django_forms
from .models import TarefaAgendada, HistoricoExecucao, Configuracao, LogEvento
from .forms import TarefaAgendadaForm
from . import scheduler as sched

TIPOS_AGENDAMENTO = TarefaAgendada.TIPO_CHOICES

DIAS_SEMANA_CHOICES = [
    ('mon', 'Seg'), ('tue', 'Ter'), ('wed', 'Qua'),
    ('thu', 'Qui'), ('fri', 'Sex'), ('sat', 'Sáb'), ('sun', 'Dom'),
]

MESES_CHOICES = [
    ('1','Jan'),('2','Fev'),('3','Mar'),('4','Abr'),('5','Mai'),('6','Jun'),
    ('7','Jul'),('8','Ago'),('9','Set'),('10','Out'),('11','Nov'),('12','Dez'),
]

CONTEXTO_FORM = {
    'tipos': TIPOS_AGENDAMENTO,
    'dias_semana_choices': DIAS_SEMANA_CHOICES,
    'meses_choices': MESES_CHOICES,
    'dias_mes_range': range(1, 32),
}


def _proximas(tarefas):
    for t in tarefas:
        t.proxima_execucao = sched.proxima_execucao(t.pk) if t.ativa else None
    return tarefas


def _extrair_agendamento(post):
    """Extrai e valida os campos de agendamento do POST. Retorna (dados, erros)."""
    tipo = post.get('tipo_agendamento', 'diario')
    dados = {'tipo_agendamento': tipo}
    erros = {}

    # horario
    horario_str = post.get('horario', '').strip()
    if horario_str:
        try:
            h, m = horario_str.split(':')
            dados['horario'] = time(int(h), int(m))
        except Exception:
            erros['horario'] = 'Formato inválido. Use HH:MM.'
    else:
        dados['horario'] = None

    # data_inicio
    data_str = post.get('data_inicio', '').strip()
    if data_str:
        try:
            dados['data_inicio'] = date.fromisoformat(data_str)
        except Exception:
            erros['data_inicio'] = 'Data inválida.'
    else:
        dados['data_inicio'] = None

    # Validações por tipo
    precisa_horario = tipo in ('diario', 'dias_uteis', 'uma_vez', 'semanal', 'mensal')
    precisa_data    = tipo in ('diario', 'dias_uteis', 'uma_vez', 'semanal', 'mensal')

    if precisa_horario and not dados.get('horario'):
        erros['horario'] = 'Informe o horário.'

    if precisa_data and not dados.get('data_inicio'):
        erros['data_inicio'] = 'Informe a data de início.'

    if tipo == 'dias_uteis' and dados.get('data_inicio'):
        if dados['data_inicio'].weekday() > 4:
            erros['data_inicio'] = 'A data de início deve ser um dia útil (segunda a sexta-feira).'

    if tipo == 'semanal':
        dias = post.get('dias_semana', '').strip()
        dados['dias_semana'] = dias
        if not dias:
            erros['dias_semana'] = 'Selecione pelo menos um dia da semana.'
        try:
            dados['repetir_semanas'] = max(1, int(post.get('repetir_semanas', 1)))
        except Exception:
            dados['repetir_semanas'] = 1

    if tipo == 'mensal':
        dias_mes = post.get('dias_mes', '').strip()
        dados['dias_mes'] = dias_mes
        if not dias_mes:
            erros['dias_mes'] = 'Selecione pelo menos um dia do mês.'
        meses = post.get('meses_execucao', '*').strip() or '*'
        dados['meses_execucao'] = meses

    if tipo == 'intervalo':
        try:
            valor = int(post.get('intervalo_valor', 0))
            unidade = post.get('intervalo_unidade', 'minutos')
            if valor < 1:
                raise ValueError
            multiplicador = {'minutos': 1, 'horas': 60}.get(unidade, 1)
            dados['intervalo_minutos'] = valor * multiplicador
        except Exception:
            erros['intervalo_minutos'] = 'Informe um valor válido (mínimo 1).'

    return dados, erros


def _intervalo_para_display(minutos):
    """Converte minutos de volta para (valor, unidade) para exibir no formulário."""
    if minutos and minutos % 60 == 0:
        return minutos // 60, 'horas'
    return minutos or 30, 'minutos'


def _aplicar_agendamento(tarefa, dados):
    """Aplica os campos de agendamento ao objeto tarefa."""
    campos = ['tipo_agendamento', 'horario', 'data_inicio', 'intervalo_minutos',
              'dias_semana', 'repetir_semanas', 'dias_mes', 'meses_execucao']
    for campo in campos:
        if campo in dados:
            setattr(tarefa, campo, dados[campo])


# ── Agendador ─────────────────────────────────────────────────────────────────

def lista_agendadas(request):
    tarefas = list(TarefaAgendada.objects.all())
    _proximas(tarefas)
    return render(request, 'agendador/lista.html', {'tarefas': tarefas})


def criar_agendada(request):
    if request.method == 'POST':
        form = TarefaAgendadaForm(request.POST)
        dados_agend, erros_agend = _extrair_agendamento(request.POST)

        if form.is_valid() and not erros_agend:
            tarefa = form.save(commit=False)
            _aplicar_agendamento(tarefa, dados_agend)
            tarefa.save()
            if tarefa.ativa:
                sched.agendar(tarefa)
            return redirect('lista_agendadas')
    else:
        form = TarefaAgendadaForm()
        dados_agend = {}
        erros_agend = {}

    intervalo_valor, intervalo_unidade = _intervalo_para_display(None)
    return render(request, 'agendador/form.html', {
        **CONTEXTO_FORM,
        'form': form,
        'titulo': 'Novo Agendamento',
        'dados_agend': dados_agend,
        'erros_agend': erros_agend,
        'intervalo_valor': intervalo_valor,
        'intervalo_unidade': intervalo_unidade,
    })


def editar_agendada(request, pk):
    tarefa = get_object_or_404(TarefaAgendada, pk=pk)
    if request.method == 'POST':
        form = TarefaAgendadaForm(request.POST, instance=tarefa)
        dados_agend, erros_agend = _extrair_agendamento(request.POST)

        if form.is_valid() and not erros_agend:
            tarefa = form.save(commit=False)
            _aplicar_agendamento(tarefa, dados_agend)
            tarefa.save()
            sched.remover(tarefa.pk)
            if tarefa.ativa:
                sched.agendar(tarefa)
            return redirect('lista_agendadas')
    else:
        from pathlib import Path
        partes = Path(tarefa.caminho_script).parts if tarefa.caminho_script else []
        initial = {}
        if len(partes) >= 3:
            initial['pasta_script'] = partes[1]
            initial['nome_script'] = partes[2]
        form = TarefaAgendadaForm(instance=tarefa, initial=initial)
        dados_agend = {}
        erros_agend = {}

    intervalo_valor, intervalo_unidade = _intervalo_para_display(tarefa.intervalo_minutos)
    return render(request, 'agendador/form.html', {
        **CONTEXTO_FORM,
        'form': form,
        'tarefa': tarefa,
        'titulo': 'Editar Agendamento',
        'dados_agend': dados_agend,
        'erros_agend': erros_agend,
        'intervalo_valor': intervalo_valor,
        'intervalo_unidade': intervalo_unidade,
    })


def excluir_agendada(request, pk):
    tarefa = get_object_or_404(TarefaAgendada, pk=pk)
    if request.method == 'POST':
        sched.remover(tarefa.pk)
        tarefa.delete()
        return redirect('lista_agendadas')
    return render(request, 'agendador/confirmar_exclusao.html', {'tarefa': tarefa})


def toggle_ativa(request, pk):
    tarefa = get_object_or_404(TarefaAgendada, pk=pk)
    tarefa.ativa = not tarefa.ativa
    tarefa.save(update_fields=['ativa'])
    if tarefa.ativa:
        sched.agendar(tarefa)
    else:
        sched.remover(tarefa.pk)
    return redirect('lista_agendadas')


def executar_agora(request, pk):
    tarefa = get_object_or_404(TarefaAgendada, pk=pk)
    t = threading.Thread(target=sched.executar_script, args=[tarefa.pk], daemon=True)
    t.start()
    return redirect('historico_agendada', pk=pk)


def historico_agendada(request, pk):
    tarefa = get_object_or_404(TarefaAgendada, pk=pk)
    historico = tarefa.historico.all()[:50]
    return render(request, 'agendador/historico.html', {'tarefa': tarefa, 'historico': historico})


def detalhe_execucao(request, pk):
    execucao = get_object_or_404(HistoricoExecucao, pk=pk)
    return render(request, 'agendador/detalhe_execucao.html', {'execucao': execucao})


# ── Logs ──────────────────────────────────────────────────────────────────────

def lista_logs(request):
    nivel = request.GET.get('nivel', '')
    origem = request.GET.get('origem', '')
    logs = LogEvento.objects.all()
    if nivel:
        logs = logs.filter(nivel=nivel)
    if origem:
        logs = logs.filter(origem__icontains=origem)
    logs = logs[:200]
    origens = LogEvento.objects.values_list('origem', flat=True).distinct().order_by('origem')
    return render(request, 'agendador/logs.html', {
        'logs': logs, 'origens': origens, 'niveis': LogEvento.NIVEL_CHOICES,
        'filtro_nivel': nivel, 'filtro_origem': origem,
    })


def limpar_logs(request):
    if request.method == 'POST':
        nivel = request.POST.get('nivel', '')
        if nivel:
            LogEvento.objects.filter(nivel=nivel).delete()
        else:
            LogEvento.objects.all().delete()
    return redirect('lista_logs')


# ── Configurações ─────────────────────────────────────────────────────────────

class ConfiguracaoForm(django_forms.ModelForm):
    class Meta:
        model = Configuracao
        fields = ['valor', 'descricao']
        widgets = {
            'valor': django_forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': django_forms.TextInput(attrs={'class': 'form-control'}),
        }


def lista_configuracoes(request):
    configuracoes = Configuracao.objects.all()
    return render(request, 'agendador/configuracoes.html', {'configuracoes': configuracoes})


def editar_configuracao(request, pk):
    config = get_object_or_404(Configuracao, pk=pk)
    if request.method == 'POST':
        form = ConfiguracaoForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            return redirect('lista_configuracoes')
    else:
        form = ConfiguracaoForm(instance=config)
    return render(request, 'agendador/form_configuracao.html', {'form': form, 'config': config})
