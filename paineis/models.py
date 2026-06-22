from django.db import models


class Projeto(models.Model):
    nome = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nome']
        verbose_name = 'Projeto'
        verbose_name_plural = 'Projetos'

    def __str__(self):
        return self.nome


class PastaDeTrabalho(models.Model):
    MODULO_CHOICES = [
        ('',                 '— Selecione —'),
        ('ambulatorial',     'Ambulatorial'),
        ('urgencia',         'Urgência'),
        ('leitos_aih',       'Leitos AIH'),
        ('leitos',           'Leitos'),
        ('pre_hospitalar',   'Pré-Hospitalar'),
        ('indicadores',      'Indicadores'),
        ('naep',             'NAEP'),
        ('nucleo_oncologia', 'Núcleo de Oncologia'),
        ('oncologia',        'Oncologia'),
        ('outros',           'Outros'),
    ]

    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE, related_name='pastas')
    nome = models.CharField('Nome', max_length=200)
    local_tableau_server = models.CharField('Local Tableau Server', max_length=500, blank=True)
    modulo = models.CharField('Módulo', max_length=20, choices=MODULO_CHOICES, blank=True)
    modulo_outro = models.CharField('Módulo (outro)', max_length=200, blank=True)
    setor_solicitante = models.CharField('Setor Solicitante', max_length=200, blank=True)
    solicitante = models.CharField('Solicitante', max_length=200, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nome']
        verbose_name = 'Dados do Tableau'
        verbose_name_plural = 'Dados do Tableau'

    def __str__(self):
        return self.nome

    def modulo_display(self):
        if self.modulo == 'outros':
            return self.modulo_outro or 'Outros'
        return self.get_modulo_display()


class RegistroDesenvolvimento(models.Model):
    TIPO_CHOICES = [
        ('desenvolvido', 'Desenvolvido por'),
        ('atualizado',   'Atualizado por'),
    ]

    pasta = models.ForeignKey(PastaDeTrabalho, on_delete=models.CASCADE, related_name='registros')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='desenvolvido')
    nome = models.CharField('Nome', max_length=200)
    data = models.DateField('Data')

    class Meta:
        ordering = ['data', 'pk']
        verbose_name = 'Registro de Desenvolvimento'
        verbose_name_plural = 'Registros de Desenvolvimento'

    def __str__(self):
        return f'{self.get_tipo_display()} — {self.nome}'


class FonteDeDados(models.Model):
    TIPO_CONEXAO = [
        ('tempo_real', 'Em tempo real'),
        ('extracao', 'Extração'),
    ]
    pasta = models.ForeignKey(PastaDeTrabalho, on_delete=models.CASCADE, related_name='fontes')
    nome = models.CharField(max_length=200)
    conexao = models.CharField('Conexão (servidor)', max_length=200, blank=True)
    banco = models.CharField(max_length=200, blank=True)
    tipo_conexao = models.CharField(max_length=20, choices=TIPO_CONEXAO, default='extracao')
    relacao_conexoes = models.TextField('Relação de conexões', blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nome']
        verbose_name = 'Fonte de Dados'
        verbose_name_plural = 'Fontes de Dados'

    def __str__(self):
        return self.nome


class FiltroFonte(models.Model):
    fonte = models.ForeignKey(FonteDeDados, on_delete=models.CASCADE, related_name='filtros')
    nome = models.CharField(max_length=200)
    detalhes = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Filtro'
        verbose_name_plural = 'Filtros'

    def __str__(self):
        return self.nome


class ImagemFonte(models.Model):
    fonte = models.ForeignKey(FonteDeDados, on_delete=models.CASCADE, related_name='imagens')
    legenda = models.CharField(max_length=200, blank=True)
    imagem = models.ImageField(upload_to='paineis/fontes/')
    ordem = models.PositiveIntegerField(default=0)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['ordem', 'criado_em']
        verbose_name = 'Imagem da Fonte'
        verbose_name_plural = 'Imagens da Fonte'


class Planilha(models.Model):
    pasta = models.ForeignKey(PastaDeTrabalho, on_delete=models.CASCADE, related_name='planilhas')
    nome = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    ordem = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['ordem', 'nome']
        verbose_name = 'Planilha'
        verbose_name_plural = 'Planilhas'

    def __str__(self):
        return self.nome


class ImagemPlanilha(models.Model):
    planilha = models.ForeignKey(Planilha, on_delete=models.CASCADE, related_name='imagens')
    secao = models.CharField('Seção', max_length=200, blank=True)
    legenda = models.CharField(max_length=200, blank=True)
    imagem = models.ImageField(upload_to='paineis/planilhas/')
    ordem = models.PositiveIntegerField(default=0)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['ordem', 'criado_em']
        verbose_name = 'Imagem da Planilha'
        verbose_name_plural = 'Imagens da Planilha'


class Painel(models.Model):
    pasta = models.ForeignKey(PastaDeTrabalho, on_delete=models.CASCADE, related_name='paineis')
    nome = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    regras = models.TextField('Regras de negócio', blank=True)
    planilhas = models.ManyToManyField(Planilha, blank=True, related_name='paineis_vinculados')
    ordem = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['ordem', 'nome']
        verbose_name = 'Painel'
        verbose_name_plural = 'Painéis'

    def __str__(self):
        return self.nome


class ImagemPainel(models.Model):
    painel = models.ForeignKey(Painel, on_delete=models.CASCADE, related_name='imagens')
    secao = models.CharField('Seção', max_length=200, blank=True)
    legenda = models.CharField(max_length=200, blank=True)
    imagem = models.ImageField(upload_to='paineis/paineis/')
    ordem = models.PositiveIntegerField(default=0)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['ordem', 'criado_em']
        verbose_name = 'Imagem do Painel'
        verbose_name_plural = 'Imagens do Painel'


class Historia(models.Model):
    pasta = models.ForeignKey(PastaDeTrabalho, on_delete=models.CASCADE, related_name='historias')
    nome = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    ordem = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['ordem', 'nome']
        verbose_name = 'História'
        verbose_name_plural = 'Histórias'

    def __str__(self):
        return self.nome


class ImagemHistoria(models.Model):
    historia = models.ForeignKey(Historia, on_delete=models.CASCADE, related_name='imagens')
    secao = models.CharField('Seção', max_length=200, blank=True)
    legenda = models.CharField(max_length=200, blank=True)
    imagem = models.ImageField(upload_to='paineis/historias/')
    ordem = models.PositiveIntegerField(default=0)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['ordem', 'criado_em']
        verbose_name = 'Imagem da História'
        verbose_name_plural = 'Imagens da História'
