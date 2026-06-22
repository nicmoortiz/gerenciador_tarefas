from django.urls import path
from . import views

urlpatterns = [
    # Projetos (= página principal com todas as abas)
    path('', views.lista_projetos, name='lista_projetos'),
    path('novo/', views.criar_projeto, name='criar_projeto'),
    path('<int:pk>/', views.detalhe_projeto, name='detalhe_projeto'),
    path('<int:pk>/excluir/', views.excluir_projeto, name='excluir_projeto'),
    path('<int:pk>/exportar/', views.exportar_word, name='exportar_word'),

    # Dados do Tableau (pasta de trabalho)
    path('pasta/<int:pk>/excluir/', views.excluir_pasta, name='excluir_pasta'),

    # Registros de Desenvolvimento
    path('pasta/<int:pasta_pk>/registro/novo/', views.adicionar_registro, name='adicionar_registro'),
    path('registro/<int:pk>/excluir/', views.excluir_registro, name='excluir_registro'),

    # Fontes de Dados
    path('pasta/<int:pasta_pk>/fonte/nova/', views.criar_fonte, name='criar_fonte'),
    path('fonte/<int:pk>/', views.detalhe_fonte, name='detalhe_fonte'),
    path('fonte/<int:pk>/editar/', views.editar_fonte, name='editar_fonte'),
    path('fonte/<int:pk>/excluir/', views.excluir_fonte, name='excluir_fonte'),
    path('fonte/<int:fonte_pk>/filtro/novo/', views.criar_filtro, name='criar_filtro'),
    path('filtro/<int:pk>/editar/', views.editar_filtro, name='editar_filtro'),
    path('filtro/<int:pk>/excluir/', views.excluir_filtro, name='excluir_filtro'),
    path('fonte/<int:fonte_pk>/imagem/nova/', views.adicionar_imagem_fonte, name='adicionar_imagem_fonte'),
    path('imagem-fonte/<int:pk>/excluir/', views.excluir_imagem_fonte, name='excluir_imagem_fonte'),

    # Planilhas
    path('pasta/<int:pasta_pk>/planilha/nova/', views.criar_planilha, name='criar_planilha'),
    path('planilha/<int:pk>/', views.detalhe_planilha, name='detalhe_planilha'),
    path('planilha/<int:pk>/editar/', views.editar_planilha, name='editar_planilha'),
    path('planilha/<int:pk>/excluir/', views.excluir_planilha, name='excluir_planilha'),
    path('planilha/<int:planilha_pk>/imagem/nova/', views.adicionar_imagem_planilha, name='adicionar_imagem_planilha'),
    path('imagem-planilha/<int:pk>/excluir/', views.excluir_imagem_planilha, name='excluir_imagem_planilha'),

    # Painéis
    path('pasta/<int:pasta_pk>/painel/novo/', views.criar_painel, name='criar_painel'),
    path('painel/<int:pk>/', views.detalhe_painel, name='detalhe_painel'),
    path('painel/<int:pk>/editar/', views.editar_painel, name='editar_painel'),
    path('painel/<int:pk>/excluir/', views.excluir_painel, name='excluir_painel'),
    path('painel/<int:painel_pk>/imagem/nova/', views.adicionar_imagem_painel, name='adicionar_imagem_painel'),
    path('imagem-painel/<int:pk>/excluir/', views.excluir_imagem_painel, name='excluir_imagem_painel'),

    # Histórias
    path('pasta/<int:pasta_pk>/historia/nova/', views.criar_historia, name='criar_historia'),
    path('historia/<int:pk>/', views.detalhe_historia, name='detalhe_historia'),
    path('historia/<int:pk>/editar/', views.editar_historia, name='editar_historia'),
    path('historia/<int:pk>/excluir/', views.excluir_historia, name='excluir_historia'),
    path('historia/<int:historia_pk>/imagem/nova/', views.adicionar_imagem_historia, name='adicionar_imagem_historia'),
    path('imagem-historia/<int:pk>/excluir/', views.excluir_imagem_historia, name='excluir_imagem_historia'),
]
