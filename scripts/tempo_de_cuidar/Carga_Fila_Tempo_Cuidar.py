'''
OBJETIVO
Este script tem como objetivo identificar, atualizar e consolidar os dados das filas pendentes das ferramentas CDR, Regulação (CFR) e Solicitações do SIRESP, 
garantindo que todas as filas pertencentes ao escopo do projeto Tempo de Cuidar estejam devidamente cadastradas e com seus dados atualizados.

O processo inicia com a atualização da lista de filas pendentes no ambiente de produção, permitindo a identificação de novas filas que ainda não fazem parte do 
projeto. Essas filas são então incorporadas à tabela de controle do Tempo de Cuidar (TB_FILA_TEMPO_CUIDAR), preservando o histórico de filas monitoradas 
pelo projeto.

Em seguida, o script recarrega a tabela analítica TB_TEMPO_CUIDAR_ATUALIZADA, consultando novamente a base de produção para extrair os dados atualizados das 
filas das três ferramentas do SIRESP (Solicitações, Regulação e CDR), com base nos códigos de filas previamente definidos no projeto.

Ao final da execução, a tabela TB_TEMPO_CUIDAR_ATUALIZADA passa a conter os dados consolidados e atualizados das filas pendentes do projeto Tempo de Cuidar, 
servindo como base oficial para análises, acompanhamento e construção de dashboards.
'''
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
        conexao.commit()
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
       # with conexao.begin():
       #     conexao.execute(text(sql))
        conexao.execute(text(sql))
        conexao.commit()
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
def ExtracaoDadosCDR(codigos_str):
    return text(f"""
                    SELECT
                                    DISTINCT
                                    'CDR'								    ORIGEM,
                                    GETDATE()							DATA_ATUALIZACAO,
                                    X.ID_FILA								CODIGO_FILA,
                                    YEAR(CAST(X.DATA_ENTRADA AS DATE))		ANO_ENTRADA,
                                    X.DATA_ENTRADA							DATA_ENTRADA,
                                    (CASE		
                                        WHEN ESPECIALIDADE.ID_ESPECIALIDADE IS NULL THEN 
                                            EXAME.TIPO
                                        ELSE 
                                            NULL
                                    END)                                    TIPO_EXAME,                      
                                    (CASE		
                                        WHEN ESPECIALIDADE.ID_ESPECIALIDADE IS NULL THEN 
                                            SUB_GRUPO2.ID_SUBGRUPO
                                        ELSE 
                                            SUB_GRUPO.ID_SUBGRUPO
                                    END)                                    CODIGO_SUBGRUPO,
                                    (CASE		
                                        WHEN ESPECIALIDADE.ID_ESPECIALIDADE IS NULL THEN 
                                            SUB_GRUPO2.NOME_SUBGRUPO
                                        ELSE 
                                            SUB_GRUPO.NOME_SUBGRUPO
                                    END)                                    NOME_SUBGRUPO,

                                    (CASE		
                                        WHEN ESPECIALIDADE.ID_ESPECIALIDADE IS NULL THEN 
                                            GRUPO2.ID_GRUPO
                                        ELSE 
                                            GRUPO.ID_GRUPO
                                    END)                                    CODIGO_GRUPO,         
                                                
                                    (CASE		
                                        WHEN ESPECIALIDADE.ID_ESPECIALIDADE IS NULL THEN 
                                            GRUPO2.NOME_GRUPO
                                        ELSE 
                                            GRUPO.NOME_GRUPO
                                    END)                                    NOME_GRUPO,  

                                    (CASE		
                                        WHEN ESPECIALIDADE.ID_ESPECIALIDADE IS NULL THEN 
                                            EXAME.ID_EXAME 
                                        ELSE 
                                            ESPECIALIDADE.ID_ESPECIALIDADE
                                    END)                                    CODIGO_RECURSO,
                                    UPPER((CASE		
                                        WHEN ESPECIALIDADE.ID_ESPECIALIDADE IS NULL THEN 
                                            EXAME.NOME_EXAME 
                                        ELSE 
                                            ESPECIALIDADE.NOME_ESPECIALIDADE
                                    END))                                   NOME_RECURSO,

                                    X.TIPO									TIPO,
                                    X.COD_PACIENTE							CODIGO_PACIENTE,
                                    X.ID_STATUS								CODIGO_STATUS,
                                    S.DESCRICAO								DESCRICAO_STATUS,
                                    X.COD_UNIDADE_CAD						CODIGO_SOLICITANTE,
                                    UNIDADE_SOLICITANTE.UNIDADE_FANTASIA    UNIDADE_SOLICITANTE,
                                    NULL CODIGO_HORARIO,
                                    UNIDADE_SOLICITANTE.COD_CGR										CODIGO_REGIAO_SAUDE_SOLICITANTE,
                                    REPLACE(CIR.CIR, 'REGIAO DE SAUDE - ', '')						NOME_REGIAO_SAUDE_SOLICITANTE  ,
                                    UNIDADE_SOLICITANTE.COD_DRS										CODIGO_DRS_SOLICITANTE,
                                    DRS_SOLICITANTE.NOME_DRS										NOME_DRS_SOLICITANTE,
                                    PACIENTE.FLG_OBITO                                              PACIENTE_OBITO,
                                    PACIENTE.DT_OBITO                                               DATA_OBITO,
                                    NULL                                                            SITUACAO_AGENDA,
                                    NULL                                                            SITUACAO_PACIENTE_AGENDA,
                                    RRAS.COD_RRAS													NOME_RRAS,
                                    NULL															STATUS_RECEPCAO,		
                                    NULL															DATA_AGENDA,			
                                    NULL															DATA_ACAO,		
                                    NULL															ULTIMO_HISTORICO,	
                                    X.DATA_SAIDA													DATA_SAIDA,
									PACIENTE.NOME													NOME_PACIENTE,
									UPPER(UNIDADE_SOLICITANTE.MUNICIPIO)							MUNICIPIO_SOLICITANTE,
                                    NULL TIPO_AGENDAMENTO,
                                    NULL ROTINA_AGENDAMENTO,
									PACIENTE.DT_NASCIMENTO											DATA_NASCIMENTO_PACIENTE,
									PACIENTE.MUNICIPIO												MUNICIPIO_PACIENTE,
									X.CID															CID_FILA,
                                    (CASE		
                                        WHEN ESPECIALIDADE.ID_ESPECIALIDADE IS NULL THEN 
                                            EXAME.COD_EXAME
                                        ELSE 
                                            NULL
                                    END)                                                            CODIGO_EXAME,
                                    PACIENTE.SEXO                                                   SEXO_PACIENTE,
                                    NULL                                                            CODIGO_HORARIO_SUGESTAO,                             
                                    NULL                                                            TIPO_HORARIO_SUGESTAO,
                                    NULL                                                            DATA_AGENDAMENTO,
                                    NULL                                                            STATUS_AGENDAMENTO,
                                    NULL                                                            PERTINENTE,
                                    NULL                                                            ID_MOTIVO,
                                    NULL                                                            TIPO_ACAO,
									CAST(X.OBSERVACAO AS VARCHAR(MAX))								OBSERVACAO_FILA,
                                    CAST(X.OBSERVACAO_STATUS AS VARCHAR(MAX))                       OBSERVACAO_STATUS_FILA
                    FROM AMB_FILA X
                    LEFT JOIN AMB_FILA_STATUS S								ON S.ID_FILA_STATUS					= X.ID_STATUS
                    LEFT JOIN AMB_ESPECIALIDADE				ESPECIALIDADE	ON (ESPECIALIDADE.ID_ESPECIALIDADE	= X.ID_ESP_EXA					AND X.TIPO = 'C')
                    LEFT JOIN AMB_SUBGRUPO					SUB_GRUPO		ON (SUB_GRUPO.ID_SUBGRUPO			= ESPECIALIDADE.ID_SUBGRUPO		AND X.TIPO = 'C')
                    LEFT JOIN AMB_GRUPO						GRUPO			ON (GRUPO.ID_GRUPO					= SUB_GRUPO.ID_GRUPO			AND X.TIPO = 'C') 
                    LEFT JOIN AMB_EXAME1					EXAME			ON (EXAME.ID_EXAME					= X.ID_ESP_EXA					AND X.TIPO = 'E')
                    LEFT JOIN AMB_SUBGRUPO					SUB_GRUPO2		ON (SUB_GRUPO2.ID_SUBGRUPO			= EXAME.ID_SUBGRUPO				AND X.TIPO = 'E')                    
                    LEFT JOIN AMB_GRUPO						GRUPO2			ON (GRUPO2.ID_GRUPO					= SUB_GRUPO2.ID_GRUPO			AND X.TIPO = 'E')                 
                    LEFT JOIN ADMAMB_ADM_UNIDADE			UNIDADE_SOLICITANTE		ON	UNIDADE_SOLICITANTE.COD_UNIDADE		=	X.COD_UNIDADE_CAD                    
                    LEFT JOIN AMB_DRS						DRS_SOLICITANTE			ON	DRS_SOLICITANTE.COD_DRS				=	UNIDADE_SOLICITANTE.COD_DRS                    
                    LEFT JOIN ADMAMB_ADM_UNIDADE_CIR		CIR				ON	CIR.COD_UNIDADE					= UNIDADE_SOLICITANTE.COD_UNIDADE    
                    LEFT JOIN SES_PACIENTE                  PACIENTE        ON  PACIENTE.COD_PACIENTE           = X.COD_PACIENTE               
                    LEFT JOIN AMB_RRAS_MUNGEST			RRAS			ON UNIDADE_SOLICITANTE.CODMUNGEST				= RRAS.CODMUNGEST
                WHERE  X.TIPO_CONSULTA <> 'R'
                AND    X.ID_FILA IN ({codigos_str})
    """)
############################################################################################################################################
def ExtracaoDadosCFR(codigos_str):
    return text(f"""
                    SELECT Distinct 
                        'Regulação'																ORIGEM,
                        GETDATE()																DATA_ATUALIZACAO,
                        X.ID_FICHA																CODIGO_FILA,
                        YEAR(CAST(X.DATA_SOLICITACAO AS DATE))									ANO_ENTRADA,
                        X.DATA_SOLICITACAO														DATA_ENTRADA,
                        (CASE		
                            WHEN ESPECIALIDADE.ID_ESPECIALIDADE IS NULL THEN 
                                EXAME.TIPO
                            ELSE 
                                NULL
                        END)																	TIPO_EXAME,              
                        (CASE		
                            WHEN ESPECIALIDADE.ID_ESPECIALIDADE IS NULL THEN 
                                SUB_GRUPO2.ID_SUBGRUPO
                            ELSE 
                                SUB_GRUPO.ID_SUBGRUPO
                        END)																	CODIGO_SUBGRUPO,
                        (CASE		
                            WHEN ESPECIALIDADE.ID_ESPECIALIDADE IS NULL THEN 
                                SUB_GRUPO2.NOME_SUBGRUPO
                            ELSE 
                                SUB_GRUPO.NOME_SUBGRUPO
                        END)																	NOME_SUBGRUPO,
                        (CASE		
                            WHEN ESPECIALIDADE.ID_ESPECIALIDADE IS NULL THEN 
                                GRUPO2.ID_GRUPO
                            ELSE 
                                GRUPO.ID_GRUPO
                        END)																	CODIGO_GRUPO,                   
                        (CASE		
                            WHEN ESPECIALIDADE.ID_ESPECIALIDADE IS NULL THEN 
                                GRUPO2.NOME_GRUPO
                            ELSE 
                                GRUPO.NOME_GRUPO
                        END)																	NOME_GRUPO,     
                        (CASE		
                            WHEN ESPECIALIDADE.ID_ESPECIALIDADE IS NULL THEN 
                                EXAME.ID_EXAME 
                            ELSE 
                                ESPECIALIDADE.ID_ESPECIALIDADE
                        END)																	CODIGO_RECURSO,
                        UPPER((CASE		
                            WHEN ESPECIALIDADE.ID_ESPECIALIDADE IS NULL THEN 
                                EXAME.NOME_EXAME 
                            ELSE 
                                ESPECIALIDADE.NOME_ESPECIALIDADE
                        END))																	NOME_RECURSO,
                        A.COD_TIPO																TIPO,
                        X.COD_PACIENTE															CODIGO_PACIENTE,
                        X.ID_FICHA_STATUS														CODIGO_STATUS,
                        S.DESCRICAO_STATUS														DESCRICAO_STATUS,
                        X.COD_UNIDADE_SOLICITANTE												CODIGO_SOLICITANTE,
                        UNIDADE_SOLICITANTE.UNIDADE_FANTASIA									UNIDADE_SOLICITANTE,
                        NULL																	CODIGO_HORARIO,
                        UNIDADE_SOLICITANTE.COD_CGR												CODIGO_REGIAO_SAUDE_SOLICITANTE,
                        REPLACE(CIR.CIR, 'REGIAO DE SAUDE - ', '')								NOME_REGIAO_SAUDE_SOLICITANTE  ,
                        UNIDADE_SOLICITANTE.COD_DRS												CODIGO_DRS_SOLICITANTE,
                        DRS_SOLICITANTE.NOME_DRS												NOME_DRS_SOLICITANTE,
                        PACIENTE.FLG_OBITO														PACIENTE_OBITO,
                        PACIENTE.DT_OBITO														DATA_OBITO,
                        NULL																	SITUACAO_AGENDA,
                        NULL																	SITUACAO_PACIENTE_AGENDA,
                        RRAS.COD_RRAS															NOME_RRAS,
                        NULL																	STATUS_RECEPCAO,						
                        NULL																	DATA_AGENDA,							
                        NULL																	DATA_ACAO,							
                        NULL																	ULTIMO_HISTORICO,					
                        NULL																	DATA_SAIDA	,
                        PACIENTE.NOME													NOME_PACIENTE,
                        UPPER(UNIDADE_SOLICITANTE.MUNICIPIO)							MUNICIPIO_SOLICITANTE	,
                        NULL TIPO_AGENDAMENTO,
                        NULL ROTINA_AGENDAMENTO	,
                        PACIENTE.DT_NASCIMENTO											DATA_NASCIMENTO_PACIENTE,
                        PACIENTE.MUNICIPIO												MUNICIPIO_PACIENTE,
                        X.COD_CID_FICHA															CID_FILA,
                        (CASE		
                            WHEN ESPECIALIDADE.ID_ESPECIALIDADE IS NULL THEN 
                                EXAME.COD_EXAME
                            ELSE 
                                NULL
                        END)                                                            CODIGO_EXAME  ,
                        PACIENTE.SEXO                                                   SEXO_PACIENTE,
                        NULL                                                            CODIGO_HORARIO_SUGESTAO,                             
                        NULL                                                            TIPO_HORARIO_SUGESTAO  ,
                        NULL															DATA_AGENDAMENTO,
                        NULL															STATUS_AGENDAMENTO,
                        NULL                                                            PERTINENTE,
                        NULL                                                            ID_MOTIVO,
                        NULL                                                            TIPO_ACAO,
                        NULL								                            OBSERVACAO_FILA,
                        NULL                                                            OBSERVACAO_STATUS_FILA                                    
                    FROM
                        [Amb-Reg_ficha]  X
                    LEFT JOIN [Amb-Reg_ficha_associacao]  A ON A.ID_FICHA_ASSOCIACAO = X.ID_FICHA_ASSOCIACAO		
                    LEFT JOIN [Amb-Reg_ficha_status] S ON S.ID_FICHA_STATUS = X.ID_FICHA_STATUS
                    LEFT JOIN AMB_ESPECIALIDADE				ESPECIALIDADE	ON (ESPECIALIDADE.ID_ESPECIALIDADE = A.ID_ESP_EXAME AND A.COD_TIPO = 'C')
                    LEFT JOIN AMB_SUBGRUPO					SUB_GRUPO		ON (SUB_GRUPO.ID_SUBGRUPO	= ESPECIALIDADE.ID_SUBGRUPO AND A.COD_TIPO = 'C')
                    LEFT JOIN AMB_GRUPO						GRUPO			ON (GRUPO.ID_GRUPO			= SUB_GRUPO.ID_GRUPO AND A.COD_TIPO = 'C')
                    LEFT JOIN AMB_EXAME1					EXAME			ON (EXAME.ID_EXAME = A.ID_ESP_EXAME AND A.COD_TIPO = 'E')
                    LEFT JOIN AMB_SUBGRUPO					SUB_GRUPO2		ON (SUB_GRUPO2.ID_SUBGRUPO	= EXAME.ID_SUBGRUPO AND A.COD_TIPO = 'E')   
                    LEFT JOIN AMB_GRUPO						GRUPO2			ON (GRUPO2.ID_GRUPO			= SUB_GRUPO2.ID_GRUPO AND A.COD_TIPO = 'E')                       
                    LEFT JOIN ADMAMB_ADM_UNIDADE			UNIDADE_SOLICITANTE		ON	UNIDADE_SOLICITANTE.COD_UNIDADE		=	X.COD_UNIDADE_SOLICITANTE                    
                    LEFT JOIN AMB_DRS						DRS_SOLICITANTE			ON	DRS_SOLICITANTE.COD_DRS				=	UNIDADE_SOLICITANTE.COD_DRS                    
                    LEFT JOIN ADMAMB_ADM_UNIDADE_CIR		CIR				ON	CIR.COD_UNIDADE					= UNIDADE_SOLICITANTE.COD_UNIDADE             
                    LEFT JOIN SES_PACIENTE                  PACIENTE        ON  PACIENTE.COD_PACIENTE           = X.COD_PACIENTE  
                    LEFT JOIN AMB_RRAS_MUNGEST			RRAS			ON UNIDADE_SOLICITANTE.CODMUNGEST				= RRAS.CODMUNGEST       
                    WHERE X.ID_FICHA IN ({codigos_str})
    """)
############################################################################################################################################
def ExtracaoDadosSolicitacao(codigos_str):
    return text(f"""
                    SELECT 
                        DISTINCT
                        'Solicitações'																	ORIGEM,
                        GETDATE()																	DATA_ATUALIZACAO,
                        X.ID_FILA_CREM																	CODIGO_FILA,
                        YEAR(CAST(X.DATA_ENTRADA AS DATE))												ANO_ENTRADA,
                        X.DATA_ENTRADA																	DATA_ENTRADA,
                        (CASE		
                            WHEN ESPECIALIDADE.ID_ESPECIALIDADE IS NULL THEN EXAME.TIPO
                            ELSE NULL
                        END)																			TIPO_EXAME,      
                        (CASE		
                            WHEN ESPECIALIDADE.ID_ESPECIALIDADE IS NULL THEN SUB_GRUPO2.ID_SUBGRUPO
                            ELSE SUB_GRUPO.ID_SUBGRUPO
                        END)																			CODIGO_SUBGRUPO,
                        (CASE		
                            WHEN ESPECIALIDADE.ID_ESPECIALIDADE IS NULL THEN SUB_GRUPO2.NOME_SUBGRUPO
                            ELSE SUB_GRUPO.NOME_SUBGRUPO
                        END)																			NOME_SUBGRUPO,
                        (CASE		
                            WHEN ESPECIALIDADE.ID_ESPECIALIDADE IS NULL THEN GRUPO2.ID_GRUPO
                            ELSE GRUPO.ID_GRUPO
                        END)																			CODIGO_GRUPO,      
                        (CASE		
                            WHEN ESPECIALIDADE.ID_ESPECIALIDADE IS NULL THEN GRUPO2.NOME_GRUPO
                            ELSE GRUPO.NOME_GRUPO
                        END)																			NOME_GRUPO,   	
                        (CASE		
                            WHEN ESPECIALIDADE.ID_ESPECIALIDADE IS NULL THEN EXAME.ID_EXAME 
                            ELSE ESPECIALIDADE.ID_ESPECIALIDADE
                        END)																			CODIGO_RECURSO,
                        UPPER((CASE		
                            WHEN ESPECIALIDADE.ID_ESPECIALIDADE IS NULL THEN EXAME.NOME_EXAME 
                            ELSE ESPECIALIDADE.NOME_ESPECIALIDADE
                        END))																			NOME_RECURSO,
                        x.TIPO																			TIPO	,
                        X.COD_PACIENTE																	CODIGO_PACIENTE,
                        X.ID_STATUS																		CODIGO_STATUS,
                        S.DESCRICAO																		DESCRICAO_STATUS,
                        X.COD_UNIDADE_CAD																CODIGO_SOLICITANTE,
                        UNIDADE_SOLICITANTE.UNIDADE_FANTASIA											UNIDADE_SOLICITANTE,
                        NULL																			CODIGO_HORARIO,
                        UNIDADE_SOLICITANTE.COD_CGR														CODIGO_REGIAO_SAUDE_SOLICITANTE,
                        REPLACE(CIR.CIR, 'REGIAO DE SAUDE - ', '')										NOME_REGIAO_SAUDE_SOLICITANTE,
                        UNIDADE_SOLICITANTE.COD_DRS														CODIGO_DRS_SOLICITANTE,
                        DRS_SOLICITANTE.NOME_DRS														NOME_DRS_SOLICITANTE,
                        PACIENTE.FLG_OBITO																PACIENTE_OBITO,
                        PACIENTE.DT_OBITO																DATA_OBITO,
                        NULL																			SITUACAO_AGENDA,
                        NULL																			SITUACAO_PACIENTE_AGENDA,
                        RRAS.COD_RRAS																	NOME_RRAS,
                        NULL																			STATUS_RECEPCAO,	
                        NULL																			DATA_AGENDA,		
                        NULL																			DATA_ACAO,		
                        NULL																			ULTIMO_HISTORICO,
                        NULL																			DATA_SAIDA	,
                        PACIENTE.NOME													NOME_PACIENTE,
                        UPPER(UNIDADE_SOLICITANTE.MUNICIPIO)							MUNICIPIO_SOLICITANTE	,
                        NULL TIPO_AGENDAMENTO,
                        NULL ROTINA_AGENDAMENTO,
                        PACIENTE.DT_NASCIMENTO											DATA_NASCIMENTO_PACIENTE,
                        PACIENTE.MUNICIPIO												MUNICIPIO_PACIENTE,
                        X.CID															CID_FILA,
                        (CASE		
                            WHEN ESPECIALIDADE.ID_ESPECIALIDADE IS NULL THEN 
                                EXAME.COD_EXAME
                            ELSE 
                                NULL
                        END)                                                            CODIGO_EXAME   ,
                        PACIENTE.SEXO                                                   SEXO_PACIENTE,
                        NULL                                                            CODIGO_HORARIO_SUGESTAO,                             
                        NULL                                                            TIPO_HORARIO_SUGESTAO  ,
                        NULL															DATA_AGENDAMENTO,
                        NULL															STATUS_AGENDAMENTO,
                        NULL                                                            PERTINENTE,
                        NULL                                                            ID_MOTIVO,
                        NULL                                                            TIPO_ACAO,
                        NULL								                            OBSERVACAO_FILA,
                        NULL                                                            OBSERVACAO_STATUS_FILA     
                    FROM
                        Amb_fila_crem X
                    LEFT JOIN Amb_fila_crem_status S ON S.ID_STATUS = X.ID_STATUS
                    LEFT JOIN AMB_ESPECIALIDADE				ESPECIALIDADE	ON (ESPECIALIDADE.ID_ESPECIALIDADE	= X.ID_ESP_EXA					AND X.TIPO = 'C')
                    LEFT JOIN AMB_SUBGRUPO					SUB_GRUPO		ON (SUB_GRUPO.ID_SUBGRUPO			= ESPECIALIDADE.ID_SUBGRUPO		AND X.TIPO = 'C')
                    LEFT JOIN AMB_GRUPO						GRUPO			ON (GRUPO.ID_GRUPO					= SUB_GRUPO.ID_GRUPO			AND X.TIPO = 'C') 
                    LEFT JOIN AMB_EXAME1					EXAME			ON (EXAME.ID_EXAME					= X.ID_ESP_EXA					AND X.TIPO = 'E')
                    LEFT JOIN AMB_SUBGRUPO					SUB_GRUPO2		ON (SUB_GRUPO2.ID_SUBGRUPO			= EXAME.ID_SUBGRUPO				AND X.TIPO = 'E')                    
                    LEFT JOIN AMB_GRUPO						GRUPO2			ON (GRUPO2.ID_GRUPO					= SUB_GRUPO2.ID_GRUPO			AND X.TIPO = 'E') 
                    LEFT JOIN ADMAMB_ADM_UNIDADE			UNIDADE_SOLICITANTE		ON	UNIDADE_SOLICITANTE.COD_UNIDADE		=	X.COD_UNIDADE_CAD                    
                    LEFT JOIN AMB_DRS						DRS_SOLICITANTE			ON	DRS_SOLICITANTE.COD_DRS				=	UNIDADE_SOLICITANTE.COD_DRS                    
                    LEFT JOIN ADMAMB_ADM_UNIDADE_CIR		CIR				ON	CIR.COD_UNIDADE					= UNIDADE_SOLICITANTE.COD_UNIDADE       
                    LEFT JOIN SES_PACIENTE                  PACIENTE        ON  PACIENTE.COD_PACIENTE           = X.COD_PACIENTE    
                    LEFT JOIN AMB_RRAS_MUNGEST			RRAS			ON UNIDADE_SOLICITANTE.CODMUNGEST				= RRAS.CODMUNGEST           
                    WHERE X.ID_FILA_CREM IN ({codigos_str})
    """)
############################################################################################################################################
def CarregarFilasPendentes():
    logger.info(f"--> INICIOU ROTINA ApagarDados.")
    ApagarDados("TB_TEMPO_CUIDAR_LISTA_FILA",conexaoMRA)    
    logger.info(f"--> FINALIZOU ROTINA ApagarDados.")  
    
    logger.info(f"--> INICIOU ROTINA DE CARGA - TB_TEMPO_CUIDAR_LISTA_FILA.")
    comando = f'''
                    WITH 
                        CFR AS (SELECT DISTINCT
                                            'CFR' + TRIM(CAST(FILA.ID_FICHA AS VARCHAR(15)))		CODIGO,
                                            'Regulação'												FERRAMENTA,
                                            GETDATE()												DATA_ATUALIZACAO,
                                            FILA.ID_FICHA											CODIGO_FILA					
                                        FROM
                                            [Amb-Reg_ficha] FILA
                                        LEFT JOIN [Amb-Reg_ficha_associacao]	ASSOCIACAO				ON	ASSOCIACAO.ID_FICHA_ASSOCIACAO					=	FILA.ID_FICHA_ASSOCIACAO
                                        LEFT JOIN [amb-reg_ficha_status]		STATUS					ON	STATUS.ID_FICHA_STATUS							=	FILA.ID_FICHA_STATUS
                                        LEFT JOIN ses_paciente					PACIENTE				ON	PACIENTE.COD_PACIENTE							=	FILA.COD_PACIENTE -- Por que temos fichas que não conseguem se relacionar aos pacientes | Erro de cadastro?  De 5.280 fichas fomos para 5.237 ou seja perdemos 43 fichas.
                                        LEFT JOIN [Amb-Reg_ficha_tipo]			TIPO_FICHA				ON	TIPO_FICHA.ID_FICHA_TIPO						=	FILA.ID_FICHA_TIPO						
                                        LEFT JOIN AdmAmb_adm_unidade			UNIDADE_SOLICITANTE		ON	UNIDADE_SOLICITANTE.COD_UNIDADE					=	FILA.COD_UNIDADE_SOLICITANTE
                                        LEFT JOIN amb_especialidade			RECURSO					ON  (RECURSO.ID_ESPECIALIDADE						=   ASSOCIACAO.ID_ESP_EXAME AND ASSOCIACAO.COD_TIPO = 'C')
                                        LEFT JOIN amb_subgrupo					SUBGRUPO				ON	SUBGRUPO.ID_SUBGRUPO							=	RECURSO.ID_SUBGRUPO
                                        LEFT JOIN amb_grupo					GRUPO					ON	GRUPO.ID_GRUPO									=	SUBGRUPO.ID_GRUPO
                                        LEFT JOIN AMB_DRS						DRS_SOLICITANTE			ON	DRS_SOLICITANTE.COD_DRS							=	UNIDADE_SOLICITANTE.COD_DRS
                                        LEFT JOIN AMB_RRAS_MUNGEST				RRAS_SOLICITANTE		ON	CAST(UNIDADE_SOLICITANTE.CODMUNGEST AS INT)		=	CAST(RRAS_SOLICITANTE.CODMUNGEST AS INT)
                                        LEFT JOIN ADMAMB_ADM_UNIDADE_CIR		CIR_SOLICITANTE			ON	CIR_SOLICITANTE.COD_UNIDADE						=	UNIDADE_SOLICITANTE.COD_UNIDADE  
                                        LEFT JOIN AdmAmb_adm_unidade_gestao	GESTAO_SOLICITANTE		ON	GESTAO_SOLICITANTE.SIGLA_GESTAO					=	UNIDADE_SOLICITANTE.SIGLA_GESTAO 
                                        LEFT JOIN AdmAmb_adm_unidade			UNIDADE_REGULADORA		ON	UNIDADE_REGULADORA.COD_UNIDADE					=	FILA.COD_UNIDADE_REGULADOR --> Acredito que não tenhamos sempre uma unidade reguladora para as filas (fichas)
                                        LEFT JOIN ADMAMB_ADM_UNIDADE_CIR		CIR_REGULADORA			ON	CIR_REGULADORA.COD_UNIDADE						=	UNIDADE_REGULADORA.COD_UNIDADE  
                                        LEFT  JOIN [Amb-Reg_ficha_agendamento]  AGENDAMENTO				ON	(AGENDAMENTO.ID_FICHA							=	FILA.ID_FICHA AND AGENDAMENTO.FLG_ATIVO = 1)
                                        LEFT JOIN amb_age_consulta_hor			HORARIO_AGENDAMENTO		ON  HORARIO_AGENDAMENTO.ID_AGE_CONSULTA_HOR			=	AGENDAMENTO.COD_AGENDA
                                        WHERE FILA.ID_FICHA_STATUS = 3
                                        AND   YEAR(FILA.DATA_SOLICITACAO) <= 2024
                                        AND ASSOCIACAO.COD_TIPO = 'C'
                                        
                                        UNION ALL

                                        SELECT 
                                            DISTINCT
                                            'CFR' + TRIM(CAST(FILA.ID_FICHA AS VARCHAR(15)))		CODIGO,
                                            'Regulação'												FERRAMENTA,
                                            GETDATE()												DATA_ATUALIZACAO,
                                            FILA.ID_FICHA											CODIGO_FILA			
                                        FROM
                                            [Amb-Reg_ficha] FILA
                                        LEFT JOIN [Amb-Reg_ficha_associacao]	ASSOCIACAO				ON	ASSOCIACAO.ID_FICHA_ASSOCIACAO					=	FILA.ID_FICHA_ASSOCIACAO
                                        LEFT JOIN [amb-reg_ficha_status]		STATUS					ON	STATUS.ID_FICHA_STATUS							=	FILA.ID_FICHA_STATUS
                                        LEFT JOIN ses_paciente					PACIENTE				ON	PACIENTE.COD_PACIENTE							=	FILA.COD_PACIENTE -- Por que temos fichas que não conseguem se relacionar aos pacientes | Erro de cadastro?  De 5.280 fichas fomos para 5.237 ou seja perdemos 43 fichas.
                                        LEFT JOIN [Amb-Reg_ficha_tipo]			TIPO_FICHA				ON	TIPO_FICHA.ID_FICHA_TIPO						=	FILA.ID_FICHA_TIPO						
                                        LEFT JOIN AdmAmb_adm_unidade			UNIDADE_SOLICITANTE		ON	UNIDADE_SOLICITANTE.COD_UNIDADE					=	FILA.COD_UNIDADE_SOLICITANTE
                                        LEFT JOIN amb_exame1					RECURSO					ON  (RECURSO.ID_EXAME								=   ASSOCIACAO.ID_ESP_EXAME AND ASSOCIACAO.COD_TIPO = 'E')
                                        LEFT JOIN amb_subgrupo					SUBGRUPO				ON	SUBGRUPO.ID_SUBGRUPO							=	RECURSO.ID_SUBGRUPO
                                        LEFT JOIN amb_grupo					GRUPO					ON	GRUPO.ID_GRUPO									=	SUBGRUPO.ID_GRUPO
                                        LEFT JOIN AMB_DRS						DRS_SOLICITANTE			ON	DRS_SOLICITANTE.COD_DRS							=	UNIDADE_SOLICITANTE.COD_DRS
                                        LEFT JOIN AMB_RRAS_MUNGEST				RRAS_SOLICITANTE		ON	CAST(UNIDADE_SOLICITANTE.CODMUNGEST AS INT)		=	CAST(RRAS_SOLICITANTE.CODMUNGEST AS INT)
                                        LEFT JOIN ADMAMB_ADM_UNIDADE_CIR		CIR_SOLICITANTE			ON	CIR_SOLICITANTE.COD_UNIDADE						=	UNIDADE_SOLICITANTE.COD_UNIDADE  
                                        LEFT JOIN AdmAmb_adm_unidade_gestao	GESTAO_SOLICITANTE		ON	GESTAO_SOLICITANTE.SIGLA_GESTAO					=	UNIDADE_SOLICITANTE.SIGLA_GESTAO 
                                        LEFT JOIN AdmAmb_adm_unidade			UNIDADE_REGULADORA		ON	UNIDADE_REGULADORA.COD_UNIDADE					=	FILA.COD_UNIDADE_REGULADOR --> Acredito que não tenhamos sempre uma unidade reguladora para as filas (fichas)
                                        LEFT JOIN ADMAMB_ADM_UNIDADE_CIR		CIR_REGULADORA			ON	CIR_REGULADORA.COD_UNIDADE						=	UNIDADE_REGULADORA.COD_UNIDADE  
                                        LEFT  JOIN [Amb-Reg_ficha_agendamento]  AGENDAMENTO				ON	(AGENDAMENTO.ID_FICHA							=	FILA.ID_FICHA AND AGENDAMENTO.FLG_ATIVO = 1)
                                        LEFT JOIN amb_age_consulta_hor			HORARIO_AGENDAMENTO		ON  HORARIO_AGENDAMENTO.ID_AGE_CONSULTA_HOR			=	AGENDAMENTO.COD_AGENDA
                                        WHERE FILA.ID_FICHA_STATUS = 3	
                                        AND ASSOCIACAO.COD_TIPO = 'E'	
                                        AND   YEAR(FILA.DATA_SOLICITACAO) <= 2024),
                        SOLICITACAO AS (
                                        SELECT
                                            'SOL' + TRIM(CAST(FILA.ID_FILA_CREM AS VARCHAR(15)))	CODIGO,
                                            'Solicitações'											FERRAMENTA,
                                            GETDATE()												DATA_ATUALIZACAO,
                                            FILA.ID_FILA_CREM										CODIGO_FILA
                                        FROM
                                            Amb_fila_crem FILA
                                        LEFT JOIN Amb_fila_crem_status			STATUS					ON	STATUS.ID_STATUS								=	FILA.ID_STATUS
                                        LEFT JOIN ses_paciente					PACIENTE				ON	PACIENTE.COD_PACIENTE							=	FILA.COD_PACIENTE -- Por que temos fichas que não conseguem se relacionar aos pacientes | Erro de cadastro?  De 5.280 fichas fomos para 5.237 ou seja perdemos 43 fichas.				
                                        LEFT JOIN AdmAmb_adm_unidade			UNIDADE_SOLICITANTE		ON	UNIDADE_SOLICITANTE.COD_UNIDADE					=	FILA.COD_UNIDADE_CAD
                                        LEFT JOIN amb_especialidade			RECURSO					ON  (RECURSO.ID_ESPECIALIDADE						=   FILA.ID_ESP_EXA AND FILA.TIPO = 'C')
                                        LEFT JOIN amb_subgrupo					SUBGRUPO				ON	SUBGRUPO.ID_SUBGRUPO							=	RECURSO.ID_SUBGRUPO
                                        LEFT JOIN amb_grupo					GRUPO					ON	GRUPO.ID_GRUPO									=	SUBGRUPO.ID_GRUPO
                                        LEFT  JOIN Amb_protocolo				PROTOCOLO				ON  PROTOCOLO.ID_PROTOCOLO							=   FILA.ID_PROTOCOLO
                                        LEFT JOIN AMB_DRS						DRS_SOLICITANTE			ON	DRS_SOLICITANTE.COD_DRS							=	UNIDADE_SOLICITANTE.COD_DRS
                                        LEFT JOIN AMB_RRAS_MUNGEST				RRAS_SOLICITANTE		ON	CAST(UNIDADE_SOLICITANTE.CODMUNGEST AS INT)		=	CAST(RRAS_SOLICITANTE.CODMUNGEST AS INT)
                                        LEFT JOIN ADMAMB_ADM_UNIDADE_CIR		CIR_SOLICITANTE			ON	CIR_SOLICITANTE.COD_UNIDADE						=	UNIDADE_SOLICITANTE.COD_UNIDADE  
                                        LEFT JOIN AdmAmb_adm_unidade_gestao	GESTAO_SOLICITANTE		ON	GESTAO_SOLICITANTE.SIGLA_GESTAO					=	UNIDADE_SOLICITANTE.SIGLA_GESTAO 
                                        WHERE FILA.ID_STATUS = 5
                                        AND   YEAR(FILA.DATA_ENTRADA) <= 2024
                                        AND FILA.TIPO = 'C'
                                        
                                        UNION ALL

                                        SELECT
                                            'SOL' + TRIM(CAST(FILA.ID_FILA_CREM AS VARCHAR(15)))	CODIGO,
                                            'Solicitações'											FERRAMENTA,
                                            GETDATE()												DATA_ATUALIZACAO,
                                            FILA.ID_FILA_CREM										CODIGO_FILA
                                        FROM                                            
                                            Amb_fila_crem FILA
                                        LEFT JOIN Amb_fila_crem_status			STATUS					ON	STATUS.ID_STATUS								=	FILA.ID_STATUS
                                        LEFT JOIN ses_paciente					PACIENTE				ON	PACIENTE.COD_PACIENTE							=	FILA.COD_PACIENTE -- Por que temos fichas que não conseguem se relacionar aos pacientes | Erro de cadastro?  De 5.280 fichas fomos para 5.237 ou seja perdemos 43 fichas.				
                                        LEFT JOIN AdmAmb_adm_unidade			UNIDADE_SOLICITANTE		ON	UNIDADE_SOLICITANTE.COD_UNIDADE					=	FILA.COD_UNIDADE_CAD
                                        LEFT JOIN amb_exame1					RECURSO					ON  (RECURSO.ID_EXAME								=   FILA.ID_ESP_EXA AND FILA.TIPO = 'E')
                                        LEFT JOIN amb_subgrupo					SUBGRUPO				ON	SUBGRUPO.ID_SUBGRUPO							=	RECURSO.ID_SUBGRUPO
                                        LEFT JOIN amb_grupo					GRUPO					ON	GRUPO.ID_GRUPO									=	SUBGRUPO.ID_GRUPO
                                        LEFT  JOIN Amb_protocolo				PROTOCOLO				ON  PROTOCOLO.ID_PROTOCOLO							=   FILA.ID_PROTOCOLO
                                        LEFT JOIN AMB_DRS						DRS_SOLICITANTE			ON	DRS_SOLICITANTE.COD_DRS							=	UNIDADE_SOLICITANTE.COD_DRS
                                        LEFT JOIN AMB_RRAS_MUNGEST				RRAS_SOLICITANTE		ON	CAST(UNIDADE_SOLICITANTE.CODMUNGEST AS INT)		=	CAST(RRAS_SOLICITANTE.CODMUNGEST AS INT)
                                        LEFT JOIN ADMAMB_ADM_UNIDADE_CIR		CIR_SOLICITANTE			ON	CIR_SOLICITANTE.COD_UNIDADE						=	UNIDADE_SOLICITANTE.COD_UNIDADE  
                                        LEFT JOIN AdmAmb_adm_unidade_gestao	GESTAO_SOLICITANTE		ON	GESTAO_SOLICITANTE.SIGLA_GESTAO					=	UNIDADE_SOLICITANTE.SIGLA_GESTAO 
                                        WHERE FILA.ID_STATUS = 5
                                        AND   YEAR(FILA.DATA_ENTRADA) <= 2024			
                                        AND FILA.TIPO = 'E'
                                        ),
                            CDR AS (
                                    SELECT
                                        'CDR' + TRIM(CAST(FILA.ID_FILA AS VARCHAR(15)))			CODIGO,
                                        'CDR'													FERRAMENTA,
                                        GETDATE()												DATA_ATUALIZACAO,
                                        FILA.ID_FILA											CODIGO_FILA
                                    FROM
                                        amb_fila FILA
                                    LEFT JOIN amb_fila_status				STATUS					ON	STATUS.ID_FILA_STATUS							=	FILA.ID_STATUS
                                    LEFT JOIN ses_paciente					PACIENTE				ON	PACIENTE.COD_PACIENTE							=	FILA.COD_PACIENTE
                                    LEFT JOIN AdmAmb_adm_unidade			UNIDADE_SOLICITANTE		ON	UNIDADE_SOLICITANTE.COD_UNIDADE					=	FILA.COD_UNIDADE_CAD
                                    LEFT JOIN amb_especialidade			RECURSO					ON  (RECURSO.ID_ESPECIALIDADE						=   FILA.ID_ESP_EXA AND FILA.TIPO = 'C')
                                    LEFT JOIN amb_subgrupo					SUBGRUPO				ON	SUBGRUPO.ID_SUBGRUPO							=	RECURSO.ID_SUBGRUPO
                                    LEFT JOIN amb_grupo					GRUPO					ON	GRUPO.ID_GRUPO									=	SUBGRUPO.ID_GRUPO
                                    LEFT JOIN AMB_DRS						DRS_SOLICITANTE			ON	DRS_SOLICITANTE.COD_DRS							=	UNIDADE_SOLICITANTE.COD_DRS
                                    LEFT JOIN AMB_RRAS_MUNGEST				RRAS_SOLICITANTE		ON	CAST(UNIDADE_SOLICITANTE.CODMUNGEST AS INT)		=	CAST(RRAS_SOLICITANTE.CODMUNGEST AS INT)
                                    LEFT JOIN ADMAMB_ADM_UNIDADE_CIR		CIR_SOLICITANTE			ON	CIR_SOLICITANTE.COD_UNIDADE						=	UNIDADE_SOLICITANTE.COD_UNIDADE  
                                    LEFT JOIN AdmAmb_adm_unidade_gestao	GESTAO_SOLICITANTE		ON	GESTAO_SOLICITANTE.SIGLA_GESTAO					=	UNIDADE_SOLICITANTE.SIGLA_GESTAO 
                                    WHERE FILA.ID_STATUS IN (0,11)
                                    AND   YEAR(FILA.DATA_ENTRADA) <= 2024
                                    AND   TIPO_CONSULTA <> 'R'
                                    AND   FILA.TIPO = 'C'

                                    UNION ALL

                                    -- Código Status = 0 e 11 (CDR)
                                    SELECT
                                        'CDR' + TRIM(CAST(FILA.ID_FILA AS VARCHAR(15)))			CODIGO,
                                        'CDR'													FERRAMENTA,
                                        GETDATE()												DATA_ATUALIZACAO,
                                        FILA.ID_FILA											CODIGO_FILA
                                    FROM
                                        amb_fila FILA
                                    LEFT JOIN amb_fila_status				STATUS					ON	STATUS.ID_FILA_STATUS							=	FILA.ID_STATUS
                                    LEFT JOIN ses_paciente					PACIENTE				ON	PACIENTE.COD_PACIENTE							=	FILA.COD_PACIENTE
                                    LEFT JOIN AdmAmb_adm_unidade			UNIDADE_SOLICITANTE		ON	UNIDADE_SOLICITANTE.COD_UNIDADE					=	FILA.COD_UNIDADE_CAD
                                    LEFT JOIN amb_exame1					RECURSO					ON  (RECURSO.ID_EXAME								=   FILA.ID_ESP_EXA AND FILA.TIPO = 'E')
                                    LEFT JOIN amb_subgrupo					SUBGRUPO				ON	SUBGRUPO.ID_SUBGRUPO							=	RECURSO.ID_SUBGRUPO
                                    LEFT JOIN amb_grupo					GRUPO					ON	GRUPO.ID_GRUPO									=	SUBGRUPO.ID_GRUPO
                                    LEFT JOIN AMB_DRS						DRS_SOLICITANTE			ON	DRS_SOLICITANTE.COD_DRS							=	UNIDADE_SOLICITANTE.COD_DRS
                                    LEFT JOIN AMB_RRAS_MUNGEST				RRAS_SOLICITANTE		ON	CAST(UNIDADE_SOLICITANTE.CODMUNGEST AS INT)		=	CAST(RRAS_SOLICITANTE.CODMUNGEST AS INT)
                                    LEFT JOIN ADMAMB_ADM_UNIDADE_CIR		CIR_SOLICITANTE			ON	CIR_SOLICITANTE.COD_UNIDADE						=	UNIDADE_SOLICITANTE.COD_UNIDADE  
                                    LEFT JOIN AdmAmb_adm_unidade_gestao	GESTAO_SOLICITANTE		ON	GESTAO_SOLICITANTE.SIGLA_GESTAO					=	UNIDADE_SOLICITANTE.SIGLA_GESTAO 
                                    WHERE FILA.ID_STATUS IN (0,11)
                                    AND   TIPO_CONSULTA <> 'R'
                                    AND FILA.TIPO = 'E'
                                    AND   YEAR(FILA.DATA_ENTRADA) <= 2024)

                        SELECT * FROM CFR 
                        UNION ALL
                        SELECT * FROM SOLICITACAO 
                        UNION ALL
                        SELECT * FROM CDR 
               '''    
    dfDados = ExtrairDados(conexaoProducao,comando)
    IncluirDados(dfDados,"TB_TEMPO_CUIDAR_LISTA_FILA",conexaoMRA)    
    logger.info(f"--> FINALIZOU ROTINA DE CARGA - TB_TEMPO_CUIDAR_LISTA_FILA.")     
############################################################################################################################################
def CarregarNovasFilasTempoCuidar():
    logger.info(f"--> INICIOU ROTINA DE CARGA - TB_FILA_TEMPO_CUIDAR.")
    comando = f'''
                SELECT
                    (CASE
                        WHEN FILAS_PENDENTES.FERRAMENTA = 'CDR' THEN 'CDR'
                        WHEN FILAS_PENDENTES.FERRAMENTA = 'Regulação' THEN 'CFR'
                        WHEN FILAS_PENDENTES.FERRAMENTA = 'Solicitações' THEN 'SOL'
                    END) + TRIM(CAST(FILAS_PENDENTES.CODIGO_FILA AS VARCHAR(15)))		CODIGO,
                    FILAS_PENDENTES.FERRAMENTA ORIGEM,
                    FILAS_PENDENTES.CODIGO_FILA,
                    CAST(GETDATE() AS DATE) DATA_TEMPO_CUIDAR
                FROM 
                    TB_TEMPO_CUIDAR_LISTA_FILA FILAS_PENDENTES
                WHERE NOT EXISTS (SELECT 1 FROM TB_FILA_TEMPO_CUIDAR FILA_EXISTENTE WHERE FILA_EXISTENTE.ORIGEM = FILAS_PENDENTES.FERRAMENTA AND FILA_EXISTENTE.CODIGO_FILA = FILAS_PENDENTES.CODIGO_FILA)

               '''    
    dfDados = ExtrairDados(conexaoMRA,comando)
    IncluirDados(dfDados,"TB_FILA_TEMPO_CUIDAR",conexaoMRA)    
    logger.info(f"--> FINALIZOU ROTINA DE CARGA - TB_FILA_TEMPO_CUIDAR.")     
############################################################################################################################################      
def AtualizaFilaCDR():
    logger.info(f": (Inicio) Processando rotina AtualizaFilaCDR :")    
    
    logger.info(f":: (Inicio) Trazendo a fila do CDR :::")
    comando = text("""SELECT CODIGO_FILA FROM TB_FILA_TEMPO_CUIDAR WHERE ORIGEM = 'CDR'""")
    dfCodigos = ExtrairDados(conexaoMRA, comando)
    logger.info(f"Qtde Filas CDR para atualização: {len(dfCodigos)}")
    logger.info(f":: (Fim) Trazendo a fila do CDR :::")

    if dfCodigos.empty:
        print(f"[{datetime.now().strftime('%d/%m/%Y %H:%M')}] Não foi encontrado nenhum código.")
        logger.info(f"--> Não foi encontrado nenhum código")
        return        

    logger.info(f":: (Inicio) Atualização da Fila CDR")
    lista_codigos = dfCodigos["CODIGO_FILA"].tolist()
    tamanho_lote = 10000
    for i in range(0, len(lista_codigos), tamanho_lote):
        lote = lista_codigos[i:i + tamanho_lote]
        codigos_str = ','.join(map(str, lote))
        logger.info(f"[{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}] "
            f"::: (Inicio) Processando lote {i//tamanho_lote + 1} de {len(lista_codigos)//tamanho_lote + 1} "
            f"({len(lote)} filas no CDR)")
        logger.info(codigos_str)
        comando = ExtracaoDadosCDR(codigos_str)          
        dfExtracao = ExtrairDados(conexaoProducao,comando)
        IncluirDados(dfExtracao,"TB_TEMPO_CUIDAR_ATUALIZADA",conexaoMRA)   
        logger.info(f"[{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}] "
            f"::: (Fim) do Processamento do lote {i//tamanho_lote + 1} de {len(lista_codigos)//tamanho_lote + 1} "
            f"({len(lote)} filas no CDR)")
    logger.info(f":: (Fim) Atualização da Fila CDR")   

    logger.info(f": (Fim) Processando rotina AtualizaFilaCDR :")    
############################################################################################################################################      
def AtualizaFilaCFR():
    logger.info(f": (Inicio) Processando rotina AtualizaFilaCFR :")    
    
    logger.info(f":: (Inicio) Trazendo a fila do CFR :::")
    comando = text("""SELECT CODIGO_FILA FROM TB_FILA_TEMPO_CUIDAR WHERE ORIGEM = 'Regulação'""")
    dfCodigos = ExtrairDados(conexaoMRA, comando)
    logger.info(f"Qtde Filas CFR para atualização: {len(dfCodigos)}")
    logger.info(f":: (Fim) Trazendo a fila do CFR :::")

    if dfCodigos.empty:
        print(f"[{datetime.now().strftime('%d/%m/%Y %H:%M')}] Não foi encontrado nenhum código.")
        logger.info(f"--> Não foi encontrado nenhum código")
        return        

    logger.info(f":: (Inicio) Atualização da Fila CFR")
    lista_codigos = dfCodigos["CODIGO_FILA"].tolist()
    tamanho_lote = 5000
    for i in range(0, len(lista_codigos), tamanho_lote):
        lote = lista_codigos[i:i + tamanho_lote]
        codigos_str = ','.join(map(str, lote))
        logger.info(f"[{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}] "
            f"::: (Inicio) Processando lote {i//tamanho_lote + 1} de {len(lista_codigos)//tamanho_lote + 1} "
            f"({len(lote)} filas no CFR)")
        comando = ExtracaoDadosCFR(codigos_str)          
        dfExtracao = ExtrairDados(conexaoProducao,comando)
        IncluirDados(dfExtracao,"TB_TEMPO_CUIDAR_ATUALIZADA",conexaoMRA)   
        logger.info(f"[{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}] "
            f"::: (Fim) do Processamento do lote {i//tamanho_lote + 1} de {len(lista_codigos)//tamanho_lote + 1} "
            f"({len(lote)} filas no CFR)")
    logger.info(f":: (Fim) Atualização da Fila CFR")   

    logger.info(f": (Fim) Processando rotina AtualizaFilaCFR :")    
############################################################################################################################################      
def AtualizaFilaSolicitacao():
    logger.info(f": (Inicio) Processando rotina AtualizaFilaSolicitacao :")    
    
    logger.info(f":: (Inicio) Trazendo a fila do Solicitações :::")
    comando = text("""SELECT CODIGO_FILA FROM TB_FILA_TEMPO_CUIDAR WHERE ORIGEM = 'Solicitações'""")
    dfCodigos = ExtrairDados(conexaoMRA, comando)
    logger.info(f"Qtde Filas Solicitações para atualização: {len(dfCodigos)}")
    logger.info(f":: (Fim) Trazendo a fila do Solicitações :::")

    if dfCodigos.empty:
        print(f"[{datetime.now().strftime('%d/%m/%Y %H:%M')}] Não foi encontrado nenhum código.")
        logger.info(f"--> Não foi encontrado nenhum código")
        return        

    logger.info(f":: (Inicio) Atualização da Fila Solicitações")
    lista_codigos = dfCodigos["CODIGO_FILA"].tolist()
    tamanho_lote = 5000
    for i in range(0, len(lista_codigos), tamanho_lote):
        lote = lista_codigos[i:i + tamanho_lote]
        codigos_str = ','.join(map(str, lote))
        logger.info(f"[{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}] "
            f"::: (Inicio) Processando lote {i//tamanho_lote + 1} de {len(lista_codigos)//tamanho_lote + 1} "
            f"({len(lote)} filas no Solicitações)")
        comando = ExtracaoDadosSolicitacao(codigos_str)          
        dfExtracao = ExtrairDados(conexaoProducao,comando)
        IncluirDados(dfExtracao,"TB_TEMPO_CUIDAR_ATUALIZADA",conexaoMRA)   
        logger.info(f"[{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}] "
            f"::: (Fim) do Processamento do lote {i//tamanho_lote + 1} de {len(lista_codigos)//tamanho_lote + 1} "
            f"({len(lote)} filas no Solicitações)")
    logger.info(f":: (Fim) Atualização da Fila Solicitações")   

    logger.info(f": (Fim) Processando rotina AtualizaFilaSolicitacao :")    
############################################################################################################################################      
def ApagarFilaTempoCuidar():
    logger.info(f"--> INICIOU ROTINA ApagarDados.")
    ApagarDados("TB_TEMPO_CUIDAR_ATUALIZADA",conexaoMRA)    
    logger.info(f"--> FINALIZOU ROTINA ApagarDados.")      
############################################################################################################################################  
if __name__ == "__main__":    
    CarregarFilasPendentes()
    CarregarNovasFilasTempoCuidar()
    ApagarFilaTempoCuidar()
    AtualizaFilaSolicitacao()
    AtualizaFilaCFR()
    AtualizaFilaCDR()
 