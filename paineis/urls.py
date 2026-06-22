from django.urls import path

from . import views


urlpatterns = [
    path('', views.lista_paineis, name='lista_paineis'),
    path('dashboard/salvar/', views.salvar_dashboard, name='salvar_dashboard'),
    path('dashboard/<int:pk>/fonte/salvar/', views.salvar_fonte, name='salvar_fonte'),
    path('servidor/<int:servidor_pk>/bancos/', views.bancos_do_servidor, name='bancos_do_servidor'),
    path('dashboard/lista/', views.lista_dashboards_json, name='lista_dashboards_json'),
    path('dashboard/<int:pk>/dados/', views.dados_dashboard, name='dados_dashboard'),
    path('servidor/novo/', views.novo_servidor, name='novo_servidor'),
    path('servidor/<int:servidor_pk>/banco/novo/', views.novo_banco, name='novo_banco'),
    path('fonte/<int:fonte_pk>/conexoes/', views.conexoes_da_fonte, name='conexoes_da_fonte'),
    path('fonte/<int:fonte_pk>/conexao/salvar/', views.salvar_conexao, name='salvar_conexao'),
    path('dashboard/<int:pk>/versoes/', views.versoes_do_dashboard, name='versoes_do_dashboard'),
    path('dashboard/<int:pk>/versao/salvar/', views.salvar_versao, name='salvar_versao'),
    path('versao/<int:versao_pk>/registros/', views.registros_da_versao, name='registros_da_versao'),
    path('versao/<int:versao_pk>/registro/salvar/', views.salvar_registro_versao, name='salvar_registro_versao'),
]
