from dotenv import load_dotenv
import os
import urllib
from datetime import datetime
import pandas as pd
from sqlalchemy import create_engine, text
import logging
import os
import sys
from dateutil.relativedelta import relativedelta
from datetime import timedelta
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
def Rotina(dataInicial, dataFinal):  
    logger.info(f"--> INICIOU ROTINA DE CARGA - TB_HORARIOS.") 
    comando = f'''
                    SELECT 
                        'LOG'							FONTE,
                        'CONSULTA'						TIPO_ATENDIMENTO,	
                        ID_AGE_CONSULTA_HOR				CODIGO_HORARIO,
                        ID_AGE_CONSULTA					CODIGO_AGENDA,
                        ID_PROFISSIONAL					CODIGO_PROFISSIONAL,
                        ID_ESPECIALIDADE				CODIGO_RECURSO,
                        COD_UNIDADE_EXECUTANTE			CODIGO_EXECUTANTE,
                        DATA_AGENDA						DATA_AGENDA,
                        HOR_INI							HORARIO_INICIAL,
                        HOR_FIM							HORARIO_FINAL,
                        COD_PACIENTE					CODIGO_PACIENTE,
                        COD_UNIDADE_SOLICITANTE			CODIGO_SOLICITANTE,
                        TIPO							TIPO_HORARIO,
                        DT_ULTIMA_ATUALIZ				DATA_AGENDAMENTO,
                        ID_PROTOCOLO					CODIGO_PROTOCOLO,
                        ID_MOTIVO						CODIGO_MOTIVO,
                        BLOQUEADO						BLOQUEADO,
                        FLG_BOLSAO						BOLSAO,
                        FLG_ND							NAO_DISTRIBUIDO,
                        UPPER(CASE
                            WHEN CONSULTA.STATUS = 'A'  THEN  'AUSENTE'
                            WHEN CONSULTA.STATUS = 'D'  THEN  'DESISTENTE'
                            WHEN CONSULTA.STATUS = 'I'  THEN  'DISPENSADO'
                            WHEN CONSULTA.STATUS = 'P'  THEN  'PRESENTE'
                            WHEN CONSULTA.DATA_AGENDA < GETDATE() THEN  'AGENDA FUTURA'
                            ELSE  'SEM RECEPÇÃO'
                        END)												STATUS_RECEPCAO
                    FROM 
                        AMB_LOG_CONSULTA CONSULTA 
                    WHERE CONSULTA.DT_ULTIMA_ATUALIZ BETWEEN '{dataInicial}' AND '{dataFinal}'
                    AND COD_PACIENTE <> 0 
                    AND TIPO_LOG = 'A'

                    UNION

                    SELECT 
                        'AGENDA'						FONTE,
                        'CONSULTA'						TIPO_ATENDIMENTO,	
                        ID_AGE_CONSULTA_HOR				CODIGO_HORARIO,
                        ID_AGE_CONSULTA					CODIGO_AGENDA,
                        ID_PROFISSIONAL					CODIGO_PROFISSIONAL,
                        ID_ESPECIALIDADE				CODIGO_RECURSO,
                        COD_UNIDADE_EXECUTANTE			CODIGO_EXECUTANTE,
                        DATA_AGENDA						DATA_AGENDA,
                        HOR_INI							HORARIO_INICIAL,
                        HOR_FIM							HORARIO_FINAL,
                        COD_PACIENTE					CODIGO_PACIENTE,
                        COD_UNIDADE_SOLICITANTE			CODIGO_SOLICITANTE,
                        TIPO							TIPO_HORARIO,
                        DT_ULTIMA_ATUALIZ				DATA_AGENDAMENTO,
                        ID_PROTOCOLO					CODIGO_PROTOCOLO,
                        ID_MOTIVO						CODIGO_MOTIVO,
                        BLOQUEADO						BLOQUEADO,
                        FLG_BOLSAO						BOLSAO,
                        FLG_ND							NAO_DISTRIBUIDO,
                        UPPER(CASE
                            WHEN CONSULTA.STATUS = 'A'  THEN  'AUSENTE'
                            WHEN CONSULTA.STATUS = 'D'  THEN  'DESISTENTE'
                            WHEN CONSULTA.STATUS = 'I'  THEN  'DISPENSADO'
                            WHEN CONSULTA.STATUS = 'P'  THEN  'PRESENTE'
                            WHEN CONSULTA.DATA_AGENDA < GETDATE() THEN  'AGENDA FUTURA'
                            ELSE  'SEM RECEPÇÃO'
                        END)												STATUS_RECEPCAO
                    FROM 
                        AMB_AGE_CONSULTA_HOR CONSULTA 
                    WHERE CONSULTA.DT_ULTIMA_ATUALIZ BETWEEN '{dataInicial}' AND '{dataFinal}'
                    AND COD_PACIENTE <> 0 

                    UNION 

                    SELECT 
                        'LOG'							FONTE,
                        'EXAME'							TIPO_ATENDIMENTO,	
                        ID_AGE_EXAME_HOR				CODIGO_HORARIO,
                        ID_AGE_EXAME					CODIGO_AGENDA,
                        ASSOCIACAO.ID_PROFISSIONAL		CODIGO_PROFISSIONAL,
                        CONSULTA.ID_EXAME				CODIGO_RECURSO,
                        COD_UNIDADE_EXECUTANTE			CODIGO_EXECUTANTE,
                        DATA_AGENDA						DATA_AGENDA,
                        HOR_INI							HORARIO_INICIAL,
                        HOR_FIM							HORARIO_FINAL,
                        COD_PACIENTE					CODIGO_PACIENTE,
                        COD_UNIDADE_SOLICITANTE			CODIGO_SOLICITANTE,
                        EXAME.TIPO						TIPO_HORARIO,
                        CONSULTA.DT_ULTIMA_ATUALIZ		DATA_AGENDAMENTO,
                        NULL							CODIGO_PROTOCOLO,
                        ID_MOTIVO						CODIGO_MOTIVO,
                        BLOQUEADO						BLOQUEADO,
                        FLG_BOLSAO						BOLSAO,
                        FLG_ND							NAO_DISTRIBUIDO,
                        UPPER(CASE
                            WHEN CONSULTA.STATUS = 'A'  THEN  'AUSENTE'
                            WHEN CONSULTA.STATUS = 'D'  THEN  'DESISTENTE'
                            WHEN CONSULTA.STATUS = 'I'  THEN  'DISPENSADO'
                            WHEN CONSULTA.STATUS = 'P'  THEN  'PRESENTE'
                            WHEN CONSULTA.DATA_AGENDA < GETDATE() THEN  'AGENDA FUTURA'
                            ELSE  'SEM RECEPÇÃO'
                        END)												STATUS_RECEPCAO
                    FROM 
                        AMB_LOG_EXAME CONSULTA 
                    LEFT JOIN AMB_ASSOCIACAO ASSOCIACAO ON ASSOCIACAO.ID_ASSOCIACAO = CONSULTA.ID_ASSOCIACAO 
                    LEFT JOIN AMB_EXAME1 EXAME ON EXAME.ID_EXAME = CONSULTA.ID_EXAME 
                    WHERE CONSULTA.DT_ULTIMA_ATUALIZ BETWEEN '{dataInicial}' AND '{dataFinal}'
                    AND CONSULTA.COD_PACIENTE <> 0 
                    AND CONSULTA.TIPO_LOG = 'A'

                    UNION

                    SELECT 
                        'AGENDA'						FONTE,
                        'EXAME'							TIPO_ATENDIMENTO,	
                        ID_AGE_EXAME_HOR				CODIGO_HORARIO,
                        ID_AGE_EXAME					CODIGO_AGENDA,
                        ASSOCIACAO.ID_PROFISSIONAL		CODIGO_PROFISSIONAL,
                        CONSULTA.ID_EXAME				CODIGO_RECURSO,
                        COD_UNIDADE_EXECUTANTE			CODIGO_EXECUTANTE,
                        DATA_AGENDA						DATA_AGENDA,
                        HOR_INI							HORARIO_INICIAL,
                        HOR_FIM							HORARIO_FINAL,
                        COD_PACIENTE					CODIGO_PACIENTE,
                        COD_UNIDADE_SOLICITANTE			CODIGO_SOLICITANTE,
                        EXAME.TIPO						TIPO_HORARIO,
                        CONSULTA.DT_ULTIMA_ATUALIZ		DATA_AGENDAMENTO,
                        NULL							CODIGO_PROTOCOLO,
                        ID_MOTIVO						CODIGO_MOTIVO,
                        BLOQUEADO						BLOQUEADO,
                        FLG_BOLSAO						BOLSAO,
                        FLG_ND							NAO_DISTRIBUIDO,
                        UPPER(CASE
                            WHEN CONSULTA.STATUS = 'A'  THEN  'AUSENTE'
                            WHEN CONSULTA.STATUS = 'D'  THEN  'DESISTENTE'
                            WHEN CONSULTA.STATUS = 'I'  THEN  'DISPENSADO'
                            WHEN CONSULTA.STATUS = 'P'  THEN  'PRESENTE'
                            WHEN CONSULTA.DATA_AGENDA < GETDATE() THEN  'AGENDA FUTURA'
                            ELSE  'SEM RECEPÇÃO'
                        END)												STATUS_RECEPCAO
                    FROM 
                        AMB_AGE_EXAME_HOR CONSULTA 
                    LEFT JOIN AMB_ASSOCIACAO ASSOCIACAO ON ASSOCIACAO.ID_ASSOCIACAO = CONSULTA.ID_ASSOCIACAO 
                    LEFT JOIN AMB_EXAME1 EXAME ON EXAME.ID_EXAME = CONSULTA.ID_EXAME                     
                    WHERE CONSULTA.DT_ULTIMA_ATUALIZ BETWEEN '{dataInicial}' AND '{dataFinal}'
                    AND CONSULTA.COD_PACIENTE <> 0 
               '''    
    dfSOLICITACAO = ExtrairDados(conexaoProducao,comando)
    IncluirDados(dfSOLICITACAO,"TB_HORARIOS",conexaoMRA)    
    logger.info(f"--> FINALIZOU ROTINA DE CARGA - TB_HORARIOS.") 

############################################################################################################################################
def executar_periodos(ano_inicio, mes_inicio, dia_inicio, ano_fim, mes_fim, dia_fim, numero_dias):
    data_atual = datetime(ano_inicio, mes_inicio, dia_inicio)
    data_limite = datetime(ano_fim, mes_fim, dia_fim)    
    while data_atual <= data_limite:
        data_inicial = data_atual
        data_final = data_atual + relativedelta(days=numero_dias)
        data_final = data_final - timedelta(seconds=1)
        logger.info(f"Data Inicial: {data_inicial} | Data Final:{data_final}")
        print(f"Data Inicial: {data_inicial} | Data Final:{data_final}")
        logger.info(f"--> INICIOU ROTINA ApagarDados - TB_HORARIOS.")
        ApagarDados("TB_HORARIOS",conexaoMRA,f" DATA_AGENDAMENTO BETWEEN '{data_inicial}' AND '{data_final}'")    
        logger.info(f"--> FINALIZOU ROTINA ApagarDados.")         
        Rotina(data_inicial, data_final)
        data_atual = data_atual + relativedelta(days=numero_dias)   

if __name__ == "__main__":
    print('Iniciou a execução BASE_HORARIOS.PY')
    executar_periodos(2026,4,8,2026,4,8,1)
