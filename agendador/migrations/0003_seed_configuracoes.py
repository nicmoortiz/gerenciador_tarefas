from django.db import migrations


CONFIGS_INICIAIS = [
    (
        'CAMINHO_LOG',
        r'C:\Configs\Logs',
        'Diretório de fallback para arquivos .txt quando o banco não estiver disponível.',
    ),
    (
        'DRIVER_SQL_SERVER',
        'ODBC Driver 17 for SQL Server',
        'Driver ODBC usado nas conexões com o SQL Server.',
    ),
]


def seed(apps, schema_editor):
    Configuracao = apps.get_model('agendador', 'Configuracao')
    for chave, valor, descricao in CONFIGS_INICIAIS:
        Configuracao.objects.get_or_create(
            chave=chave,
            defaults={'valor': valor, 'descricao': descricao},
        )


class Migration(migrations.Migration):
    dependencies = [
        ('agendador', '0002_configuracao_logevento'),
    ]
    operations = [
        migrations.RunPython(seed, migrations.RunPython.noop),
    ]
