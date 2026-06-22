import subprocess
import threading
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler(timezone='America/Sao_Paulo')
_lock = threading.Lock()


def _monitorar_processo(proc, tarefa_id, historico_id, timeout=3600):
    """Aguarda o processo filho e persiste o resultado. Roda em thread daemon."""
    from django.db import close_old_connections
    from django.utils import timezone as tz
    from .models import HistoricoExecucao, TarefaAgendada

    stdout, stderr, codigo, status = '', '', -1, 'erro'
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
        codigo = proc.returncode
        status = 'sucesso' if codigo == 0 else 'erro'
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, stderr = proc.communicate()
        stderr = 'Timeout: execução excedeu 1 hora.'
    except Exception as exc:
        try:
            proc.kill()
        except Exception:
            pass
        stderr = str(exc)

    close_old_connections()
    now = tz.now()
    HistoricoExecucao.objects.filter(pk=historico_id).update(
        saida=stdout,
        erro=stderr,
        codigo_retorno=codigo,
        status=status,
        finalizada_em=now,
    )
    TarefaAgendada.objects.filter(pk=tarefa_id).update(ultima_execucao=now)


def executar_script(tarefa_id):
    """Lança o script em processo separado e retorna imediatamente.

    O monitoramento (captura de saída + gravação do histórico) ocorre em
    uma thread daemon independente, sem bloquear o pool do APScheduler.
    """
    from django.db import close_old_connections
    from django.conf import settings
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

    caminho = settings.BASE_DIR / tarefa.caminho_script
    try:
        proc = subprocess.Popen(
            ['python', str(caminho)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except FileNotFoundError:
        historico.status = 'erro'
        historico.erro = f'Script não encontrado: {tarefa.caminho_script}'
        historico.finalizada_em = timezone.now()
        historico.save()
        return
    except Exception as exc:
        historico.status = 'erro'
        historico.erro = str(exc)
        historico.finalizada_em = timezone.now()
        historico.save()
        return

    threading.Thread(
        target=_monitorar_processo,
        args=[proc, tarefa_id, historico.pk],
        daemon=True,
    ).start()


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
