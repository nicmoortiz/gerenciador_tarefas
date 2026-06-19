import os
from django.core.management.base import BaseCommand
from agendador.models import LogEvento, Configuracao


class Command(BaseCommand):
    help = 'Testa as funções do utils.py'

    def handle(self, *args, **kwargs):
        self.stdout.write('\n=== Testando utils.py ===\n')
        erros = 0

        # ── 1. configurar_logging ─────────────────────────────────────────────
        self.stdout.write('1. configurar_logging ...')
        try:
            from utils import configurar_logging

            total_antes = LogEvento.objects.count()
            logger = configurar_logging('teste_utils')
            logger.info('Mensagem de teste INFO')
            logger.warning('Mensagem de teste WARNING')
            logger.error('Mensagem de teste ERROR')
            total_depois = LogEvento.objects.count()

            novos = total_depois - total_antes
            if novos == 3:
                self.stdout.write(self.style.SUCCESS(f'   OK — {novos} registros gravados no banco'))
            else:
                self.stdout.write(self.style.ERROR(f'   FALHOU — esperava 3 registros, gravou {novos}'))
                erros += 1
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ERRO — {e}'))
            erros += 1

        # ── 2. _config com chave existente ────────────────────────────────────
        self.stdout.write('2. _config (chave existente) ...')
        try:
            from utils import _config

            valor = _config('CAMINHO_LOG', 'PADRAO')
            if valor and valor != 'PADRAO':
                self.stdout.write(self.style.SUCCESS(f'   OK — CAMINHO_LOG = {valor}'))
            else:
                self.stdout.write(self.style.ERROR('   FALHOU — chave não encontrada no banco'))
                erros += 1
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ERRO — {e}'))
            erros += 1

        # ── 3. _config com chave inexistente (deve retornar o padrão) ─────────
        self.stdout.write('3. _config (chave inexistente) ...')
        try:
            valor = _config('CHAVE_QUE_NAO_EXISTE', 'meu_padrao')
            if valor == 'meu_padrao':
                self.stdout.write(self.style.SUCCESS('   OK — retornou o valor padrão corretamente'))
            else:
                self.stdout.write(self.style.ERROR(f'   FALHOU — retornou "{valor}" em vez do padrão'))
                erros += 1
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ERRO — {e}'))
            erros += 1

        # ── 4. Variáveis de ambiente (.env) ───────────────────────────────────
        self.stdout.write('4. Variáveis de ambiente (.env) ...')
        variaveis = [
            'servidorProducao', 'bancoProducao', 'usuarioProducao', 'senhaProducao',
            'servidorMRA',      'bancoMRA',      'usuarioMRA',      'senhaMRA',
        ]
        ausentes = [v for v in variaveis if not os.getenv(v)]
        if not ausentes:
            self.stdout.write(self.style.SUCCESS('   OK — todas as variáveis estão definidas'))
        else:
            self.stdout.write(self.style.WARNING(f'   AVISO — variáveis não definidas: {", ".join(ausentes)}'))
            self.stdout.write('          Verifique o caminho do .env em utils.py')

        # ── 5. CriarConexaoProducao (apenas verifica se executa sem crash) ────
        self.stdout.write('5. CriarConexaoProducao ...')
        if ausentes:
            self.stdout.write(self.style.WARNING('   PULADO — variáveis do .env ausentes'))
        else:
            try:
                from utils import CriarConexaoProducao
                conn = CriarConexaoProducao()
                conn.close()
                self.stdout.write(self.style.SUCCESS('   OK — conexão estabelecida e fechada'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'   FALHOU — {e}'))
                erros += 1

        # ── 6. CriarConexaoMRA ────────────────────────────────────────────────
        self.stdout.write('6. CriarConexaoMRA ...')
        if ausentes:
            self.stdout.write(self.style.WARNING('   PULADO — variáveis do .env ausentes'))
        else:
            try:
                from utils import CriarConexaoMRA
                conn = CriarConexaoMRA()
                conn.close()
                self.stdout.write(self.style.SUCCESS('   OK — conexão estabelecida e fechada'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'   FALHOU — {e}'))
                erros += 1

        # ── Resultado final ───────────────────────────────────────────────────
        self.stdout.write('')
        if erros == 0:
            self.stdout.write(self.style.SUCCESS('Todos os testes passaram.'))
        else:
            self.stdout.write(self.style.ERROR(f'{erros} teste(s) falharam.'))
        self.stdout.write('')
