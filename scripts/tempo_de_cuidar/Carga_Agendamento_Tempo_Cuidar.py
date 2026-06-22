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
        qtd_registros = len(dataframe)
        logger.info(f"Iniciou o processo de inclusão dos registros na tabela {tabela}. Quantidade de Registros inclusos:{qtd_registros}")
        dataframe.to_sql(name=tabela, con=conexao, if_exists='append', index=False, chunksize =1000) 
        logger.info(f"Finalizou o processo de inclusão dos registros na tabela {tabela}.")
        conexao.commit()
    except Exception as e:
        logger.exception(f"Erro no processo de inclusão dos registros na tabela {tabela}. ")
        raise
############################################################################################################################################ 
def IncluirDados_chat(dataframe, tabela, conexao, schema="dbo"):
    qtd_registros = len(dataframe)
    logger.info(f"[{tabela}] Linhas no DF: {qtd_registros}")

    if qtd_registros == 0:
        logger.warning(f"[{tabela}] DF vazio. Nada a inserir.")
        return

    dataframe.to_sql(
        name=tabela,
        con=conexao,
        schema=schema,
        if_exists='append',
        index=False,
        chunksize=1000,
        method="multi"
    )

    # Confirma na MESMA conexão (sem depender de commit visível em outra sessão)
    try:
        total = conexao.execute(text(f"SELECT COUNT(1) FROM {schema}.{tabela}")).scalar()
        logger.info(f"[{tabela}] COUNT após insert (mesma conexão): {total}")
    except Exception:
        logger.exception(f"[{tabela}] Falha ao validar COUNT pós-insert")
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
def QueryAgendamento(codigos_str):
    return text(f"""
                   WITH DADOS AS ( SELECT
                        'CONSULTA' TIPO,
                        'LOG' FONTE,
                        (CASE
                            WHEN AGENDAMENTO.COD_PACIENTE = HORARIO.COD_PACIENTE THEN 'HISTORICO'
                            ELSE NULL
                        END) ABA,	
                        AGENDAMENTO.TIPO_LOG						TIPO_LOG,
                        AGENDAMENTO.ID_MOTIVO						CODIGO_MOTIVO,
                        AGENDAMENTO.COD_PACIENTE,	
                        AGENDAMENTO.ID_AGE_CONSULTA					CODIGO_AGENDA,
                        AGENDAMENTO.ID_AGE_CONSULTA_HOR				CODIGO_HORARIO,
                        AGENDAMENTO.COD_UNIDADE_EXECUTANTE			CODIGO_EXECUTANTE,
                        UNIDADE_EXECUTANTE.UNIDADE_FANTASIA			UNIDADE_EXECUTANTE,
                        AGENDAMENTO.DATA_AGENDA						DATA_AGENDA,
                        AGENDAMENTO.HOR_INI							HORARIO,
                        AGENDAMENTO.ID_PROFISSIONAL					CODIGO_PROFISSIONAL,
                        PROFISSIONAL.NOME_PROFISSIONAL				NOME_PROFISSIONAL,
                        ESPECIALIDADE.ID_ESPECIALIDADE				CODIGO_RECURSO,
                        UPPER(ESPECIALIDADE.NOME_ESPECIALIDADE)		NOME_RECURSO,
                        SUB_GRUPO.ID_SUBGRUPO						CODIGO_SUBGRUPO,
                        UPPER(SUB_GRUPO.NOME_SUBGRUPO)				NOME_SUBGRUPO,
                        GRUPO.ID_GRUPO								CODIGO_GRUPO,
                        UPPER(GRUPO.NOME_GRUPO)						NOME_GRUPO,
                        PROTOCOLO.SUBCATEG							CID,
                        HORARIO.STATUS								STATUS_AGENDA,     
                        AGENDAMENTO.COD_UNIDADE_SOLICITANTE			CODIGO_SOLICITANTE,
                        UNIDADE_SOLICITANTE.UNIDADE_FANTASIA		UNIDADE_SOLICITANTE,  
                        AGENDAMENTO.DT_ULTIMA_ATUALIZ               DATA_AGENDAMENTO,                 
                        AGENDAMENTO.DATA_ACAO						DATA_ACAO,
                        --ROW_NUMBER() OVER(PARTITION BY AGENDAMENTO.ID_AGE_CONSULTA_HOR ORDER BY AGENDAMENTO.ID_LOG_CONSULTA DESC) LINHA,
                        AGENDAMENTO.ID_FILA							CODIGO_FILA
                    FROM 
                        AMB_LOG_CONSULTA AGENDAMENTO
                    LEFT JOIN AMB_PROTOCOLO			PROTOCOLO				ON PROTOCOLO.ID_PROTOCOLO				= AGENDAMENTO.ID_PROTOCOLO
                    LEFT JOIN AMB_AGE_CONSULTA_HOR	HORARIO					ON HORARIO.ID_AGE_CONSULTA_HOR			= AGENDAMENTO.ID_AGE_CONSULTA_HOR
                    LEFT JOIN SES_PROFISSIONAL		PROFISSIONAL			ON PROFISSIONAL.ID_PROFISSIONAL			= AGENDAMENTO.ID_PROFISSIONAL
                    LEFT JOIN ADMAMB_ADM_UNIDADE	UNIDADE_EXECUTANTE		ON UNIDADE_EXECUTANTE.COD_UNIDADE		= AGENDAMENTO.COD_UNIDADE_EXECUTANTE
                    LEFT JOIN ADMAMB_ADM_UNIDADE	UNIDADE_SOLICITANTE		ON UNIDADE_SOLICITANTE.COD_UNIDADE		= AGENDAMENTO.COD_UNIDADE_SOLICITANTE                
                    LEFT JOIN AMB_ESPECIALIDADE		ESPECIALIDADE			ON ESPECIALIDADE.ID_ESPECIALIDADE		= AGENDAMENTO.ID_ESPECIALIDADE
                    LEFT JOIN Amb_subgrupo		    SUB_GRUPO				ON SUB_GRUPO.ID_SUBGRUPO				= ESPECIALIDADE.ID_SUBGRUPO
                    LEFT JOIN amb_grupo				GRUPO					ON GRUPO.ID_GRUPO						= SUB_GRUPO.ID_GRUPO
                    WHERE AGENDAMENTO.COD_PACIENTE IN ({codigos_str})
                    AND   HORARIO.DATA_AGENDA > '2025-07-28'

                    UNION ALL

                    SELECT 
                        'CONSULTA' TIPO,
                        'AGENDA' FONTE,
                        'HISTORICO'									ABA,
                        'X'											TIPO_LOG,
                        NULL										CODIGO_MOTIVO,
                        HORARIO.COD_PACIENTE,
                        HORARIO.ID_AGE_CONSULTA						CODIGO_AGENDA,
                        HORARIO.ID_AGE_CONSULTA_HOR					CODIGO_HORARIO,
                        HORARIO.COD_UNIDADE_EXECUTANTE				CODIGO_EXECUTANTE,
                        UNIDADE_EXECUTANTE.UNIDADE_FANTASIA			UNIDADE_EXECUTANTE,
                        HORARIO.DATA_AGENDA							DATA_AGENDA,
                        HORARIO.HOR_INI								HORARIO,
                        HORARIO.ID_PROFISSIONAL						CODIGO_PROFISSIONAL,
                        PROFISSIONAL.NOME_PROFISSIONAL				NOME_PROFISSIONAL,
                        ESPECIALIDADE.ID_ESPECIALIDADE				CODIGO_RECURSO,
                        UPPER(ESPECIALIDADE.NOME_ESPECIALIDADE)		NOME_RECURSO,
                        SUB_GRUPO.ID_SUBGRUPO						CODIGO_SUBGRUPO,
                        UPPER(SUB_GRUPO	.NOME_SUBGRUPO)				NOME_SUBGRUPO,
                        GRUPO.ID_GRUPO								CODIGO_GRUPO,
                        UPPER(GRUPO.NOME_GRUPO)						NOME_GRUPO,
                        PROTOCOLO.SUBCATEG							CID,
                        HORARIO.STATUS								STATUS_AGENDA,  
                        HORARIO.COD_UNIDADE_SOLICITANTE				CODIGO_SOLICITANTE,
                        UNIDADE_SOLICITANTE.UNIDADE_FANTASIA		UNIDADE_SOLICITANTE, 
                        HORARIO.DT_ULTIMA_ATUALIZ                   DATA_AGENDAMENTO,      
                        HORARIO.DT_ULTIMA_ATUALIZ                   DATA_ACAO,      
                        --1                                           LINHA,
                        NULL						                CODIGO_FILA
                    FROM 
                        AMB_AGE_CONSULTA_HOR HORARIO 
                    LEFT JOIN AMB_PROTOCOLO			PROTOCOLO				ON PROTOCOLO.ID_PROTOCOLO				= HORARIO.ID_PROTOCOLO
                    LEFT JOIN SES_PROFISSIONAL		PROFISSIONAL			ON PROFISSIONAL.ID_PROFISSIONAL			= HORARIO.ID_PROFISSIONAL
                    LEFT JOIN ADMAMB_ADM_UNIDADE	UNIDADE_EXECUTANTE		ON UNIDADE_EXECUTANTE.COD_UNIDADE		= HORARIO.COD_UNIDADE_EXECUTANTE
                    LEFT JOIN ADMAMB_ADM_UNIDADE	UNIDADE_SOLICITANTE		ON UNIDADE_SOLICITANTE.COD_UNIDADE		= HORARIO.COD_UNIDADE_SOLICITANTE
                    LEFT JOIN AMB_ESPECIALIDADE		ESPECIALIDADE			ON ESPECIALIDADE.ID_ESPECIALIDADE		= HORARIO.ID_ESPECIALIDADE
                    LEFT JOIN Amb_subgrupo		    SUB_GRUPO				ON SUB_GRUPO.ID_SUBGRUPO				= ESPECIALIDADE.ID_SUBGRUPO
                    LEFT JOIN amb_grupo				GRUPO					ON GRUPO.ID_GRUPO						= SUB_GRUPO.ID_GRUPO
                    WHERE HORARIO.COD_PACIENTE IN ({codigos_str})
                    AND   HORARIO.DATA_AGENDA > '2025-07-28'

                    UNION ALL


                    SELECT
                        'EXAME' TIPO,
                        'LOG' FONTE,
                        (CASE
                            WHEN AGENDAMENTO.COD_PACIENTE = HORARIO.COD_PACIENTE THEN 'HISTORICO'
                            ELSE NULL
                        END) ABA,	
                        AGENDAMENTO.TIPO_LOG						TIPO_LOG,
                        AGENDAMENTO.ID_MOTIVO						CODIGO_MOTIVO,
                        AGENDAMENTO.COD_PACIENTE,	
                        AGENDAMENTO.ID_AGE_EXAME					CODIGO_AGENDA,
                        AGENDAMENTO.ID_AGE_EXAME_HOR				CODIGO_HORARIO,
                        AGENDAMENTO.COD_UNIDADE_EXECUTANTE			CODIGO_EXECUTANTE,
                        UNIDADE_EXECUTANTE.UNIDADE_FANTASIA			UNIDADE_EXECUTANTE,
                        AGENDAMENTO.DATA_AGENDA						DATA_AGENDA,
                        AGENDAMENTO.HOR_INI							HORARIO,
                        NULL										CODIGO_PROFISSIONAL,
                        NULL										NOME_PROFISSIONAL,
                        EXAME.ID_EXAME								CODIGO_RECURSO,
                        UPPER(EXAME.NOME_EXAME)						NOME_RECURSO,
                        SUB_GRUPO.ID_SUBGRUPO						CODIGO_SUBGRUPO,
                        UPPER(SUB_GRUPO.NOME_SUBGRUPO)				NOME_SUBGRUPO,
                        GRUPO.ID_GRUPO								CODIGO_GRUPO,
                        UPPER(GRUPO.NOME_GRUPO)						NOME_GRUPO,
                        NULL										CID,
                        HORARIO.STATUS								STATUS_AGENDA,  
                        AGENDAMENTO.COD_UNIDADE_SOLICITANTE			CODIGO_SOLICITANTE,
                        UNIDADE_SOLICITANTE.UNIDADE_FANTASIA		UNIDADE_SOLICITANTE,  
                        AGENDAMENTO.DT_ULTIMA_ATUALIZ               DATA_AGENDAMENTO,                    
                        AGENDAMENTO.DATA_ACAO						DATA_ACAO,
                        --ROW_NUMBER() OVER(PARTITION BY AGENDAMENTO.ID_AGE_EXAME_HOR ORDER BY AGENDAMENTO.ID_LOG_EXAME DESC) LINHA,
                        AGENDAMENTO.ID_FILA							CODIGO_FILA
                    FROM 
                        AMB_LOG_EXAME AGENDAMENTO
                    LEFT JOIN AMB_AGE_EXAME_HOR		HORARIO					ON HORARIO.ID_AGE_EXAME_HOR				= AGENDAMENTO.ID_AGE_EXAME_HOR
                    LEFT JOIN ADMAMB_ADM_UNIDADE	UNIDADE_EXECUTANTE		ON UNIDADE_EXECUTANTE.COD_UNIDADE		= AGENDAMENTO.COD_UNIDADE_EXECUTANTE
                    LEFT JOIN ADMAMB_ADM_UNIDADE	UNIDADE_SOLICITANTE		ON UNIDADE_SOLICITANTE.COD_UNIDADE		= AGENDAMENTO.COD_UNIDADE_SOLICITANTE
                    LEFT JOIN AMB_EXAME1			EXAME					ON EXAME.ID_EXAME						= HORARIO.ID_EXAME
                    LEFT JOIN Amb_subgrupo		    SUB_GRUPO				ON SUB_GRUPO.ID_SUBGRUPO				= EXAME.ID_SUBGRUPO
                    LEFT JOIN amb_grupo				GRUPO					ON GRUPO.ID_GRUPO						= SUB_GRUPO.ID_GRUPO
                    WHERE AGENDAMENTO.COD_PACIENTE IN ({codigos_str})
                    AND   HORARIO.DATA_AGENDA > '2025-07-28'

                    UNION ALL
                    SELECT 
                        'EXAME' TIPO,
                        'AGENDA' FONTE,
                        'HISTORICO'									ABA,
                        'X'											TIPO_LOG,
                        NULL										CODIGO_MOTIVO,
                        HORARIO.COD_PACIENTE,
                        HORARIO.ID_AGE_EXAME						CODIGO_AGENDA,
                        HORARIO.ID_AGE_EXAME_HOR					CODIGO_HORARIO,
                        HORARIO.COD_UNIDADE_EXECUTANTE				CODIGO_EXECUTANTE,
                        UNIDADE_EXECUTANTE.UNIDADE_FANTASIA			UNIDADE_EXECUTANTE,
                        HORARIO.DATA_AGENDA							DATA_AGENDA,
                        HORARIO.HOR_INI								HORARIO,
                        NULL										CODIGO_PROFISSIONAL,
                        NULL										NOME_PROFISSIONAL,
                        EXAME.ID_EXAME								CODIGO_RECURSO,
                        UPPER(EXAME.NOME_EXAME)						NOME_RECURSO,
                        SUB_GRUPO.ID_SUBGRUPO						CODIGO_SUBGRUPO,
                        UPPER(SUB_GRUPO	.NOME_SUBGRUPO)				NOME_SUBGRUPO,
                        GRUPO.ID_GRUPO								CODIGO_GRUPO,
                        UPPER(GRUPO.NOME_GRUPO)						NOME_GRUPO,
                        NULL										CID,
                        HORARIO.STATUS								STATUS_AGENDA,    
                        HORARIO.COD_UNIDADE_SOLICITANTE				CODIGO_SOLICITANTE,    
                        UNIDADE_SOLICITANTE.UNIDADE_FANTASIA		UNIDADE_SOLICITANTE,     
                        HORARIO.DT_ULTIMA_ATUALIZ                   DATA_AGENDAMENTO,    
                        HORARIO.DT_ULTIMA_ATUALIZ					DATA_ACAO,	
                        --1                                           LINHA	,
                        NULL                                        CODIGO_FILA
                    FROM 
                        AMB_AGE_EXAME_HOR HORARIO 
                    LEFT JOIN ADMAMB_ADM_UNIDADE	UNIDADE_EXECUTANTE		ON UNIDADE_EXECUTANTE.COD_UNIDADE		= HORARIO.COD_UNIDADE_EXECUTANTE
                    LEFT JOIN ADMAMB_ADM_UNIDADE	UNIDADE_SOLICITANTE		ON UNIDADE_SOLICITANTE.COD_UNIDADE		= HORARIO.COD_UNIDADE_SOLICITANTE
                    LEFT JOIN AMB_EXAME1			EXAME					ON EXAME.ID_EXAME						= HORARIO.ID_EXAME
                    LEFT JOIN Amb_subgrupo		    SUB_GRUPO				ON SUB_GRUPO.ID_SUBGRUPO				= EXAME.ID_SUBGRUPO
                    LEFT JOIN amb_grupo				GRUPO					ON GRUPO.ID_GRUPO						= SUB_GRUPO.ID_GRUPO
                    WHERE HORARIO.COD_PACIENTE IN ({codigos_str})
                    AND   HORARIO.DATA_AGENDA > '2025-07-28'),
                    ORDENADO AS (SELECT
                                    ROW_NUMBER() OVER(PARTITION BY TIPO,COD_PACIENTE,NOME_RECURSO ORDER BY DATA_AGENDA,  CODIGO_FILA DESC) LINHA,
                                    DADOS.*
                                FROM 
                                    DADOS),                    
                    
                    RELATORIO AS(SELECT 
                                    ORDENADO.*
                                FROM 
                                    ORDENADO
                                where ORDENADO.LINHA = 1)

                    SELECT 
                        TIPO	,
                        ABA	,
                        TIPO_LOG	,
                        CODIGO_MOTIVO	,
                        COD_PACIENTE	,
                        CODIGO_AGENDA	,
                        CODIGO_HORARIO	,
                        CODIGO_EXECUTANTE	,
                        UNIDADE_EXECUTANTE	,
                        DATA_AGENDA	,
                        HORARIO	,
                        CODIGO_PROFISSIONAL	,
                        NOME_PROFISSIONAL	,
                        CODIGO_RECURSO	,
                        NOME_RECURSO	,
                        CODIGO_SUBGRUPO	,
                        NOME_SUBGRUPO	,
                        CODIGO_GRUPO	,
                        NOME_GRUPO	,
                        CID	,
                        STATUS_AGENDA	,
                        CODIGO_SOLICITANTE	,
                        UNIDADE_SOLICITANTE	,
                        DATA_AGENDAMENTO	,
                        LINHA	,
                        NULL ORDEM	,
                        DATA_AGENDAMENTO DATA_ATUALIZACAO	,
                        DATA_ACAO	,
                        CODIGO_FILA	
                    FROM 
                        RELATORIO 
                    ORDER BY TIPO, ABA, DATA_AGENDA DESC                       
            """)
############################################################################################################################################
def QueryAgendamentoCompleta(codigos_str):
    return text(f"""
                   WITH DADOS AS ( SELECT
                        'CONSULTA' TIPO,
                        'LOG' FONTE,
                        (CASE
                            WHEN AGENDAMENTO.COD_PACIENTE = HORARIO.COD_PACIENTE THEN 'HISTORICO'
                            ELSE NULL
                        END) ABA,	
                        AGENDAMENTO.TIPO_LOG						TIPO_LOG,
                        AGENDAMENTO.ID_MOTIVO						CODIGO_MOTIVO,
                        AGENDAMENTO.COD_PACIENTE,	
                        AGENDAMENTO.ID_AGE_CONSULTA					CODIGO_AGENDA,
                        AGENDAMENTO.ID_AGE_CONSULTA_HOR				CODIGO_HORARIO,
                        AGENDAMENTO.COD_UNIDADE_EXECUTANTE			CODIGO_EXECUTANTE,
                        UNIDADE_EXECUTANTE.UNIDADE_FANTASIA			UNIDADE_EXECUTANTE,
                        AGENDAMENTO.DATA_AGENDA						DATA_AGENDA,
                        AGENDAMENTO.HOR_INI							HORARIO,
                        AGENDAMENTO.ID_PROFISSIONAL					CODIGO_PROFISSIONAL,
                        PROFISSIONAL.NOME_PROFISSIONAL				NOME_PROFISSIONAL,
                        ESPECIALIDADE.ID_ESPECIALIDADE				CODIGO_RECURSO,
                        UPPER(ESPECIALIDADE.NOME_ESPECIALIDADE)		NOME_RECURSO,
                        SUB_GRUPO.ID_SUBGRUPO						CODIGO_SUBGRUPO,
                        UPPER(SUB_GRUPO.NOME_SUBGRUPO)				NOME_SUBGRUPO,
                        GRUPO.ID_GRUPO								CODIGO_GRUPO,
                        UPPER(GRUPO.NOME_GRUPO)						NOME_GRUPO,
                        PROTOCOLO.SUBCATEG							CID,
                        HORARIO.STATUS								STATUS_AGENDA,     
                        AGENDAMENTO.COD_UNIDADE_SOLICITANTE			CODIGO_SOLICITANTE,
                        UNIDADE_SOLICITANTE.UNIDADE_FANTASIA		UNIDADE_SOLICITANTE,  
                        AGENDAMENTO.DT_ULTIMA_ATUALIZ               DATA_AGENDAMENTO,                 
                        AGENDAMENTO.DATA_ACAO						DATA_ACAO,
                        --ROW_NUMBER() OVER(PARTITION BY AGENDAMENTO.ID_AGE_CONSULTA_HOR ORDER BY AGENDAMENTO.ID_LOG_CONSULTA DESC) LINHA,
                        AGENDAMENTO.ID_FILA							CODIGO_FILA
                    FROM 
                        AMB_LOG_CONSULTA AGENDAMENTO
                    LEFT JOIN AMB_PROTOCOLO			PROTOCOLO				ON PROTOCOLO.ID_PROTOCOLO				= AGENDAMENTO.ID_PROTOCOLO
                    LEFT JOIN AMB_AGE_CONSULTA_HOR	HORARIO					ON HORARIO.ID_AGE_CONSULTA_HOR			= AGENDAMENTO.ID_AGE_CONSULTA_HOR
                    LEFT JOIN SES_PROFISSIONAL		PROFISSIONAL			ON PROFISSIONAL.ID_PROFISSIONAL			= AGENDAMENTO.ID_PROFISSIONAL
                    LEFT JOIN ADMAMB_ADM_UNIDADE	UNIDADE_EXECUTANTE		ON UNIDADE_EXECUTANTE.COD_UNIDADE		= AGENDAMENTO.COD_UNIDADE_EXECUTANTE
                    LEFT JOIN ADMAMB_ADM_UNIDADE	UNIDADE_SOLICITANTE		ON UNIDADE_SOLICITANTE.COD_UNIDADE		= AGENDAMENTO.COD_UNIDADE_SOLICITANTE                
                    LEFT JOIN AMB_ESPECIALIDADE		ESPECIALIDADE			ON ESPECIALIDADE.ID_ESPECIALIDADE		= AGENDAMENTO.ID_ESPECIALIDADE
                    LEFT JOIN Amb_subgrupo		    SUB_GRUPO				ON SUB_GRUPO.ID_SUBGRUPO				= ESPECIALIDADE.ID_SUBGRUPO
                    LEFT JOIN amb_grupo				GRUPO					ON GRUPO.ID_GRUPO						= SUB_GRUPO.ID_GRUPO
                    WHERE AGENDAMENTO.COD_PACIENTE IN ({codigos_str})
                    AND   HORARIO.DATA_AGENDA > '2025-07-28'

                    UNION ALL

                    SELECT 
                        'CONSULTA' TIPO,
                        'AGENDA' FONTE,
                        'HISTORICO'									ABA,
                        'X'											TIPO_LOG,
                        NULL										CODIGO_MOTIVO,
                        HORARIO.COD_PACIENTE,
                        HORARIO.ID_AGE_CONSULTA						CODIGO_AGENDA,
                        HORARIO.ID_AGE_CONSULTA_HOR					CODIGO_HORARIO,
                        HORARIO.COD_UNIDADE_EXECUTANTE				CODIGO_EXECUTANTE,
                        UNIDADE_EXECUTANTE.UNIDADE_FANTASIA			UNIDADE_EXECUTANTE,
                        HORARIO.DATA_AGENDA							DATA_AGENDA,
                        HORARIO.HOR_INI								HORARIO,
                        HORARIO.ID_PROFISSIONAL						CODIGO_PROFISSIONAL,
                        PROFISSIONAL.NOME_PROFISSIONAL				NOME_PROFISSIONAL,
                        ESPECIALIDADE.ID_ESPECIALIDADE				CODIGO_RECURSO,
                        UPPER(ESPECIALIDADE.NOME_ESPECIALIDADE)		NOME_RECURSO,
                        SUB_GRUPO.ID_SUBGRUPO						CODIGO_SUBGRUPO,
                        UPPER(SUB_GRUPO	.NOME_SUBGRUPO)				NOME_SUBGRUPO,
                        GRUPO.ID_GRUPO								CODIGO_GRUPO,
                        UPPER(GRUPO.NOME_GRUPO)						NOME_GRUPO,
                        PROTOCOLO.SUBCATEG							CID,
                        HORARIO.STATUS								STATUS_AGENDA,  
                        HORARIO.COD_UNIDADE_SOLICITANTE				CODIGO_SOLICITANTE,
                        UNIDADE_SOLICITANTE.UNIDADE_FANTASIA		UNIDADE_SOLICITANTE, 
                        HORARIO.DT_ULTIMA_ATUALIZ                   DATA_AGENDAMENTO,      
                        HORARIO.DT_ULTIMA_ATUALIZ                   DATA_ACAO,      
                        --1                                           LINHA,
                        NULL						                CODIGO_FILA
                    FROM 
                        AMB_AGE_CONSULTA_HOR HORARIO 
                    LEFT JOIN AMB_PROTOCOLO			PROTOCOLO				ON PROTOCOLO.ID_PROTOCOLO				= HORARIO.ID_PROTOCOLO
                    LEFT JOIN SES_PROFISSIONAL		PROFISSIONAL			ON PROFISSIONAL.ID_PROFISSIONAL			= HORARIO.ID_PROFISSIONAL
                    LEFT JOIN ADMAMB_ADM_UNIDADE	UNIDADE_EXECUTANTE		ON UNIDADE_EXECUTANTE.COD_UNIDADE		= HORARIO.COD_UNIDADE_EXECUTANTE
                    LEFT JOIN ADMAMB_ADM_UNIDADE	UNIDADE_SOLICITANTE		ON UNIDADE_SOLICITANTE.COD_UNIDADE		= HORARIO.COD_UNIDADE_SOLICITANTE
                    LEFT JOIN AMB_ESPECIALIDADE		ESPECIALIDADE			ON ESPECIALIDADE.ID_ESPECIALIDADE		= HORARIO.ID_ESPECIALIDADE
                    LEFT JOIN Amb_subgrupo		    SUB_GRUPO				ON SUB_GRUPO.ID_SUBGRUPO				= ESPECIALIDADE.ID_SUBGRUPO
                    LEFT JOIN amb_grupo				GRUPO					ON GRUPO.ID_GRUPO						= SUB_GRUPO.ID_GRUPO
                    WHERE HORARIO.COD_PACIENTE IN ({codigos_str})
                    AND   HORARIO.DATA_AGENDA > '2025-07-28'

                    UNION ALL


                    SELECT
                        'EXAME' TIPO,
                        'LOG' FONTE,
                        (CASE
                            WHEN AGENDAMENTO.COD_PACIENTE = HORARIO.COD_PACIENTE THEN 'HISTORICO'
                            ELSE NULL
                        END) ABA,	
                        AGENDAMENTO.TIPO_LOG						TIPO_LOG,
                        AGENDAMENTO.ID_MOTIVO						CODIGO_MOTIVO,
                        AGENDAMENTO.COD_PACIENTE,	
                        AGENDAMENTO.ID_AGE_EXAME					CODIGO_AGENDA,
                        AGENDAMENTO.ID_AGE_EXAME_HOR				CODIGO_HORARIO,
                        AGENDAMENTO.COD_UNIDADE_EXECUTANTE			CODIGO_EXECUTANTE,
                        UNIDADE_EXECUTANTE.UNIDADE_FANTASIA			UNIDADE_EXECUTANTE,
                        AGENDAMENTO.DATA_AGENDA						DATA_AGENDA,
                        AGENDAMENTO.HOR_INI							HORARIO,
                        NULL										CODIGO_PROFISSIONAL,
                        NULL										NOME_PROFISSIONAL,
                        EXAME.ID_EXAME								CODIGO_RECURSO,
                        UPPER(EXAME.NOME_EXAME)						NOME_RECURSO,
                        SUB_GRUPO.ID_SUBGRUPO						CODIGO_SUBGRUPO,
                        UPPER(SUB_GRUPO.NOME_SUBGRUPO)				NOME_SUBGRUPO,
                        GRUPO.ID_GRUPO								CODIGO_GRUPO,
                        UPPER(GRUPO.NOME_GRUPO)						NOME_GRUPO,
                        NULL										CID,
                        HORARIO.STATUS								STATUS_AGENDA,  
                        AGENDAMENTO.COD_UNIDADE_SOLICITANTE			CODIGO_SOLICITANTE,
                        UNIDADE_SOLICITANTE.UNIDADE_FANTASIA		UNIDADE_SOLICITANTE,  
                        AGENDAMENTO.DT_ULTIMA_ATUALIZ               DATA_AGENDAMENTO,                    
                        AGENDAMENTO.DATA_ACAO						DATA_ACAO,
                        --ROW_NUMBER() OVER(PARTITION BY AGENDAMENTO.ID_AGE_EXAME_HOR ORDER BY AGENDAMENTO.ID_LOG_EXAME DESC) LINHA,
                        AGENDAMENTO.ID_FILA							CODIGO_FILA
                    FROM 
                        AMB_LOG_EXAME AGENDAMENTO
                    LEFT JOIN AMB_AGE_EXAME_HOR		HORARIO					ON HORARIO.ID_AGE_EXAME_HOR				= AGENDAMENTO.ID_AGE_EXAME_HOR
                    LEFT JOIN ADMAMB_ADM_UNIDADE	UNIDADE_EXECUTANTE		ON UNIDADE_EXECUTANTE.COD_UNIDADE		= AGENDAMENTO.COD_UNIDADE_EXECUTANTE
                    LEFT JOIN ADMAMB_ADM_UNIDADE	UNIDADE_SOLICITANTE		ON UNIDADE_SOLICITANTE.COD_UNIDADE		= AGENDAMENTO.COD_UNIDADE_SOLICITANTE
                    LEFT JOIN AMB_EXAME1			EXAME					ON EXAME.ID_EXAME						= HORARIO.ID_EXAME
                    LEFT JOIN Amb_subgrupo		    SUB_GRUPO				ON SUB_GRUPO.ID_SUBGRUPO				= EXAME.ID_SUBGRUPO
                    LEFT JOIN amb_grupo				GRUPO					ON GRUPO.ID_GRUPO						= SUB_GRUPO.ID_GRUPO
                    WHERE AGENDAMENTO.COD_PACIENTE IN ({codigos_str})
                    AND   HORARIO.DATA_AGENDA > '2025-07-28'

                    UNION ALL
                    SELECT 
                        'EXAME' TIPO,
                        'AGENDA' FONTE,
                        'HISTORICO'									ABA,
                        'X'											TIPO_LOG,
                        NULL										CODIGO_MOTIVO,
                        HORARIO.COD_PACIENTE,
                        HORARIO.ID_AGE_EXAME						CODIGO_AGENDA,
                        HORARIO.ID_AGE_EXAME_HOR					CODIGO_HORARIO,
                        HORARIO.COD_UNIDADE_EXECUTANTE				CODIGO_EXECUTANTE,
                        UNIDADE_EXECUTANTE.UNIDADE_FANTASIA			UNIDADE_EXECUTANTE,
                        HORARIO.DATA_AGENDA							DATA_AGENDA,
                        HORARIO.HOR_INI								HORARIO,
                        NULL										CODIGO_PROFISSIONAL,
                        NULL										NOME_PROFISSIONAL,
                        EXAME.ID_EXAME								CODIGO_RECURSO,
                        UPPER(EXAME.NOME_EXAME)						NOME_RECURSO,
                        SUB_GRUPO.ID_SUBGRUPO						CODIGO_SUBGRUPO,
                        UPPER(SUB_GRUPO	.NOME_SUBGRUPO)				NOME_SUBGRUPO,
                        GRUPO.ID_GRUPO								CODIGO_GRUPO,
                        UPPER(GRUPO.NOME_GRUPO)						NOME_GRUPO,
                        NULL										CID,
                        HORARIO.STATUS								STATUS_AGENDA,    
                        HORARIO.COD_UNIDADE_SOLICITANTE				CODIGO_SOLICITANTE,    
                        UNIDADE_SOLICITANTE.UNIDADE_FANTASIA		UNIDADE_SOLICITANTE,     
                        HORARIO.DT_ULTIMA_ATUALIZ                   DATA_AGENDAMENTO,    
                        HORARIO.DT_ULTIMA_ATUALIZ					DATA_ACAO,	
                        --1                                           LINHA	,
                        NULL                                        CODIGO_FILA
                    FROM 
                        AMB_AGE_EXAME_HOR HORARIO 
                    LEFT JOIN ADMAMB_ADM_UNIDADE	UNIDADE_EXECUTANTE		ON UNIDADE_EXECUTANTE.COD_UNIDADE		= HORARIO.COD_UNIDADE_EXECUTANTE
                    LEFT JOIN ADMAMB_ADM_UNIDADE	UNIDADE_SOLICITANTE		ON UNIDADE_SOLICITANTE.COD_UNIDADE		= HORARIO.COD_UNIDADE_SOLICITANTE
                    LEFT JOIN AMB_EXAME1			EXAME					ON EXAME.ID_EXAME						= HORARIO.ID_EXAME
                    LEFT JOIN Amb_subgrupo		    SUB_GRUPO				ON SUB_GRUPO.ID_SUBGRUPO				= EXAME.ID_SUBGRUPO
                    LEFT JOIN amb_grupo				GRUPO					ON GRUPO.ID_GRUPO						= SUB_GRUPO.ID_GRUPO
                    WHERE HORARIO.COD_PACIENTE IN ({codigos_str})
                    AND   HORARIO.DATA_AGENDA > '2025-07-28'),
                    ORDENADO AS (SELECT
                                    ROW_NUMBER() OVER(PARTITION BY TIPO,COD_PACIENTE,NOME_RECURSO ORDER BY DATA_AGENDA,  CODIGO_FILA DESC) LINHA,
                                    DADOS.*
                                FROM 
                                    DADOS),                    
                    
                    RELATORIO AS(SELECT 
                                    ORDENADO.*
                                FROM 
                                    ORDENADO)

                    SELECT 
                        TIPO	,
                        ABA	,
                        TIPO_LOG	,
                        CODIGO_MOTIVO	,
                        COD_PACIENTE	,
                        CODIGO_AGENDA	,
                        CODIGO_HORARIO	,
                        CODIGO_EXECUTANTE	,
                        UNIDADE_EXECUTANTE	,
                        DATA_AGENDA	,
                        HORARIO	,
                        CODIGO_PROFISSIONAL	,
                        NOME_PROFISSIONAL	,
                        CODIGO_RECURSO	,
                        NOME_RECURSO	,
                        CODIGO_SUBGRUPO	,
                        NOME_SUBGRUPO	,
                        CODIGO_GRUPO	,
                        NOME_GRUPO	,
                        CID	,
                        STATUS_AGENDA	,
                        CODIGO_SOLICITANTE	,
                        UNIDADE_SOLICITANTE	,
                        DATA_AGENDAMENTO	,
                        LINHA	,
                        NULL ORDEM	,
                        DATA_AGENDAMENTO DATA_ATUALIZACAO	,
                        DATA_ACAO	,
                        CODIGO_FILA	
                    FROM 
                        RELATORIO 
                    ORDER BY TIPO, ABA, DATA_AGENDA DESC                       
            """)
############################################################################################################################################

def AgendamentosFila():    
    logger.info(f"--> INICIOU ROTINA ApagarDados.")
    ApagarDados("TB_LOG_AGENDA",conexaoMRA)    
    logger.info(f"--> FINALIZOU ROTINA ApagarDados.") 

    logger.info(f"--> INICIOU ROTINA Extrair Pacientes")  
    comandoPaciente = text("""
                                WITH FILA_PENDENTE AS (
                                SELECT 
                                    FILA.CODIGO_PACIENTE,
                                    (CASE
                                        WHEN (((FILA.CODIGO_STATUS IN (0,11) AND FILA.ORIGEM = 'CDR') OR (FILA.CODIGO_STATUS = (3) AND FILA.ORIGEM = 'Regulação') OR (FILA.CODIGO_STATUS = (5) AND FILA.ORIGEM = 'Solicitações'))) THEN 'PENDENTE'
                                        ELSE 'RESOLVIDA'
                                    END)STATUS_FILA,
                                    FILA.ANO_ENTRADA,
                                    FILA.CODIGO_HORARIO
                                FROM 
                                    TB_TEMPO_CUIDAR_ATUALIZADA FILA)
                                SELECT  
                                    DISTINCT CODIGO_PACIENTE 
                                FROM 
                                    FILA_PENDENTE 
                                WHERE FILA_PENDENTE.STATUS_FILA = 'RESOLVIDA'
        """)
    dfPaciente = ExtrairDados(conexaoMRA,comandoPaciente) 
    if dfPaciente.empty:
        print(f"[{datetime.now().strftime('%d/%m/%Y %H:%M')}] Não foi encontrado nenhum paciente.")   
    logger.info(f"Qtde de Pacientes Encontrados: {len(dfPaciente)}")  
    logger.info(f"--> FINALIZOU ROTINA Extrair Pacientes")  
                
    lista_codigos = dfPaciente['CODIGO_PACIENTE'].tolist()
    codigos_str = ','.join(map(str, lista_codigos))
    tamanho_lote = 500

    logger.info(f"--> INICIOU ROTINA de Processamento em Lote")      
    for i in range(0, len(lista_codigos), tamanho_lote):
        lote = lista_codigos[i:i + tamanho_lote]
        codigos_str = ','.join(map(str, lote))
        logger.info(f"[{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}] "
            f"Processando lote {i//tamanho_lote + 1} de {len(lista_codigos)//tamanho_lote + 1} "
            f"({len(lote)} códigos)")
        comando = QueryAgendamento(codigos_str)          
        dfExtracao = ExtrairDados(conexaoProducao,comando)
        IncluirDados(dfExtracao,"TB_LOG_AGENDA",conexaoMRA)   
        logger.info(f"[{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}] "
            f"Final do Processamento do lote {i//tamanho_lote + 1} de {len(lista_codigos)//tamanho_lote + 1} "
            f"({len(lote)} códigos)")
    logger.info(f"--> FINALIZOU ROTINA de Processamento em Lote")  
############################################################################################################################################
def AgendamentosFilaCompleta():    
    logger.info(f"--> INICIOU ROTINA ApagarDados.")
    ApagarDados("TB_LOG_AGENDA_COMPLETA",conexaoMRA)    
    logger.info(f"--> FINALIZOU ROTINA ApagarDados.") 

    logger.info(f"--> INICIOU ROTINA Extrair Pacientes")  
    comandoPaciente = text("""
                                WITH FILA_PENDENTE AS (
                                SELECT 
                                    FILA.CODIGO_PACIENTE,
                                    (CASE
                                        WHEN (((FILA.CODIGO_STATUS IN (0,11) AND FILA.ORIGEM = 'CDR') OR (FILA.CODIGO_STATUS = (3) AND FILA.ORIGEM = 'Regulação') OR (FILA.CODIGO_STATUS = (5) AND FILA.ORIGEM = 'Solicitações'))) THEN 'PENDENTE'
                                        ELSE 'RESOLVIDA'
                                    END)STATUS_FILA,
                                    FILA.ANO_ENTRADA,
                                    FILA.CODIGO_HORARIO
                                FROM 
                                    TB_TEMPO_CUIDAR_ATUALIZADA FILA)
                                SELECT  
                                    DISTINCT CODIGO_PACIENTE 
                                FROM 
                                    FILA_PENDENTE 
                                WHERE FILA_PENDENTE.STATUS_FILA = 'RESOLVIDA'
        """)
    dfPaciente = ExtrairDados(conexaoMRA,comandoPaciente) 
    if dfPaciente.empty:
        print(f"[{datetime.now().strftime('%d/%m/%Y %H:%M')}] Não foi encontrado nenhum paciente.")   
    logger.info(f"Qtde de Pacientes Encontrados: {len(dfPaciente)}")  
    logger.info(f"--> FINALIZOU ROTINA Extrair Pacientes")  
                
    lista_codigos = dfPaciente['CODIGO_PACIENTE'].tolist()
    codigos_str = ','.join(map(str, lista_codigos))
    tamanho_lote = 500

    logger.info(f"--> INICIOU ROTINA de Processamento em Lote")      
    for i in range(0, len(lista_codigos), tamanho_lote):
        lote = lista_codigos[i:i + tamanho_lote]
        codigos_str = ','.join(map(str, lote))
        logger.info(f"[{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}] "
            f"Processando lote {i//tamanho_lote + 1} de {len(lista_codigos)//tamanho_lote + 1} "
            f"({len(lote)} códigos)")
        comando = QueryAgendamentoCompleta(codigos_str)          
        dfExtracao = ExtrairDados(conexaoProducao,comando)
        IncluirDados(dfExtracao,"TB_LOG_AGENDA_COMPLETA",conexaoMRA)   
        logger.info(f"[{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}] "
            f"Final do Processamento do lote {i//tamanho_lote + 1} de {len(lista_codigos)//tamanho_lote + 1} "
            f"({len(lote)} códigos)")
    logger.info(f"--> FINALIZOU ROTINA de Processamento em Lote")  
############################################################################################################################################
def AtualizaDadosAgendamentos(conexao):
    try:
        logger.info(f"Iniciou o processo de atualização dos dados do agendamento (AtualizaDadosAgendamentos)")
        comando = f'''
            UPDATE TB_TEMPO_CUIDAR_ATUALIZADA
            SET CODIGO_HORARIO				= NULL,
                STATUS_RECEPCAO				= NULL,
                DATA_AGENDA					= NULL,
                SITUACAO_PACIENTE_AGENDA	= NULL,
                DATA_AGENDAMENTO			= NULL,
                CODIGO_SOLICITANTE_AGENDA   = NULL,
                TIPO_ACAO				= NULL;

            WITH RELATORIO AS
                (SELECT 
                    AGENDAMENTO.TIPO_LOG,
                    FILA.ORIGEM,
                    FILA.CODIGO_FILA,
                    FILA.DATA_ENTRADA,

                    FILA.CODIGO_RECURSO		CODIGO_RECURSO,
                    FILA.NOME_RECURSO		NOME_RECURSO,

                    (CASE
                        WHEN FILA.TIPO = 'E' THEN 'EXAME'
                        ELSE 'CONSULTA'
                    END)					TIPO_FILA,


                    FILA.CODIGO_PACIENTE,
                    FILA.NOME_PACIENTE,
                
                    FILA.CODIGO_SOLICITANTE					CODIGO_SOLICITANTE_FILA,
                    FILA.UNIDADE_SOLICITANTE				UNIDADE_SOLICITANTE_FILA,

                    AGENDAMENTO.CODIGO_SOLICITANTE			CODIGO_SOLICITANTE_AGENDA,
                    AGENDAMENTO.UNIDADE_SOLICITANTE			UNIDADE_SOLICITANTE_AGENDA,
                
                    AGENDAMENTO.CODIGO_EXECUTANTE			CODIGO_EXECUTANTE_AGENDA,
                    AGENDAMENTO.UNIDADE_EXECUTANTE			UNIDADE_EXECUTANTE_AGENDA,
                
                    FILA.CID_FILA,
                    AGENDAMENTO.CID CID_AGENDA,

                    AGENDAMENTO.CODIGO_MOTIVO,
                    MOTIVO.MOTIVO,

                    AGENDAMENTO.CODIGO_AGENDA,
                    AGENDAMENTO.CODIGO_HORARIO,
                    AGENDAMENTO.DATA_AGENDA,
                    AGENDAMENTO.DATA_AGENDAMENTO,

                    (CASE
                        WHEN MOTIVO.STATUS_AGENDA = 'CANCELADA' THEN 'CANCELADO'
                        ELSE 'AGENDADO'
                    END) STATUS_AGENDA,

                    UPPER(CASE
                        WHEN MOTIVO.STATUS_AGENDA = 'CANCELADA' THEN 
                            NULL
                        WHEN AGENDAMENTO.STATUS_AGENDA = 'A' THEN
                            'Ausente'
                        WHEN AGENDAMENTO.STATUS_AGENDA = 'D' THEN
                            'Desistente'
                        WHEN AGENDAMENTO.STATUS_AGENDA = 'I' THEN
                            'Dispensado'
                        WHEN AGENDAMENTO.STATUS_AGENDA = 'P' THEN
                            'Presente'
                        WHEN AGENDAMENTO.DATA_AGENDA >= GETDATE() THEN
                            'Sem recepção (Agenda Futura)'
                        ELSE
                            'Sem recepção'
                    END)												STATUS_RECEPCAO,
                    ROW_NUMBER() OVER(PARTITION BY FILA.CODIGO_FILA, FILA.NOME_RECURSO ORDER BY AGENDAMENTO.DATA_AGENDA DESC) POSICAO
                FROM 
                    TB_TEMPO_CUIDAR_ATUALIZADA FILA
                LEFT JOIN TB_LOG_AGENDA		AGENDAMENTO ON (AGENDAMENTO.COD_PACIENTE = FILA.CODIGO_PACIENTE	AND AGENDAMENTO.NOME_RECURSO	= FILA.NOME_RECURSO AND CAST(AGENDAMENTO.DATA_AGENDA AS date)>= CAST(FILA.DATA_ENTRADA AS date) AND AGENDAMENTO.TIPO_LOG <> 'T')
                LEFT JOIN TB_TEMPO_CUIDAR_MOTIVO_AGENDA MOTIVO		ON MOTIVO.ID_MOTIVO			= AGENDAMENTO.CODIGO_MOTIVO			AND MOTIVO.TIPO_ACAO			= AGENDAMENTO.TIPO_LOG
                WHERE NOT (((FILA.CODIGO_STATUS IN (0,11) AND FILA.ORIGEM = 'CDR') OR (FILA.CODIGO_STATUS = (3) AND FILA.ORIGEM = 'Regulação') OR (FILA.CODIGO_STATUS = (5) AND FILA.ORIGEM = 'Solicitações')))) 
            --SELECT * FROM RELATORIO WHERE CODIGO_PACIENTE = 3920317

            UPDATE FILA
            SET FILA.CODIGO_HORARIO					= RELATORIO.CODIGO_HORARIO,
                FILA.STATUS_RECEPCAO				= RELATORIO.STATUS_RECEPCAO,
                FILA.DATA_AGENDA					= RELATORIO.DATA_AGENDA,
                FILA.SITUACAO_PACIENTE_AGENDA		= RELATORIO.STATUS_AGENDA,
                FILA.DATA_AGENDAMENTO				= RELATORIO.DATA_AGENDAMENTO,
                FILA.CODIGO_SOLICITANTE_AGENDA		= RELATORIO.CODIGO_SOLICITANTE_AGENDA,
                FILA.TIPO_ACAO						= RELATORIO.TIPO_LOG,
                FILA.ID_MOTIVO					    = RELATORIO.CODIGO_MOTIVO
            FROM TB_TEMPO_CUIDAR_ATUALIZADA FILA
            INNER JOIN RELATORIO ON RELATORIO.ORIGEM  = FILA.ORIGEM AND RELATORIO.CODIGO_FILA = FILA.CODIGO_FILA AND RELATORIO.POSICAO = 1;        
        
        '''
        conexao.execute(text(comando))
        logger.info(f"Finalizou o processo de atualização dos dados do agendamento (AtualizaDadosAgendamentos)")   
        conexao.commit()     
    except Exception:
        logger.exception(f"Erro no processo AtualizaDadosAgendamentos.")
        raise  
############################################################################################################################################    
if __name__ == "__main__":
    AgendamentosFila()
    AgendamentosFilaCompleta()
    AtualizaDadosAgendamentos(conexaoMRA)