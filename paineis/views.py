import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET

from .models import Dashboard, FonteDeDados, Servidor, Banco, Conexao, Versao, RegistroVersao


def lista_paineis(request):
    return render(request, 'paineis/lista_paineis.html', {
        'paineis': Dashboard.objects.all(),
        'subpaineis_fonte': ['Relacionamentos', 'Comandos', 'Filtros', 'Imagens'],
        'servidores': Servidor.objects.all(),
    })


@require_GET
def lista_dashboards_json(_):
    dados = [
        {
            'id':              d.pk,
            'nome_arquivo':    d.nome_arquivo,
            'modulo':          d.modulo_display(),
            'caminho_tableau': d.caminho_tableau,
            'nome_solicitante': d.nome_solicitante,
        }
        for d in Dashboard.objects.all()
    ]
    return JsonResponse({'dashboards': dados})


@require_GET
def dados_dashboard(_, pk):
    try:
        db = Dashboard.objects.get(pk=pk)
        fontes = []
        for f in db.fontes.all():
            fontes.append({'id': f.pk, 'nome': f.nome})
        return JsonResponse({
            'ok': True,
            'id':              db.pk,
            'modulo':          db.modulo,
            'modulo_outros':   db.modulo_outros,
            'nome_arquivo':    db.nome_arquivo,
            'caminho_tableau': db.caminho_tableau,
            'link_tableau':    db.link_tableau,
            'fontes':          fontes,
        })
    except Dashboard.DoesNotExist:
        return JsonResponse({'ok': False, 'erro': 'Não encontrado'}, status=404)


@require_POST
def novo_servidor(request):
    try:
        data = json.loads(request.body)
        nome = data.get('nome', '').strip()
        if not nome:
            return JsonResponse({'ok': False, 'erro': 'Nome obrigatório'}, status=400)
        servidor, criado = Servidor.objects.get_or_create(nome=nome)
        return JsonResponse({'ok': True, 'id': servidor.pk, 'nome': servidor.nome, 'criado': criado})
    except Exception as e:
        return JsonResponse({'ok': False, 'erro': str(e)}, status=400)


@require_POST
def novo_banco(request, servidor_pk):
    try:
        servidor = Servidor.objects.get(pk=servidor_pk)
        data = json.loads(request.body)
        nome = data.get('nome', '').strip()
        if not nome:
            return JsonResponse({'ok': False, 'erro': 'Nome obrigatório'}, status=400)
        banco, criado = Banco.objects.get_or_create(servidor=servidor, nome=nome)
        return JsonResponse({'ok': True, 'id': banco.pk, 'nome': banco.nome, 'criado': criado})
    except Servidor.DoesNotExist:
        return JsonResponse({'ok': False, 'erro': 'Servidor não encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'ok': False, 'erro': str(e)}, status=400)


@require_GET
def bancos_do_servidor(_, servidor_pk):
    bancos = list(Banco.objects.filter(servidor_id=servidor_pk).values('id', 'nome'))
    return JsonResponse({'bancos': bancos})


@require_POST
def salvar_dashboard(request):
    try:
        data = json.loads(request.body)
        pk = data.get('id')

        campos = {
            'modulo':           data.get('modulo', ''),
            'modulo_outros':    data.get('modulo_outros', ''),
            'nome_arquivo':     data.get('nome_arquivo', ''),
            'caminho_tableau':  data.get('caminho_tableau', ''),
            'link_tableau':     data.get('link_tableau', ''),
        }

        if pk:
            Dashboard.objects.filter(pk=pk).update(**campos)
            dashboard = Dashboard.objects.get(pk=pk)
        else:
            dashboard = Dashboard.objects.create(**campos)

        return JsonResponse({'ok': True, 'id': dashboard.pk})
    except Exception as e:
        return JsonResponse({'ok': False, 'erro': str(e)}, status=400)


@require_GET
def versoes_do_dashboard(_, pk):
    versoes = list(Versao.objects.filter(dashboard_id=pk).values('id', 'numero'))
    return JsonResponse({'versoes': versoes})


@require_POST
def salvar_versao(request, pk):
    try:
        dashboard = Dashboard.objects.get(pk=pk)
        data      = json.loads(request.body)
        versao_pk = data.get('id')
        numero    = data.get('numero', '').strip()
        if not numero:
            return JsonResponse({'ok': False, 'erro': 'Número obrigatório'}, status=400)
        if versao_pk:
            Versao.objects.filter(pk=versao_pk, dashboard=dashboard).update(numero=numero)
            versao = Versao.objects.get(pk=versao_pk)
        else:
            versao = Versao.objects.create(dashboard=dashboard, numero=numero)
        return JsonResponse({'ok': True, 'id': versao.pk})
    except Dashboard.DoesNotExist:
        return JsonResponse({'ok': False, 'erro': 'Dashboard não encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'ok': False, 'erro': str(e)}, status=400)


@require_GET
def registros_da_versao(_, versao_pk):
    registros = list(
        RegistroVersao.objects.filter(versao_id=versao_pk)
        .values('id', 'nome_desenvolvedor', 'data_desenvolvimento', 'acoes_realizadas')
    )
    for r in registros:
        if r['data_desenvolvimento']:
            r['data_desenvolvimento'] = r['data_desenvolvimento'].isoformat()
    return JsonResponse({'registros': registros})


@require_POST
def salvar_registro_versao(request, versao_pk):
    try:
        versao    = Versao.objects.get(pk=versao_pk)
        data      = json.loads(request.body)
        reg_pk    = data.get('id')
        campos    = {
            'nome_desenvolvedor':   data.get('nome_desenvolvedor', '').strip(),
            'data_desenvolvimento': data.get('data_desenvolvimento') or None,
            'acoes_realizadas':     data.get('acoes_realizadas', '').strip(),
        }
        if reg_pk:
            RegistroVersao.objects.filter(pk=reg_pk, versao=versao).update(**campos)
            reg = RegistroVersao.objects.get(pk=reg_pk)
        else:
            reg = RegistroVersao.objects.create(versao=versao, **campos)
        return JsonResponse({'ok': True, 'id': reg.pk})
    except Versao.DoesNotExist:
        return JsonResponse({'ok': False, 'erro': 'Versão não encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'ok': False, 'erro': str(e)}, status=400)


@require_POST
def salvar_fonte(request, pk):
    try:
        dashboard = Dashboard.objects.get(pk=pk)
        data      = json.loads(request.body)
        fonte_pk  = data.get('id')
        nome      = data.get('nome', '')

        if fonte_pk:
            FonteDeDados.objects.filter(pk=fonte_pk, dashboard=dashboard).update(nome=nome)
            fonte = FonteDeDados.objects.get(pk=fonte_pk)
        else:
            fonte = FonteDeDados.objects.create(dashboard=dashboard, nome=nome)

        return JsonResponse({'ok': True, 'id': fonte.pk})
    except Dashboard.DoesNotExist:
        return JsonResponse({'ok': False, 'erro': 'Dashboard não encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'ok': False, 'erro': str(e)}, status=400)


@require_GET
def conexoes_da_fonte(_, fonte_pk):
    conexoes = []
    for c in Conexao.objects.filter(fonte_id=fonte_pk).select_related('servidor', 'banco_dados'):
        conexoes.append({
            'id':           c.pk,
            'servidor_id':  c.servidor_id,
            'servidor_nome': c.servidor.nome if c.servidor else '',
            'banco_id':     c.banco_dados_id,
            'banco_nome':   c.banco_dados.nome if c.banco_dados else '',
        })
    return JsonResponse({'conexoes': conexoes})


@require_POST
def salvar_conexao(request, fonte_pk):
    try:
        fonte       = FonteDeDados.objects.get(pk=fonte_pk)
        data        = json.loads(request.body)
        conexao_pk  = data.get('id')
        servidor_id = data.get('servidor_id') or None
        banco_id    = data.get('banco_id') or None

        campos = {'servidor_id': servidor_id, 'banco_dados_id': banco_id}

        if conexao_pk:
            Conexao.objects.filter(pk=conexao_pk, fonte=fonte).update(**campos)
            conexao = Conexao.objects.get(pk=conexao_pk)
        else:
            conexao = Conexao.objects.create(fonte=fonte, **campos)

        return JsonResponse({'ok': True, 'id': conexao.pk})
    except FonteDeDados.DoesNotExist:
        return JsonResponse({'ok': False, 'erro': 'Fonte não encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'ok': False, 'erro': str(e)}, status=400)
