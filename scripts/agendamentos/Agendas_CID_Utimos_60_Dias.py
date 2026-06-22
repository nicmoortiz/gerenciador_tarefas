from dotenv import load_dotenv
import os
import urllib
from datetime import datetime
import pandas as pd
from sqlalchemy import create_engine, text
import logging
import os
import sys
############################################################################################################################################ 
CAMINHO_ENV = r"C:\Configs\Variaveis\.env"
CAMINHO_LOG = r"C:\Configs\Logs"
nome_script = os.path.splitext(os.path.basename(sys.argv[0]))[0]
ARQUIVO_LOG = f"log_{nome_script}.txt"
############################################################################################################################################ 
os.makedirs(CAMINHO_LOG, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(CAMINHO_LOG, ARQUIVO_LOG),
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%d/%m/%Y %H:%M:%S"
)
logger = logging.getLogger(__name__)
load_dotenv(CAMINHO_ENV)
############################################################################################################################################ 
### Produção ###
############################################################################################################################################ 
servidorDUO 			= os.getenv("servidorProducao")
bancoDUO    			= os.getenv("bancoProducao")
usuarioDUO  			= os.getenv("usuarioProducao")
senhaDUO    			= os.getenv("senhaProducao")
parametros_bdProducao 	= ("DRIVER={" + "ODBC Driver 17 for SQL Server" + "};SERVER=" + servidorDUO + ";DATABASE=" + bancoDUO+ ";UID=" + usuarioDUO + ";PWD=" + senhaDUO)        
mecanismoProducao 		= create_engine("mssql+pyodbc:///?odbc_connect=%s" % urllib.parse.quote_plus(parametros_bdProducao)) 
conexaoProducao 		= mecanismoProducao.connect()
############################################################################################################################################ 
### Desenvolvimento ###
############################################################################################################################################ 
servidorMRA 	= os.getenv("servidorMRA")
bancoMRA    	= os.getenv("bancoMRA")
usuarioMRA  	= os.getenv("usuarioMRA")
senhaMRA    	= os.getenv("senhaMRA")
parametrosMRA	= ("DRIVER={" + "ODBC Driver 17 for SQL Server" + "};SERVER=" + servidorMRA + ";DATABASE=" + bancoMRA  + ";UID=" + usuarioMRA  + ";PWD=" + senhaMRA)        
mecanismoMRA  	= create_engine("mssql+pyodbc:///?odbc_connect=%s" % urllib.parse.quote_plus(parametrosMRA)) 
conexaoMRA   	= mecanismoMRA.connect() 
############################################################################################################################################ 
def IncluirDados(dataframe,tabela,conexao):
    try:
        logger.info(f"Iniciou o processo de inclusão dos registros na tabela {tabela}.")
        dataframe.to_sql(name=tabela, con=conexao, if_exists='append', index=False, chunksize =1000) 
        logger.info(f"Finalizou o processo de inclusão dos registros na tabela {tabela}.")
    except Exception as e:
        logger.exception(f"Erro no processo de inclusão dos registros na tabela {tabela}. ")
        raise
############################################################################################################################################
def ApagarDados(tabela, conexao, condicao=""):
    try:
        logger.info(f"Iniciou o processo de exclusão dos registros na tabela {tabela}.")
        sql = f"DELETE FROM {tabela}"
        if condicao.strip():
            sql += f" WHERE {condicao}"
        with conexao.begin():
            conexao.execute(text(sql))
        logger.info(f"Finalizou o processo de exclusão dos registros na tabela {tabela}.")        
    except Exception:
        logger.exception(f"Erro no processo de extração dos dados.")
        raise      
############################################################################################################################################    
def ExtrairDados(conexao, comando):
    try:
        logger.info(f"Iniciou o processo de extração dos dados.")
        dfExtracao = pd.read_sql_query(comando, conexao)
        logger.info(f"Finalizou o processo de extração dos dados. Total de registros extraídos: {len(dfExtracao)}.")
        return dfExtracao        
    except Exception:
        logger.exception(f"Erro no processo de extração dos dados.")
        raise
############################################################################################################################################
def AtualizarDados(comando, conexao):
    try:
        comando_exec = text(comando) if isinstance(comando, str) else comando
        result = conexao.execute(comando_exec)
        conexao.commit()
        logger.info(f"Atualizado os dados - Número de Registros = {result.rowcount}")
    except Exception:
        conexao.rollback()
        logger.exception("Erro ao atualizar dados.")
        raise
############################################################################################################################################
if __name__ == "__main__":

    logger.info(f"--> INICIOU ROTINA ApagarDados.")
    ApagarDados("TB_AGENDA_CID",conexaoMRA)    
    logger.info(f"--> FINALIZOU ROTINA ApagarDados.") 

    logger.info(f"--> INICIOU ROTINA ExtrairDados")  
    comandoSQL = text("""
                SELECT	DISTINCT
                        MONTH(HORARIO.DATA_AGENDA)							MES,
                        PROFISSIONAL.NOME_PROFISSIONAL,
                        ESPECIALIDADE.ID_ESPECIALIDADE						CODIGO_RECURSO,
                        UPPER(ESPECIALIDADE.NOME_ESPECIALIDADE)				NOME_RECURSO,
                        PROTOCOLO.SUBCATEG									CID,
                        UNIDADE_EXECUTANTE.COD_UNIDADE						CODIGO_EXECUTANTE,
                        UNIDADE_EXECUTANTE.UNIDADE_FANTASIA					UNIDADE_EXECUTANTE,
                        (CASE
                            WHEN UNIDADE_EXECUTANTE.SIGLA_GESTAO = 'EST' THEN 'ESTADUAL'
                            WHEN UNIDADE_EXECUTANTE.SIGLA_GESTAO = 'MUN' THEN 'MUNICIPAL'
                        END) TIPO_GESTAO,
                        DRS_EXECUTANTE.NOME_DRS,
                        DRS_EXECUTANTE.SIGLA_DRS,
                        AGENDA.SEXO,
                        AGENDA.IDADE_INI,
                        AGENDA.IDADE_FIM
                FROM 
                        AMB_AGE_CONSULTA_HOR  		HORARIO
                LEFT JOIN AMB_AGE_CONSULTA		AGENDA					ON AGENDA.ID_AGE_CONSULTA 					= HORARIO.ID_AGE_CONSULTA
                LEFT JOIN ADMAMB_ADM_UNIDADE		UNIDADE_EXECUTANTE		ON UNIDADE_EXECUTANTE.COD_UNIDADE			= HORARIO.COD_UNIDADE_EXECUTANTE
                LEFT JOIN AMB_DRS					DRS_EXECUTANTE			ON	DRS_EXECUTANTE.COD_DRS				=	UNIDADE_EXECUTANTE.COD_DRS                    
                LEFT JOIN AMB_ESPECIALIDADE			ESPECIALIDADE			ON ESPECIALIDADE.ID_ESPECIALIDADE			= HORARIO.ID_ESPECIALIDADE
                LEFT JOIN SES_PROFISSIONAL			PROFISSIONAL			ON PROFISSIONAL.ID_PROFISSIONAL			= AGENDA.ID_PROFISSIONAL
                INNER JOIN AMB_PROTOCOLO			PROTOCOLO				ON PROTOCOLO.ID_PROTOCOLO					= HORARIO.ID_PROTOCOLO
                WHERE HORARIO.DATA_AGENDA >= CAST(GETDATE() AS DATE)  AND HORARIO.DATA_AGENDA < DATEADD(DAY, 60, CAST(GETDATE() AS DATE))                            
        """)
    dfExtracao = ExtrairDados(conexaoProducao,comandoSQL)
    IncluirDados(dfExtracao,"TB_AGENDA_CID",conexaoMRA)    
    logger.info(f"--> FINALIZOU ROTINA ExtrairDados.")   