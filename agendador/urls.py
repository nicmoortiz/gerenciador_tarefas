from django.urls import path
from . import views

urlpatterns = [
    # Agendador
    path('', views.lista_agendadas, name='lista_agendadas'),
    path('nova/', views.criar_agendada, name='criar_agendada'),
    path('<int:pk>/editar/', views.editar_agendada, name='editar_agendada'),
    path('<int:pk>/excluir/', views.excluir_agendada, name='excluir_agendada'),
    path('<int:pk>/toggle/', views.toggle_ativa, name='toggle_agendada'),
    path('<int:pk>/executar/', views.executar_agora, name='executar_agora'),
    path('<int:pk>/historico/', views.historico_agendada, name='historico_agendada'),
    path('execucao/<int:pk>/', views.detalhe_execucao, name='detalhe_execucao'),

    # Logs
    path('logs/', views.lista_logs, name='lista_logs'),
    path('logs/limpar/', views.limpar_logs, name='limpar_logs'),

    # Configurações
    path('configuracoes/', views.lista_configuracoes, name='lista_configuracoes'),
    path('configuracoes/<int:pk>/editar/', views.editar_configuracao, name='editar_configuracao'),
]
