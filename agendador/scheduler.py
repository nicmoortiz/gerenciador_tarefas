import subprocess
import threading
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler(timezone='America/Sao_Paulo')
_lock = threading.Lock()


def executar_script(tarefa_id):
    """Executa o script Python da tarefa e grava o histórico."""
    from django.db import close_old_connections
    from django.utils import timezone
    from .models import TarefaAgendada, HistoricoExecucao

    close_old_connections()

    try:
        tarefa = TarefaAgendada.objects.get(pk=tarefa_id)
    except TarefaAgendada.DoesNotExist:
        return

    historico = HistoricoExecucao.objects.create(
        tarefa=tarefa,
        iniciada_em=timezone.now(),
        status='rodando',
    )

    try:
        from django.conf import settings
        caminho = settings.BASE_DIR / tarefa.caminho_script
        cmd = ['python', str(caminho)]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
        historico.saida = result.stdout
        historico.erro = result.stderr
        historico.codigo_retorno = result.returncode
        historico.status = 'sucesso' if result.returncode == 0 else 'erro'
    except subprocess.TimeoutExpired:
        historico.status = 'erro'
        historico.erro = 'Timeout: execução excedeu 1 hora.'
    except FileNotFoundError:
        historico.status = 'erro'
        historico.erro = f'Script não encontrado: {tarefa.caminho_script}'
    except Exception as exc:
        historico.status = 'erro'
        historico.erro = str(exc)
    finally:
        from django.utils import timezone as tz
        historico.finalizada_em = tz.now()
        historico.save()
        TarefaAgendada.objects.filter(pk=tarefa_id).update(
            ultima_execucao=historico.iniciada_em
        )


def agendar(tarefa):
    """Adiciona ou atualiza o job no scheduler usando o tipo de trigger da tarefa."""
    job_id = f'tarefa_{tarefa.pk}'
    trigger_tipo, trigger_kwargs = tarefa.get_trigger()

    scheduler.add_job(
        executar_script,
        trigger_tipo,
        id=job_id,
        args=[tarefa.pk],
        replace_existing=True,
        misfire_grace_time=60,
        **trigger_kwargs,
    )


def remover(tarefa_id):
    job_id = f'tarefa_{tarefa_id}'
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)


def proxima_execucao(tarefa_id):
    job = scheduler.get_job(f'tarefa_{tarefa_id}')
    return job.next_run_time if job else None


def start_scheduler():
    with _lock:
        if scheduler.running:
            return
        scheduler.start()

    from .models import TarefaAgendada
    for tarefa in TarefaAgendada.objects.filter(ativa=True):
        agendar(tarefa)
