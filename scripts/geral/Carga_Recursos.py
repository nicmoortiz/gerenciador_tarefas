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
    ApagarDados("TB_RECURSOS",conexaoMRA)    
    logger.info(f"--> FINALIZOU ROTINA ApagarDados.")  
    logger.info(f"--> INICIOU ROTINA DE CARGA - TB_RECURSOS.")
    #Para atender aos relatorios tempo de cuidar que serao criados só preciso do ano de 2026.    
    comando = f'''
                            SELECT 
                                EXAME.ID_EXAME						CODIGO_RECURSO,
                                'E'									TIPO_RECURSO,
                                EXAME.NOME_EXAME					NOME_RECURSO,
                                GRUPO.ID_GRUPO						CODIGO_GRUPO,
                                UPPER(GRUPO.NOME_GRUPO)				NOME_GRUPO,
                                SUB_GRUPO.ID_SUBGRUPO				CODIGO_SUBGRUPO,
                                UPPER(SUB_GRUPO.NOME_SUBGRUPO)		NOME_SUBGRUPO,
                                UPPER(CASE 
                                    WHEN EXAME.TIPO = 'E' AND GRUPO.ID_GRUPO IN (201, 204, 205, 206, 207, 208, 209, 210, 211)								THEN 'Procedimentos Diagnósticos'
                                    WHEN EXAME.TIPO = 'E' AND GRUPO.ID_GRUPO NOT IN (201, 204, 205, 206, 207, 208, 209, 210, 211)							THEN 'Outros Exames'
                                    WHEN EXAME.TIPO = 'P' AND GRUPO.ID_GRUPO IN (401,402,403,404,405,406,407,408,409,410,411,412,413,414,415,416,418)		THEN 'Procedimentos Cirúrgicos SIGTAP'
                                    WHEN EXAME.TIPO = 'P' AND GRUPO.ID_GRUPO NOT IN (401,402,403,404,405,406,407,408,409,410,411,412,413,414,415,416,418)	THEN 'Outros Procedimentos'
                                END)								CLASSIFICACAO,
                                UPPER(CASE 
                                    WHEN EXAME.TIPO = 'E'																									THEN 'Exame'
                                    WHEN EXAME.TIPO = 'P'																									THEN 'Procedimento'
                                END)								TIPO_FILA,
                                EXAME.FLG_ATIVO						RECURSO_ATIVO
                            FROM AMB_EXAME1 EXAME
                            LEFT JOIN AMB_SUBGRUPO		SUB_GRUPO	  ON (SUB_GRUPO.ID_SUBGRUPO			= EXAME.ID_SUBGRUPO		AND SUB_GRUPO.TIPO_SUBGRUPO		= 'E')
                            LEFT JOIN AMB_GRUPO			GRUPO		  ON (GRUPO.ID_GRUPO				= SUB_GRUPO.ID_GRUPO	AND GRUPO.TIPO_GRUPO		= 'E')

                            UNION ALL

                            SELECT 
                                ESPECIALIDADE.ID_ESPECIALIDADE					CODIGO_RECURSO,
                                'C'												TIPO_RECURSO,
                                UPPER(ESPECIALIDADE.NOME_ESPECIALIDADE)			NOME_RECURSO,
                                GRUPO.ID_GRUPO									CODIGO_GRUPO,
                                UPPER(GRUPO.NOME_GRUPO)							NOME_GRUPO,
                                SUB_GRUPO.ID_SUBGRUPO							CODIGO_SUBGRUPO,
                                UPPER(SUB_GRUPO.NOME_SUBGRUPO)					NOME_SUBGRUPO,
                                UPPER(CASE 
                                        WHEN GRUPO.ID_GRUPO = 3 AND ESPECIALIDADE.ID_ESPECIALIDADE     IN (1087,1089,1091,1093,1095,1341,1358,1359,1360,1361,1362,1363,1364,1365,1366,1367,1369,1370,1371,1374,1375,1376,1377,1378,1449,1459,1460,1522,1528,1540,1573,1574,1589,1597,1598,1599,1617,1647,1653,1708,1767,1769,1770,1771,1773,1774,1775,1778,1787,1790)	THEN 'Avaliação Cirurgia Eletiva'
                                        WHEN GRUPO.ID_GRUPO = 3 AND ESPECIALIDADE.ID_ESPECIALIDADE NOT IN (1087,1089,1091,1093,1095,1341,1358,1359,1360,1361,1362,1363,1364,1365,1366,1367,1369,1370,1371,1374,1375,1376,1377,1378,1449,1459,1460,1522,1528,1540,1573,1574,1589,1597,1598,1599,1617,1647,1653,1708,1767,1769,1770,1771,1773,1774,1775,1778,1787,1790)	THEN 'Consultas Médicas em Especialidades'
                                        WHEN GRUPO.ID_GRUPO = 4 THEN 'Consultas Profissionais Nível Superior'
                                END)											CLASSIFICACAO,
                                UPPER(CASE 
                                            WHEN GRUPO.ID_GRUPO = 3 THEN 'Consultas Médicas'
                                            WHEN GRUPO.ID_GRUPO = 4 THEN 'Consultas Profissionais'
                                END)											TIPO_FILA,
                                ESPECIALIDADE.FLG_ATIVO							RECURSO_ATIVO
                            FROM 
                                AMB_ESPECIALIDADE		ESPECIALIDADE
                            LEFT JOIN AMB_SUBGRUPO		SUB_GRUPO	  ON (SUB_GRUPO.ID_SUBGRUPO			= ESPECIALIDADE.ID_SUBGRUPO		AND SUB_GRUPO.TIPO_SUBGRUPO		= 'C')
                            LEFT JOIN AMB_GRUPO			GRUPO		  ON (GRUPO.ID_GRUPO				= SUB_GRUPO.ID_GRUPO			AND GRUPO.TIPO_GRUPO			= 'C')
               '''    
    dfSOLICITACAO = ExtrairDados(conexaoProducao,comando)
    IncluirDados(dfSOLICITACAO,"TB_RECURSOS",conexaoMRA)    
    logger.info(f"--> FINALIZOU ROTINA DE CARGA - TB_RECURSOS.")      