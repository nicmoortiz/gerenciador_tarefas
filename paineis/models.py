from django.db import models


MODULO_CHOICES = [
    ('ambulatorial',   'Ambulatorial'),
    ('urgencia',       'Urgência'),
    ('leitos_aih',     'Leitos AIH'),
    ('leitos',         'Leitos'),
    ('pre_hospitalar', 'Pré-Hospitalar'),
    ('indicadores',    'Indicadores'),
    ('outros',         'Outros'),
]


class Servidor(models.Model):
    nome = models.CharField('Nome', max_length=300, unique=True)

    class Meta:
        ordering = ['nome']
        verbose_name = 'Servidor'
        verbose_name_plural = 'Servidores'

    def __str__(self):
        return self.nome


class Banco(models.Model):
    servidor = models.ForeignKey(Servidor, on_delete=models.CASCADE, related_name='bancos')
    nome     = models.CharField('Nome', max_length=300)

    class Meta:
        ordering = ['nome']
        unique_together = [('servidor', 'nome')]
        verbose_name = 'Banco de Dados'
        verbose_name_plural = 'Bancos de Dados'

    def __str__(self):
        return self.nome


class Dashboard(models.Model):
    modulo             = models.CharField('Módulo', max_length=20, choices=MODULO_CHOICES)
    modulo_outros      = models.CharField('Módulo (outros)', max_length=200, blank=True)
    nome_arquivo       = models.CharField('Nome do Arquivo', max_length=300)
    caminho_tableau    = models.TextField('Caminho Tableau', blank=True)
    link_tableau       = models.URLField('Link do Tableau', max_length=500, blank=True)
    setor_solicitante  = models.CharField('Setor Solicitante', max_length=200, blank=True)
    nome_solicitante   = models.CharField('Nome do Solicitante', max_length=200, blank=True)
    data_solicitacao   = models.DateField('Data de Solicitação', null=True, blank=True)
    data_homologacao   = models.DateField('Data de Homologação', null=True, blank=True)
    data_aceite        = models.DateField('Data de Aceite', null=True, blank=True)
    data_publicacao    = models.DateField('Data de Publicação', null=True, blank=True)
    criado_em          = models.DateTimeField(auto_now_add=True)
    atualizado_em      = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nome_arquivo']
        verbose_name = 'Dashboard'
        verbose_name_plural = 'Dashboards'

    def __str__(self):
        return self.nome_arquivo

    def modulo_display(self):
        if self.modulo == 'outros':
            return self.modulo_outros or 'Outros'
        return self.get_modulo_display()


class FonteDeDados(models.Model):
    dashboard     = models.ForeignKey(Dashboard, on_delete=models.CASCADE, related_name='fontes')
    nome          = models.CharField('Nome', max_length=300)
    criado_em     = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nome']
        verbose_name = 'Fonte de Dados'
        verbose_name_plural = 'Fontes de Dados'

    def __str__(self):
        return self.nome


class Conexao(models.Model):
    fonte       = models.ForeignKey(FonteDeDados, on_delete=models.CASCADE, related_name='conexoes')
    servidor    = models.ForeignKey(Servidor, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Servidor')
    banco_dados = models.ForeignKey(Banco, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Banco de Dados')

    class Meta:
        verbose_name = 'Conexão'
        verbose_name_plural = 'Conexões'

    def __str__(self):
        return f'{self.servidor} / {self.banco_dados}'


class Relacionamento(models.Model):
    fonte = models.ForeignKey(FonteDeDados, on_delete=models.CASCADE, related_name='relacionamentos')

    class Meta:
        verbose_name = 'Relacionamento'
        verbose_name_plural = 'Relacionamentos'


class Comando(models.Model):
    fonte = models.ForeignKey(FonteDeDados, on_delete=models.CASCADE, related_name='comandos')

    class Meta:
        verbose_name = 'Comando'
        verbose_name_plural = 'Comandos'


class Filtro(models.Model):
    fonte = models.ForeignKey(FonteDeDados, on_delete=models.CASCADE, related_name='filtros')

    class Meta:
        verbose_name = 'Filtro'
        verbose_name_plural = 'Filtros'


class Imagem(models.Model):
    fonte = models.ForeignKey(FonteDeDados, on_delete=models.CASCADE, related_name='imagens')

    class Meta:
        verbose_name = 'Imagem'
        verbose_name_plural = 'Imagens'


class Planilha(models.Model):
    dashboard = models.ForeignKey(Dashboard, on_delete=models.CASCADE, related_name='planilhas')

    class Meta:
        verbose_name = 'Planilha'
        verbose_name_plural = 'Planilhas'


class Painel(models.Model):
    dashboard = models.ForeignKey(Dashboard, on_delete=models.CASCADE, related_name='paineis')

    class Meta:
        verbose_name = 'Painel'
        verbose_name_plural = 'Painéis'


class Historia(models.Model):
    dashboard = models.ForeignKey(Dashboard, on_delete=models.CASCADE, related_name='historias')

    class Meta:
        verbose_name = 'História'
        verbose_name_plural = 'Histórias'


class Versao(models.Model):
    dashboard = models.ForeignKey(Dashboard, on_delete=models.CASCADE, related_name='versoes')
    numero    = models.CharField('Número da Versão', max_length=50, default='')

    class Meta:
        ordering = ['pk']
        verbose_name = 'Versão'
        verbose_name_plural = 'Versões'

    def __str__(self):
        return self.numero


class RegistroVersao(models.Model):
    versao               = models.ForeignKey(Versao, on_delete=models.CASCADE, related_name='registros')
    nome_desenvolvedor   = models.CharField('Nome do(a) Desenvolvedor(a)', max_length=200)
    data_desenvolvimento = models.DateField('Data do Desenvolvimento')
    acoes_realizadas     = models.TextField('Ações Realizadas')

    class Meta:
        ordering = ['data_desenvolvimento', 'pk']
        verbose_name = 'Registro de Versão'
        verbose_name_plural = 'Registros de Versão'

    def __str__(self):
        return f'{self.versao.numero} — {self.nome_desenvolvedor}'
