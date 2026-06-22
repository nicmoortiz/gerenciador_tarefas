from dotenv import load_dotenv
import os
from io import BytesIO
import sys
import pymysql
current_dir = os.path.dirname(__file__)
relative_path = r"C:\Users\vanessa.almeida\Documents\GitHub\Publico\metodo_cross"
target_path = os.path.abspath(os.path.join(current_dir, relative_path))
sys.path.insert(0, target_path)
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import pandas as pd
from sqlalchemy import create_engine, text
import urllib
from IPython.display import display
import calendar
from shareplum import Office365
from datetime import datetime, date, timedelta
import pandas as pd
import metodos_cross as mc
import pyodbc
import pandas as pd
from bs4 import BeautifulSoup

# Configuração Banco de Dados #
caminho_env = r"C:\Configs\Variaveis\.env"
load_dotenv(caminho_env)
### Produção ###
servidorProducao = os.getenv("servidorProducao")
bancoProducao = os.getenv("bancoProducao")
usuarioProducao = os.getenv("usuarioProducao")
senhaProducao = os.getenv("senhaProducao")
parametros_bdProducao = ("DRIVER={" + "ODBC Driver 17 for SQL Server" + "};SERVER=" + servidorProducao + ";DATABASE=" + bancoProducao + ";UID=" + usuarioProducao + ";PWD=" + senhaProducao)        
mecanismoProducao = create_engine("mssql+pyodbc:///?odbc_connect=%s" % urllib.parse.quote_plus(parametros_bdProducao)) 

### Desenvolvimento ###
servidorLibia = os.getenv("servidorLibia")
bancoLibia = os.getenv("bancoLibia")
usuarioLibia = os.getenv("usuarioLibia")
senhaLibia = os.getenv("senhaLibia")

parametrosLibia= ("DRIVER={" + "ODBC Driver 17 for SQL Server" + "};SERVER=" + servidorLibia + ";DATABASE=" + bancoLibia  + ";UID=" + usuarioLibia  + ";PWD=" + senhaLibia)        
mecanismoLibia  = create_engine("mssql+pyodbc:///?odbc_connect=%s" % urllib.parse.quote_plus(parametrosLibia)) 

#Funções Auxiliares
def IncluirDados(dataframe,tabela,conexao):
    dataframe.to_sql(name=tabela, con=conexao, if_exists='append', index=False, chunksize =1000) 


conexaoProducao = mecanismoProducao.connect()
conexaoLibiaWork   = mecanismoLibia.connect() 

def ApagarDados(): 
    print(f"[{datetime.now().strftime('%d/%m/%Y %H:%M')}] (Inicio) ApagarDados")
    with conexaoLibiaWork.begin():
        conexaoLibiaWork.execute(text(f"""DELETE FROM TB_TEMPO_CUIDAR_CONTATO_HISTORICO """))            
        conexaoLibiaWork.commit     
    print(f"[{datetime.now().strftime('%d/%m/%Y %H:%M')}] (Final) ApagarDados")

def CargaDados():
    Comando = f'''
                SELECT 
                    HISTORICO.AHC_ID_HORARIO			CODIGO_HORARIO,
                    HISTORICO.AHC_COD_PACIENTE			CODIGO_PACIENTE,
                    HISTORICO.AHC_ID_MOTIVO				CODIGO_MOTIVO,
                    UPPER(MOTIVO.DESCRICAO)				DESCRICAO_MOTIVO,
                    UPPER(HISTORICO.AHC_TXT_OBSERVACAO)	OBSERVACAO,
                    HISTORICO.AHC_COD_UNIDADE			CODIGO_UNIDADE,
                    UNIDADE.UNIDADE_FANTASIA			NOME_UNIDADE,                    
                    HISTORICO.AHC_COD_USUARIO			CODIGO_USUARIO,
                    USUARIO.NOME						NOME_USUARIO,
                    HISTORICO.AHC_DAT_ACAO				DATA_ACAO
                FROM 
                    AMB_AGE_HISTORICO_CONTATO HISTORICO 
                LEFT JOIN ADMAMB_USUARIO USUARIO ON USUARIO.COD_USUARIO = HISTORICO.AHC_COD_USUARIO
                LEFT JOIN ADMAMB_ADM_UNIDADE UNIDADE ON UNIDADE.COD_UNIDADE = HISTORICO.AHC_COD_UNIDADE
                LEFT JOIN AMB_MOTIVO MOTIVO ON MOTIVO.ID_MOTIVO = HISTORICO.AHC_ID_MOTIVO AND  MOTIVO.TIPO_MOTIVO = 'O'
                WHERE HISTORICO.AHC_ID_MOTIVO IN (SELECT ID_MOTIVO FROM AMB_MOTIVO MOTIVO WHERE MOTIVO.TIPO_MOTIVO = 'O')     
                '''    
    dfDadosProducao = pd.read_sql_query(Comando, conexaoProducao)

    print(f"[{datetime.now().strftime('%d/%m/%Y %H:%M')}] (Inicio) Colocando os dados na tabela TB_TEMPO_CUIDAR_HISTORICO_CONTATO")
    IncluirDados(dfDadosProducao, "TB_TEMPO_CUIDAR_CONTATO_HISTORICO", conexaoLibiaWork)
    conexaoLibiaWork.commit()
    print(f"[{datetime.now().strftime('%d/%m/%Y %H:%M')}] (Fim) Colocando os dados na tabela TB_TEMPO_CUIDAR_HISTORICO_CONTATO")

    conexaoLibiaWork.commit   
    print(f"[{datetime.now().strftime('%d/%m/%Y %H:%M')}] (Fim) Atuando campo ROTINA - TB_TEMPO_CUIDAR_HISTORICO_CONTATO")                  

try:  
    ApagarDados()
    CargaDados() 
except Exception as e:
    print(f"Ocorreu um erro: {e}")
finally:
    conexaoLibiaWork.close()
    conexaoProducao.close()
    print('Conexões Fechadas')     