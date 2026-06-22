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
if __name__ == "__main__":

    logger.info(f"--> INICIOU ROTINA ApagarDados.")
    ApagarDados("TB_UNIDADES",conexaoMRA)    
    logger.info(f"--> FINALIZOU ROTINA ApagarDados.")  
    logger.info(f"--> INICIOU ROTINA DE CARGA - TB_UNIDADES.")
    #Para atender aos relatorios tempo de cuidar que serao criados só preciso do ano de 2026.    
    comando = f'''
                SELECT 
                    UNIDADE.COD_UNIDADE					CODIGO_UNIDADE,
                    UNIDADE.CNES						CNES_UNIDADE,
                    UNIDADE.UNIDADE_FANTASIA			NOME_UNIDADE,
                    UNIDADE.SIGLA_GESTAO				GESTAO_UNIDADE,
                    UPPER(UNIDADE.MUNICIPIO)			MUNICIPIO_UNIDADE,
                    UNIDADE.CODMUNGEST					IBGE_UNIDADE,
                    UNIDADE.COD_DRS						CODIGO_DRS,
                    DRS.NOME_DRS						NOME_DRS,
                    DRS.SIGLA_DRS						SIGLA_DRS,
                    RRAS.COD_RRAS						SIGLA_RRAS,
                    UNIDADE.COD_CGR						CODIGO_REGIAO_SAUDE,                    
                    REPLACE(CIR.CIR	, 'REGIAO DE SAUDE - ', '') NOME_REGIAO_SAUDE
                FROM 
                    ADMAMB_ADM_UNIDADE				UNIDADE
                LEFT JOIN AMB_DRS					DRS				ON DRS.COD_DRS				= UNIDADE.COD_DRS
                LEFT JOIN AMB_RRAS_MUNGEST			RRAS			ON UNIDADE.CODMUNGEST		= RRAS.CODMUNGEST
                LEFT JOIN ADMAMB_ADM_UNIDADE_CIR	CIR				ON CIR.COD_UNIDADE			= UNIDADE.COD_UNIDADE  
               '''    
    dfSOLICITACAO = ExtrairDados(conexaoProducao,comando)
    IncluirDados(dfSOLICITACAO,"TB_UNIDADES",conexaoMRA)    
    logger.info(f"--> FINALIZOU ROTINA DE CARGA - TB_UNIDADES.")      